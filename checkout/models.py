"""Checkout Models"""

import uuid
from decimal import Decimal
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from phonenumber_field.modelfields import PhoneNumberField
from django_countries.fields import CountryField


from profiles.models import UserProfile

class Order(models.Model):
    """
    Model representing an order placed by a customer
    """

    order_number = models.CharField(max_length=32, null=False, editable=False)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='orders')
    full_name = models.CharField(max_length=50, null=False, blank=False)
    email = models.EmailField(max_length=254, null=False, blank=False)
    phone_number = PhoneNumberField(blank=True, null=True)
    postcode = models.CharField(max_length=20, null=True, blank=True)
    town_or_city = models.CharField(max_length=40, null=False, blank=False)
    street_address1 = models.CharField(max_length=80, null=False, blank=False)
    street_address2 = models.CharField(max_length=80, null=True, blank=True)
    country = CountryField(blank_label='Country *', null=False, blank=False, default='IE')
    county = models.CharField(max_length=80, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    delivery_cost = models.DecimalField(max_digits=6, decimal_places=2, null=False, default=0)
    order_total = models.DecimalField(max_digits=10, decimal_places=2, null=False, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, null=False, default=0)
    original_cart = models.TextField(null=False, blank=False, default='')
    stripe_pid = models.CharField(max_length=254, null=False, blank=False, default='')

    def _generate_order_number(self):
        """
        Generate a random, unique order number using UUID
        """
        return uuid.uuid4().hex.upper()

    


    def save(self, *args, **kwargs):
        """
        Override the original save method to set the order number
        if it hasn't been set already.
        """
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number

class OrderLineItem(models.Model):
    """
    Model representing a line item within an order.
    An Order line item can be of any type of product or subscription.
    This is achieved using Django's content types framework.

    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='lineitems')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    quantity = models.IntegerField(null=False, blank=False, default=0)
    lineitem_total = models.DecimalField(
        max_digits=6, decimal_places=2, null=False, blank=False,
        editable=False)
    subscription_discount = models.DecimalField(
        blank=True, null=True, max_digits=6, decimal_places=0)
    item_total = models.DecimalField(
        max_digits=6, decimal_places=2, null=False, blank=False,
        default=0)


    def save(self, *args, **kwargs):
        """
        Override the original save method to set the lineitem total
        and update the order total.
        """

        # Calculate the total price before applying discount
        total_price = self.content_object.total_final_price * self.quantity

        # Apply discount if it's not None
        if self.subscription_discount is not None:
            discount_amount = total_price * (self.subscription_discount / Decimal(100))
            total_price -= discount_amount

        # Assign the calculated total price to lineitem_total
        self.lineitem_total = total_price

        self.item_total = total_price / self.quantity

        super().save(*args, **kwargs)

    def __str__(self):
        return f'SKU {self.content_object.sku} on order {self.order.order_number}'
