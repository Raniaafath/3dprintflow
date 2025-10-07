from django.contrib import admin
from .models import PrinterType, Printer, Filament, FilamentTransaction, PrintJob

@admin.register(PrinterType)
class PrinterTypeAdmin(admin.ModelAdmin):
    list_display = ("type_name", "max_build_volume", "is_active", "created_at")
    search_fields = ("type_name",)
    list_filter = ("is_active",)

@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ("machine_name", "printer_type", "status", "workspace", "location", "updated_at")
    list_filter = ("status", "printer_type", "workspace")
    search_fields = ("machine_name", "location")
    autocomplete_fields = ("workspace", "printer_type")

class FilamentTransactionInline(admin.TabularInline):
    model = FilamentTransaction
    extra = 1
    readonly_fields = ("previous_stock", "new_stock", "created_at")

@admin.register(Filament)
class FilamentAdmin(admin.ModelAdmin):
    list_display = ("filament_name", "material", "color", "current_stock_grams", "location", "workspace", "is_available")
    list_filter = ("material", "color", "workspace", "is_available")
    search_fields = ("filament_name", "filament_code", "location")
    autocomplete_fields = ("workspace", "material", "color")
    inlines = [FilamentTransactionInline]

@admin.register(FilamentTransaction)
class FilamentTransactionAdmin(admin.ModelAdmin):
    list_display = ("filament", "kind", "quantity_grams", "previous_stock", "new_stock", "created_at", "created_by")
    list_filter = ("kind", "created_at")
    autocomplete_fields = ("filament", "print_job")

@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    list_display = ("print_job_id", "product", "order_item", "status", "priority", "printer", "filament_used", "updated_at")
    list_filter = ("status", "priority", "printer", "workspace")
    search_fields = ("product__title", "order_item__order__order_number")
    autocomplete_fields = ("workspace", "order_item", "product", "printer", "filament_used")
