from django.contrib import admin
from .models import PlatformSource, OrderStatus, Customer, Order, OrderItem

@admin.register(PlatformSource)
class PlatformSourceAdmin(admin.ModelAdmin):
    list_display = ("platform_name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("platform_name", "description")

@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ("status_name", "sort_order", "is_active", "created_at")
    list_editable = ("sort_order", "is_active")
    search_fields = ("status_name",)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "platform", "workspace", "updated_at")
    list_filter = ("platform", "workspace")
    search_fields = ("name", "email", "phone")
    autocomplete_fields = ("workspace", "platform")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ("product", "quantity", "unit_price", "total_price", "is_personalized", "attributes", "external_id")
    readonly_fields = ("total_price",)
    autocomplete_fields = ("product",)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # If you added 'currency', 'totals_locked', 'external_total_cost' keep them here; if not, remove them.
    list_display = (
        "order_number", "customer", "status", "currency", "total_cost",
        "platform", "workspace", "updated_at"
    )
    list_filter = ("status", "platform", "workspace", "currency")
    search_fields = ("order_number", "invoice_number", "customer__name", "customer__email")
    autocomplete_fields = ("workspace", "customer", "status", "platform")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "unit_price", "total_price", "is_personalized", "updated_at")
    list_filter = ("is_personalized", "order__workspace")
    search_fields = ("order__order_number", "product__title", "external_id")
    autocomplete_fields = ("order", "product")
    list_select_related = ("order", "product")
    date_hierarchy = "created_at"
    readonly_fields = ("total_price",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "attributes" in form.base_fields:
            form.base_fields["attributes"].initial = {}
        return form
