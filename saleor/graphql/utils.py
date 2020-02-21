from typing import Tuple, Union

import graphene
from django.db.models import Q, QuerySet
from django.utils import timezone
from graphene_django.registry import get_global_registry
from graphql.error import GraphQLError
from graphql_jwt.utils import jwt_payload
from graphql_relay import from_global_id

from .core.enums import OrderDirection, PermissionEnum, ReportingPeriod
from .core.types import PermissionDisplay, SortInputObjectType

ERROR_COULD_NO_RESOLVE_GLOBAL_ID = (
    "Could not resolve to a node with the global id list of '%s'."
)
registry = get_global_registry()


def get_database_id(info, node_id, only_type):
    """Get a database ID from a node ID of given type."""
    _type, _id = graphene.relay.Node.from_global_id(node_id)
    if _type != str(only_type):
        raise AssertionError("Must receive a %s id." % str(only_type))
    return _id


def _check_graphene_type(requested_graphene_type, received_type):
    if requested_graphene_type:
        assert str(requested_graphene_type) == received_type, (
            "Must receive an {} id."
        ).format(str(requested_graphene_type))


def resolve_global_ids_to_primary_keys(ids, graphene_type=None):
    pks = []
    invalid_ids = []
    used_type = graphene_type

    for graphql_id in ids:
        if not graphql_id:
            continue

        try:
            node_type, _id = from_global_id(graphql_id)
        except Exception:
            invalid_ids.append(graphql_id)
            continue

        _check_graphene_type(used_type, node_type)
        used_type = node_type
        pks.append(_id)

    if invalid_ids:
        raise GraphQLError(ERROR_COULD_NO_RESOLVE_GLOBAL_ID % invalid_ids)

    return used_type, pks


def _resolve_graphene_type(type_name):
    for _, _type in registry._registry.items():
        if _type._meta.name == type_name:
            return _type
    raise AssertionError("Could not resolve the type {}".format(type_name))


def get_nodes(
    ids, graphene_type: Union[graphene.ObjectType, str] = None, model=None, qs=None
):
    """Return a list of nodes.

    If the `graphene_type` argument is provided, the IDs will be validated
    against this type. If the type was not provided, it will be looked up in
    the Graphene's registry. Raises an error if not all IDs are of the same
    type.

    If the `graphene_type` is of type str, the model keyword argument must be provided.
    """
    nodes_type, pks = resolve_global_ids_to_primary_keys(ids, graphene_type)

    # If `graphene_type` was not provided, check if all resolved types are
    # the same. This prevents from accidentally mismatching IDs of different
    # types.
    if nodes_type and not graphene_type:
        graphene_type = _resolve_graphene_type(nodes_type)

    if qs is None and graphene_type and not isinstance(graphene_type, str):
        qs = graphene_type._meta.model.objects
    elif model is not None:
        qs = model.objects

    nodes = list(qs.filter(pk__in=pks))
    nodes.sort(key=lambda e: pks.index(str(e.pk)))  # preserve order in pks

    if not nodes:
        raise GraphQLError(ERROR_COULD_NO_RESOLVE_GLOBAL_ID % ids)

    nodes_pk_list = [str(node.pk) for node in nodes]
    for pk in pks:
        assert pk in nodes_pk_list, "There is no node of type {} with pk {}".format(
            graphene_type, pk
        )
    return nodes


def filter_by_query_param(queryset, query, search_fields):
    """Filter queryset according to given parameters.

    Keyword Arguments:
        queryset - queryset to be filtered
        query - search string
        search_fields - fields considered in filtering

    """
    if query:
        query_by = {
            "{0}__{1}".format(field, "icontains"): query for field in search_fields
        }
        query_objects = Q()
        for q in query_by:
            query_objects |= Q(**{q: query_by[q]})
        return queryset.filter(query_objects).distinct()
    return queryset


