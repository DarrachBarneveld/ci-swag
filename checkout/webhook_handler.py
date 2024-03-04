"""Stripe webhook handler"""

import stripe
import json
import time

from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from products.models import Product
from programs.models import Program
from profiles.models import UserProfile, Subscription
from cart.utils import get_item_from_item_id


from .models import Order, OrderLineItem


class StripeWH_Handler:
    """Handle Stripe webhooks"""

    def __init__(self, request):
        self.request = request

    def _send_confirmation_email(self, order):
        """Send the user a confirmation email"""
        customer_email = order.email
        subject = render_to_string(
            'checkout/confirmation_emails/confirmation_email_subject.txt',
            {'order': order})
        body = render_to_string(
            'checkout/confirmation_emails/confirmation_email_body.txt',
            {'order': order, 'contact_email': settings.DEFAULT_FROM_EMAIL})

        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [customer_email]
        )

    def handle_event(self, event):
        """
        Handle a generic/unknown/unexpected webhook event
        """
        return HttpResponse(
            content=f'Unhandled webhook received: {event["type"]}',
            status=200)

    def handle_payment_intent_succeeded(self, event):
        """
        Handle the payment_intent.succeeded webhook from Stripe
        """
        intent = event.data.object
        pid = intent.id
        cart = intent.metadata.cart
        save_info = intent.metadata.save_info

        # Get the Charge object
        stripe_charge = stripe.Charge.retrieve(
            intent.latest_charge
        )

        billing_details = stripe_charge.billing_details
        shipping_details = intent.shipping
        grand_total = round(stripe_charge.amount / 100, 2)

        # Clean data in the shipping details
        for field, value in shipping_details.address.items():
            if value == "":
                shipping_details.address[field] = None

        profile = None
        username = intent.metadata.username

        if username != 'AnonymousUser':
            profile = UserProfile.objects.get(user__username=username)
            if save_info:
                profile.default_phone_number = \
                    shipping_details.phone
                profile.default_country = shipping_details.address.country
                profile.default_postcode = shipping_details.address.postal_code
                profile.default_town_or_city = shipping_details.address.city
                profile.default_street_address1 = \
                    shipping_details.address.line1
                profile.default_street_address2 = \
                    shipping_details.address.line2
                profile.default_county = shipping_details.address.state
                profile.save()

        order_exists = False
        attempt = 1
        while attempt <= 5:
            orders = Order.objects.all()
            try:
                order = Order.objects.get(
                    full_name__iexact=shipping_details.name,
                    email__iexact=billing_details.email,
                    phone_number__iexact=shipping_details.phone,
                    country__iexact=shipping_details.address.country,
                    postcode__iexact=shipping_details.address.postal_code,
                    town_or_city__iexact=shipping_details.address.city,
                    street_address1__iexact=shipping_details.address.line1,
                    street_address2__iexact=shipping_details.address.line2,
                    county__iexact=shipping_details.address.state,
                    grand_total=grand_total,
                    original_cart=cart,
                    stripe_pid=pid,
                )
                order_exists = True
                break
            except Order.DoesNotExist:
                attempt += 1
                time.sleep(1)
        if order_exists:
            self._send_confirmation_email(order)
            return HttpResponse(
                content=(
                    f'Webhook received: {event["type"]} |'
                    " SUCCESS: Verified order already in database"
                ),
                status=200,
            )
        else:
            order = None
            try:
                order = Order.objects.create(
                    full_name=shipping_details.name,
                    user_profile=profile,
                    email=billing_details.email,
                    phone_number=shipping_details.phone,
                    country=shipping_details.address.country,
                    postcode=shipping_details.address.postal_code,
                    town_or_city=shipping_details.address.city,
                    street_address1=shipping_details.address.line1,
                    street_address2=shipping_details.address.line2,
                    county=shipping_details.address.state,
                    original_cart=cart,
                    stripe_pid=pid,
                )
                
                if profile is not None:
                    product_discount = profile.subscription.product_discount
                    program_discount = profile.subscription.program_discount
                
                for item_id, item_data in json.loads(cart).items():
                    discount = 0
                    if profile is not None:
                        # Membership discount
                        item = get_item_from_item_id(item_id)
                        # Apply discounts to products if user has a subscription
                        if isinstance(item, Subscription):
                            content_type = \
                                ContentType.objects.get_for_model(Subscription) 
                        elif isinstance(item, Program):
                            content_type = \
                                ContentType.objects.get_for_model(Program)
                            total_item_price = item_data * item.total_final_price
                            if program_discount:
                                discount = program_discount
                                item.price = item.price * (1 - program_discount / 100)
                                item.save()
                        else:
                            content_type = \
                                ContentType.objects.get_for_model(Product)
                            total_item_price = item_data * item.total_final_price
                            if product_discount:
                                item.price = item.price * (1 - product_discount / 100)
                                item.save()

                    else:
                        item = get_item_from_item_id(item_id)
                        if isinstance(item, Subscription):
                            content_type = \
                                ContentType.objects.get_for_model(Subscription)
                        if isinstance(item, Program):
                            content_type = \
                                ContentType.objects.get_for_model(Program)
                        if isinstance(item, Product):
                            content_type = \
                                ContentType.objects.get_for_model(Product)


                    order_line_item = OrderLineItem(
                            order=order,
                            content_type=content_type,
                            object_id=item_id,
                            quantity=item_data,
                            subscription_discount=discount
                        )
                    order_line_item.save()

            except Exception as e:
                if order:
                    order.delete()
                return HttpResponse(
                    content=f'Webhook received: {event["type"]} | ERROR: {e}',
                    status=500)
        self._send_confirmation_email(order)

        return HttpResponse(
            content=(
                f'Webhook received: {event["type"]}'
                " | SUCCESS: Created order in webhook"
            ),
            status=200,
        )

    def handle_payment_intent_payment_failed(self, event):
        """
        Handle the payment_intent.payment_failed webhook from Stripe
        """
        return HttpResponse(
            content=f'Webhook received: {event["type"]}',
            status=200)
