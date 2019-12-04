from django.urls import reverse
from templated_email import send_templated_mail

from ..account.models import StaffNotificationRecipient
from ..celeryconf import app
from ..core.emails import get_email_context
from ..core.utils import build_absolute_uri
from ..seo.schema.email import get_order_confirmation_markup
from . import events
from .models import Fulfillment, Order

CONFIRM_ORDER_TEMPLATE = "order/confirm_order"
STAFF_CONFIRM_ORDER_TEMPLATE = "order/staff_confirm_order"
CONFIRM_FULFILLMENT_TEMPLATE = "order/confirm_fulfillment"
UPDATE_FULFILLMENT_TEMPLATE = "order/update_fulfillment"
CONFIRM_PAYMENT_TEMPLATE = "order/payment/confirm_payment"


def collect_data_for_email(order_pk, template):
    """Collect the required data for sending emails.

    Args:
        order_pk (int): order primary key
        template (str): email template path

    """
    order = Order.objects.get(pk=order_pk)
    recipient_email = order.get_customer_email()
    send_kwargs, email_context = get_email_context()
    email_context["order_details_url"] = build_absolute_uri(
        reverse("order:details", kwargs={"token": order.token})
    )
    email_context["order"] = order

    # Order confirmation template requires additional information
    if template == CONFIRM_ORDER_TEMPLATE:
        email_markup = get_order_confirmation_markup(order)
        email_context["schema_markup"] = email_markup

    return {
        "recipient_list": [recipient_email],
        "template_name": template,
        "context": email_context,
        **send_kwargs,
    }


def collect_staff_order_notification_data(order_pk, template):
    """Collect the required data for sending emails.

    Args:
        order_pk (int): order primary key
        template (str): email template path

    """
    order = Order.objects.get(pk=order_pk)
    staff_notifications = StaffNotificationRecipient.objects.filter(
        active=True, user__is_active=True, user__is_staff=True
    )
    recipient_emails = [
        notification.get_email() for notification in staff_notifications
    ]
    send_kwargs, email_context = get_email_context()
    email_context["order_details_url"] = build_absolute_uri(
        reverse("order:details", kwargs={"token": order.token})
    )
    email_context["order"] = order
    email_markup = get_order_confirmation_markup(order)
    email_context["schema_markup"] = email_markup

    return {
        "recipient_list": recipient_emails,
        "template_name": template,
        "context": email_context,
        **send_kwargs,
    }


def collect_data_for_fullfillment_email(order_pk, template, fulfillment_pk):
    fulfillment = Fulfillment.objects.get(pk=fulfillment_pk)
    email_data = collect_data_for_email(order_pk, template)
    lines = fulfillment.lines.all()
    physical_lines = [line for line in lines if not line.order_line.is_digital]
    digital_lines = [line for line in lines if line.order_line.is_digital]
    context = email_data["context"]
    context.update(
        {
            "fulfillment": fulfillment,
            "physical_lines": physical_lines,
            "digital_lines": digital_lines,
        }
    )
    return email_data


@app.task
def send_order_confirmation(order_pk, user_pk=None):
    """Send order confirmation email."""
    email_data = collect_data_for_email(order_pk, CONFIRM_ORDER_TEMPLATE)
    send_templated_mail(**email_data)
    events.email_sent_event(
        order=email_data["context"]["order"],
        user=None,
        user_pk=user_pk,
        email_type=events.OrderEventsEmails.ORDER,
    )


@app.task
def send_staff_order_confirmation(order_pk):
    """Send order confirmation email."""
    staff_email_data = collect_staff_order_notification_data(
        order_pk, STAFF_CONFIRM_ORDER_TEMPLATE
    )
    if staff_email_data["recipient_list"]:
        send_templated_mail(**staff_email_data)


@app.task
def send_fulfillment_confirmation(order_pk, fulfillment_pk):
    email_data = collect_data_for_fullfillment_email(
        order_pk, CONFIRM_FULFILLMENT_TEMPLATE, fulfillment_pk
    )
    send_templated_mail(**email_data)


def send_fulfillment_confirmation_to_customer(order, fulfillment, user):
    send_fulfillment_confirmation.delay(order.pk, fulfillment.pk)

    events.email_sent_event(
        order=order, user=user, email_type=events.OrderEventsEmails.FULFILLMENT
    )

    # If digital lines were sent in the fulfillment email,
    # trigger the event
    if any((line for line in order if line.variant.is_digital())):
        events.email_sent_event(
            order=order, user=user, email_type=events.OrderEventsEmails.DIGITAL_LINKS
        )


@app.task
def send_fulfillment_update(order_pk, fulfillment_pk):
    email_data = collect_data_for_fullfillment_email(
        order_pk, UPDATE_FULFILLMENT_TEMPLATE, fulfillment_pk
    )
    send_templated_mail(**email_data)


@app.task
def send_payment_confirmation(order_pk):
    """Send the payment confirmation email."""
    email_data = collect_data_for_email(order_pk, CONFIRM_PAYMENT_TEMPLATE)
    send_templated_mail(**email_data)