def sort_queryset(queryset: QuerySet, sort_by: SortInputObjectType) -> QuerySet:
    """Sort queryset according to given parameters.

    rules:
        - sorting_field and sorting_attribute cannot be together)
        - when sorting_attribute is passed, it is expected that
            queryset will have method to sort by attributes
        - when sorter has custom sorting method it's name must be like
            `prepare_qs_for_sort_{enum_name}` and it must return sorted queryset

    Keyword Arguments:
        queryset - queryset to be sorted
        sort_by - dictionary with sorting field and direction

    """
    sorting_direction = sort_by.direction
    sorting_field = sort_by.field
    sorting_attribute = getattr(sort_by, "attribute_id", None)

    if sorting_field is not None and sorting_attribute is not None:
        raise GraphQLError(
            "You must provide either `field` or `attributeId` to sort the products."
        )
    elif sorting_attribute is not None:  # empty string as sorting_attribute is valid
        if sorting_attribute != "":
            graphene_type, sorting_attribute = from_global_id(sorting_attribute)
        descending = sorting_direction == OrderDirection.DESC

        # If the passed attribute ID is valid, execute the sorting
        # if attribute_pk.isnumeric() and graphene_type == "Attribute":
        queryset = queryset.sort_by_attribute(sorting_attribute, descending=descending)
        return queryset

    sort_enum = sort_by._meta.sort_enum
    if not sort_enum:
        return queryset
    sorting_fields = sort_enum.get(sorting_field)
    sorting_field_name = sorting_fields.name.lower()
    sorting_field_value = sorting_fields.value
    sorting_field_value = (
        sorting_field_value
        if isinstance(sorting_field_value, list)
        else [sorting_field_value]
    )

    custom_sort_by = getattr(sort_enum, f"qs_with_{sorting_field_name}", None)
    if custom_sort_by:
        queryset = custom_sort_by(queryset)
    sorting_list = [f"{sorting_direction}{field}" for field in sorting_field_value]

    return queryset.order_by(*sorting_list)


def sort_queryset_by_default(queryset: QuerySet) -> Tuple[QuerySet, dict]:
    """Sort queryset by it's default ordering."""
    queryset_model = queryset.model
    deafault_ordering = queryset_model._meta.ordering if queryset_model else []
    if deafault_ordering:
        ordering_fields = [field.replace("-", "") for field in deafault_ordering]
        direction = "-" if "-" in deafault_ordering[0] else ""
        order_by = {"field": ordering_fields, "direction": direction}
        return queryset.order_by(*deafault_ordering), order_by
    else:
        order_by = {"field": ["pk"], "direction": ""}
        return queryset.order_by("pk"), order_by


def reporting_period_to_date(period):
    now = timezone.now()
    if period == ReportingPeriod.TODAY:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == ReportingPeriod.THIS_MONTH:
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError("Unknown period: %s" % period)
    return start_date


def filter_by_period(queryset, period, field_name):
    start_date = reporting_period_to_date(period)
    return queryset.filter(**{"%s__gte" % field_name: start_date})


def format_permissions_for_display(permissions):
    """Transform permissions queryset into PermissionDisplay list.

    Keyword Arguments:
        permissions - queryset with permissions

    """
    formatted_permissions = []
    for permission in permissions:
        codename = ".".join([permission.content_type.app_label, permission.codename])
        formatted_permissions.append(
            PermissionDisplay(code=PermissionEnum.get(codename), name=permission.name)
        )
    return formatted_permissions


def create_jwt_payload(user, context=None):
    payload = jwt_payload(user, context)
    payload["user_id"] = graphene.Node.to_global_id("User", user.id)
    payload["is_staff"] = user.is_staff
    payload["is_superuser"] = user.is_superuser
    return payload


def get_user_or_service_account_from_context(context):
    # order is important
    # service_account can be None but user if None then is passed as anonymous
    return context.service_account or context.user


def filter_range_field(qs, field, value):
    gte, lte = value.get("gte"), value.get("lte")
    if gte:
        lookup = {f"{field}__gte": gte}
        qs = qs.filter(**lookup)
    if lte:
        lookup = {f"{field}__lte": lte}
        qs = qs.filter(**lookup)
    return qs
