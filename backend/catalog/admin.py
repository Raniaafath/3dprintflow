from django.contrib import admin

from .models import Color, Material, Product, ProductDocument, ProductType

@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ("type_name", "requires_components", "created_at")
    search_fields = ("type_name",)

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("material_name", "material_code", "is_available", "cost_per_kg", "density", "workspace", "created_at")
    list_filter = ("is_available", "workspace")
    search_fields = ("material_name", "material_code")
    autocomplete_fields = ("workspace",)

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("color_name", "color_code", "hex_value", "is_available", "workspace", "created_at")
    list_filter = ("is_available", "workspace")
    search_fields = ("color_name", "color_code", "hex_value")
    autocomplete_fields = ("workspace",)

class ProductDocumentInline(admin.TabularInline):
    model = ProductDocument
    extra = 1
    fields = ("kind", "version", "file", "is_primary", "size", "checksum", "uploaded_at")
    readonly_fields = ("size", "checksum", "uploaded_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "sku", "ean", "product_type", "price", "is_personalized", "workspace", "updated_at")
    list_filter = ("product_type", "is_personalized", "workspace")
    search_fields = ("title", "sku", "ean")
    autocomplete_fields = ("workspace", "product_type")
    exclude = ("pdf_fiche_technique",)
    inlines = [ProductDocumentInline]


@admin.register(ProductDocument)
class ProductDocumentAdmin(admin.ModelAdmin):
    list_display = ("product", "kind", "version", "is_primary", "size", "uploaded_at")
    list_filter = ("kind", "is_primary")
    search_fields = ("product__title", "version", "checksum")
