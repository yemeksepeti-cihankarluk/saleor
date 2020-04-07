from typing import TYPE_CHECKING, List, Optional, Set

from django.contrib.auth.models import Group, Permission
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import ValidationError
from django.db.models import Q, Value
from django.db.models.functions import Concat
from graphene.utils.str_converters import to_camel_case

from ...account import events as account_events
from ...account.error_codes import AccountErrorCode
from ...core.permissions import AccountPermissions, get_permissions

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from ...account.models import User


class UserDeleteMixin:
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        user = info.context.user
        if instance == user:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "You cannot delete your own account.",
                        code=AccountErrorCode.DELETE_OWN_ACCOUNT,
                    )
                }
            )
        elif instance.is_superuser:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete this account.",
                        code=AccountErrorCode.DELETE_SUPERUSER_ACCOUNT,
                    )
                }
            )


class CustomerDeleteMixin(UserDeleteMixin):
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        super().clean_instance(info, instance)
        if instance.is_staff:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete a staff account.",
                        code=AccountErrorCode.DELETE_STAFF_ACCOUNT,
                    )
                }
            )

    @classmethod
    def post_process(cls, info, deleted_count=1):
        account_events.staff_user_deleted_a_customer_event(
            staff_user=info.context.user, deleted_count=deleted_count
        )


class StaffDeleteMixin(UserDeleteMixin):
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        super().clean_instance(info, instance)
        if not instance.is_staff:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete a non-staff user.",
                        code=AccountErrorCode.DELETE_NON_STAFF_USER,
                    )
                }
            )

        # check if requestor can manage this user
        if get_out_of_scope_users(info.context.user, [instance]):
            msg = "You can't manage this user."
            code = AccountErrorCode.OUT_OF_SCOPE_USER.value
            raise ValidationError({"id": ValidationError(msg, code=code)})


def get_required_fields_camel_case(required_fields: set) -> set:
    """Return set of AddressValidationRules required fields in camel case."""
    return {validation_field_to_camel_case(field) for field in required_fields}


def validation_field_to_camel_case(name: str) -> str:
    """Convert name of the field from snake case to camel case."""
    name = to_camel_case(name)
    if name == "streetAddress":
        return "streetAddress1"
    return name


def get_allowed_fields_camel_case(allowed_fields: set) -> set:
    """Return set of AddressValidationRules allowed fields in camel case."""
    fields = {validation_field_to_camel_case(field) for field in allowed_fields}
    if "streetAddress1" in fields:
        fields.add("streetAddress2")
    return fields


def get_user_permissions(user: "User") -> "QuerySet":
    """Return all user permissions - from user groups and user_permissions field."""
    if user.is_superuser:
        return get_permissions()
    groups = user.groups.all()
    user_permissions = user.user_permissions.all()
    group_permissions = Permission.objects.filter(group__in=groups)
    permissions = user_permissions | group_permissions
    return permissions


def get_out_of_scope_permissions(user: "User", permissions: List[str]) -> List[str]:
    """Return permissions that the user hasn't got."""
    missing_permissions = []
    for perm in permissions:
        if not user.has_perm(perm):
            missing_permissions.append(perm)
    return missing_permissions


def get_out_of_scope_users(root_user: "User", users: List["User"]):
    """Return users whose permission scope is wider than the given user."""
    out_of_scope_users = []
    for user in users:
        user_permissions = user.get_all_permissions()
        if not root_user.has_perms(user_permissions):
            out_of_scope_users.append(user)
    return out_of_scope_users


def can_user_manage_group(user: "User", group: Group) -> bool:
    """User can't manage a group with permission that is out of the user's scope."""
    permissions = get_group_permission_codes(group)
    return user.has_perms(permissions)


def get_group_permission_codes(group: Group) -> "QuerySet":
    """Return group permissions in the format '<app label>.<permission codename>'."""
    return group.permissions.annotate(
        formated_codename=Concat("content_type__app_label", Value("."), "codename")
    ).values_list("formated_codename", flat=True)


def get_groups_which_user_can_manage(user: "User") -> List[Optional[Group]]:
    """Return groups which user can manage."""
    if not user.is_staff:
        return []

    user_permissions = get_user_permissions(user)
    user_permission_pks = set(user_permissions.values_list("pk", flat=True))

    groups = Group.objects.all().annotate(group_perms=ArrayAgg("permissions"))

    editable_groups = []
    for group in groups.iterator():
        out_of_scope_permissions = set(group.group_perms) - user_permission_pks
        out_of_scope_permissions.discard(None)
        if not out_of_scope_permissions:
            editable_groups.append(group)

    return editable_groups


