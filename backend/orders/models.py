from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import models


# --------- Platform & Status catalogs ---------

class PlatformSource(models.Model):
    """
    Source marketplace/platform for customers/orders (Manual, Shopify, Etsy, Billbee, Amazon, eBay, ...).
    """
    platform_id = models.AutoField(primary_key=True)
    platform_name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "platform_sources"

    def __str__(self) -> str:
        return self.platform_name


class OrderStatus(models.Model):
    """
    Global status catalog. Orders will FK to this.
    """
    status_id = models.AutoField(primary_key=True)
    status_name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_status"
        ordering = ["sort_order", "status_name"]

    def __str__(self) -> str:
        return self.status_name


# --------- Customers ---------

class Customer(models.Model):
    """
    Customers are workspace-scoped. Email is optionally unique per workspace when provided.
    """
    customer_id = models.BigAutoField(primary_key=True)
    workspace = models.ForeignKey('core.Workspace', on_delete=models.CASCADE)

    # Billbee now; keep for easy testing
    customer_billbee_id = models.BigIntegerField(null=True, blank=True)
    platform = models.ForeignKey(PlatformSource, null=True, blank=True, on_delete=models.SET_NULL)

    # future-proof generic external mapping (works for any integration)
    external_id = models.CharField(max_length=120, null=True, blank=True)
    external_payload = models.JSONField(null=True, blank=True)

    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers"
        indexes = [
            models.Index(fields=["platform"]),
            models.Index(fields=["email"]),
            models.Index(fields=["workspace", "name"]),
            models.Index(fields=["workspace", "platform", "external_id"]),
        ]
        constraints = [
            # email unique within a workspace when present
            models.UniqueConstraint(
                fields=["workspace", "email"],
                name="uniq_customer_email_per_workspace_when_present",
                condition=models.Q(email__isnull=False),
            ),
            # external id unique per (workspace, platform) when present
            models.UniqueConstraint(
                fields=["workspace", "platform", "external_id"],
                name="uniq_customer_external_when_present",
                condition=models.Q(external_id__isnull=False),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.email or 'no-email'})"


# --------- Orders & Items ---------

class Order(models.Model):
    """Customer order scoped to a workspace.

    Integrations (Billbee/Shopify/etc.) should:
    * set ``total_cost`` to the marketplace total
      and copy it into ``external_total_cost`` for auditing
    * mark ``totals_locked=True`` so signals do not recompute totals

    Manual orders keep ``totals_locked=False`` and let the signal
    recompute totals whenever items change.
    """
    order_id = models.BigAutoField(primary_key=True)
    workspace = models.ForeignKey('core.Workspace', on_delete=models.CASCADE)

    order_number = models.CharField(max_length=50)  # unique per workspace
    order_billbee_id = models.BigIntegerField(null=True, blank=True)

    customer = models.ForeignKey('orders.Customer', on_delete=models.PROTECT)
    status = models.ForeignKey('orders.OrderStatus', on_delete=models.PROTECT)

    platform = models.ForeignKey('orders.PlatformSource', null=True, blank=True, on_delete=models.SET_NULL)

    # future-proof generic external mapping
    external_id = models.CharField(max_length=120, null=True, blank=True)
    external_payload = models.JSONField(null=True, blank=True)

    total_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    external_total_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="TND")
    totals_locked = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    is_personalized = models.BooleanField(default=False)
    shipping_address = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["status"]),
            models.Index(fields=["platform"]),
            models.Index(fields=["paid_at"]),
            models.Index(fields=["workspace", "order_number"]),
            models.Index(fields=["workspace", "platform", "external_id"]),
        ]
        unique_together = (("workspace", "order_number"),)
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "platform", "external_id"],
                name="uniq_order_external_when_present",
                condition=models.Q(external_id__isnull=False),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.order_number} — {self.customer.name}"

    def recompute_total(self):
        agg = self.items.aggregate(s=models.Sum("total_price"))
        self.total_cost = agg["s"] or Decimal("0.00")


class OrderItem(models.Model):
    """Line item for an order.

    Behaviour rules:
    * ``attributes`` is always stored as JSON (never NULL)
    * When the parent order is not locked, the unit price defaults to
      the linked product's price if left blank
    * ``total_price`` is only calculated when the marketplace did not
      provide one, using ROUND_HALF_UP rounding
    """
    order_item_id = models.BigAutoField(primary_key=True)
    order_item_billbee_id = models.BigIntegerField(null=True, blank=True)

    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey('catalog.Product', on_delete=models.PROTECT)

    quantity = models.DecimalField(max_digits=12, decimal_places=3)  # > 0
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    is_personalized = models.BooleanField(default=False)
    attributes = models.JSONField(default=dict, blank=True)

    # future-proof generic external mapping
    external_id = models.CharField(max_length=120, null=True, blank=True)
    external_payload = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "order_items"
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["product"]),
            models.Index(fields=["is_personalized"]),
            models.Index(fields=["order", "external_id"]),
        ]
        # avoid duplicate identical lines
        unique_together = (("order", "product", "is_personalized", "attributes"),)
        constraints = [
            models.UniqueConstraint(
                fields=["order", "external_id"],
                name="uniq_orderitem_external_when_present",
                condition=models.Q(external_id__isnull=False),
            ),
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name="orderitem_qty_gt_0",
            ),
            models.CheckConstraint(
                check=models.Q(unit_price__gte=0) | models.Q(unit_price__isnull=True),
                name="orderitem_unit_price_gte_0",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.order.order_number} → {self.product.title} x {self.quantity}"

    def clean(self):
        if self.quantity is None or self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be > 0"})
        if self.unit_price is not None and self.unit_price < 0:
            raise ValidationError({"unit_price": "Must be ≥ 0"})

    def save(self, *args, **kwargs):
        if self.attributes is None:
            self.attributes = {}

        if self.unit_price is None and not self.order.totals_locked:
            if self.product and self.product.price is not None:
                self.unit_price = self.product.price

        if (
            self.total_price is None
            and self.unit_price is not None
            and self.quantity is not None
        ):
            self.total_price = (self.unit_price * self.quantity).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        super().save(*args, **kwargs)