def get_not_manageable_permissions_after_removing_users_from_group(
    group: Group, users: List["User"]
):
    """Return permissions that cannot be managed after removing users from group.

    After removing users from group, for each permission, there should be at least
    one staff member who can manage it (has both “manage staff” and this permission).
    """
    group_users = group.user_set.all()
    group_permissions = group.permissions.values_list("codename", flat=True)
    # If group has manage_staff permission and some users will stay in group
    # given users can me removed (permissions will be manageable)
    manage_staff_codename = AccountPermissions.MANAGE_STAFF.codename
    if len(group_users) > len(users) and manage_staff_codename in group_permissions:
        return set()

    # check if any of remaining group user has manage staff permission
    # if True, all group permissions can be managed
    group_remaining_users = set(group_users) - set(users)
    manage_staff_permission = AccountPermissions.MANAGE_STAFF.value
    if any([user.has_perm(manage_staff_permission) for user in group_remaining_users]):
        return set()

    # if group and any of remaining group user doesn't have manage staff permission
    # we can treat the situation as this when group is removing
    not_manageable_permissions = get_not_manageable_permissions_after_group_deleting(
        group
    )

    return not_manageable_permissions


def get_not_manageable_permissions_after_group_deleting(group):
    """Return permissions that cannot be managed after deleting the group.

    After removing group, for each permission, there should be at least one staff member
    who can manage it (has both “manage staff” and this permission).
    """
    group_pk = group.pk
    groups_data = get_group_to_permissions_and_users_mapping()
    not_manageable_permissions = groups_data.pop(group_pk)["permissions"]

    # get users from groups with manage staff and look for not_manageable_permissions
    # if any of not_manageable_permissions is found it is removed from set
    manage_staff_users = get_users_and_look_for_permissions_in_groups_with_manage_staff(
        groups_data, not_manageable_permissions
    )

    # check if management of all permissions provided by other groups
    if not not_manageable_permissions:
        return set()

    # check lack of users with manage staff in other groups
    if not manage_staff_users:
        return not_manageable_permissions

    # look for remaining permissions from not_manageable_permissions in user with
    # manage staff permissions groups, if any of not_manageable_permissions is found
    # it is removed from set
    look_for_permission_in_users_with_manage_staff(
        groups_data, manage_staff_users, not_manageable_permissions
    )

    # return remaining not managable permissions
    return not_manageable_permissions


def get_group_to_permissions_and_users_mapping():
    """Return group mapping with data about their permissions and user.

    Get all groups and return mapping in structure:
        {
            group1_pk: {
                "permissions": ["perm_codename1", "perm_codename2"],
                "users": [user_pk1, user_pk2]
            },
        }
    """
    mapping = {}
    groups_data = (
        Group.objects.all()
        .annotate(
            perm_codenames=ArrayAgg(
                Concat(
                    "permissions__content_type__app_label",
                    Value("."),
                    "permissions__codename",
                ),
                filter=Q(permissions__isnull=False),
            ),
            users=ArrayAgg("user", filter=Q(user__is_active=True)),
        )
        .values("pk", "perm_codenames", "users")
    )

    for data in groups_data:
        mapping[data["pk"]] = {
            "permissions": set(data["perm_codenames"]),
            "users": set(data["users"]),
        }

    return mapping


def get_users_and_look_for_permissions_in_groups_with_manage_staff(
    groups_data: dict, permissions_to_find: Set[str],
):
    """Search for permissions in groups with manage staff and return their users.

    Args:
        groups_data: dict with groups data, key is a group pk and value is group data
            with permissions and users
        permissions_to_find: searched permissions

    """
    users_with_manage_staff: Set[int] = set()
    for data in groups_data.values():
        permissions = data["permissions"]
        users = data["users"]
        has_manage_staff = AccountPermissions.MANAGE_STAFF.value in permissions
        has_users = bool(users)
        # only consider groups with active users and manage_staff permission
        if has_users and has_manage_staff:
            common_permissions = permissions_to_find & permissions
            # remove found permission from set
            permissions_to_find.difference_update(common_permissions)
            users_with_manage_staff.update(users)

    return users_with_manage_staff


def look_for_permission_in_users_with_manage_staff(
    groups_data: dict, users_to_check: Set[int], permissions_to_find: Set[str],
):
    """Search for permissions in user with manage staff groups.

    Args:
        groups_data: dict with groups data, key is a group pk and value is group data
            with permissions and users
        users_to_check: users with manage_staff
        permissions_to_find: searched permissions

    """
    for data in groups_data.values():
        permissions = data["permissions"]
        users = data["users"]
        common_users = users_to_check & users
        if common_users:
            common_permissions = permissions_to_find & permissions
            # remove found permission from set
            permissions_to_find.difference_update(common_permissions)
