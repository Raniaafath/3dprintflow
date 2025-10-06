from django.db import models

# If your Workspace model lives elsewhere, keep the string 'core.Workspace' and ensure 'core' is in INSTALLED_APPS.
class WorkspaceScopedModel(models.Model):
    workspace = models.ForeignKey('core.Workspace', on_delete=models.CASCADE)
    class Meta:
        abstract = True

class ProductType(models.Model):
    type_id = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=100, blank=True)
    requires_components = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "product_types"
    def __str__(self): return self.type_name

class Material(WorkspaceScopedModel):
    material_id = models.AutoField(primary_key=True)
    material_name = models.CharField(max_length=50)
    material_code = models.CharField(max_length=20, blank=True)
    cost_per_kg = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    density = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "materials"
        unique_together = ("workspace", "material_name")
        indexes = [models.Index(fields=["workspace", "material_code"])]
    def __str__(self): return self.material_name

class Color(WorkspaceScopedModel):
    color_id = models.AutoField(primary_key=True)
    color_name = models.CharField(max_length=30)
    color_code = models.CharField(max_length=10, blank=True)
    hex_value = models.CharField(max_length=7, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "colors"
        unique_together = ("workspace", "color_name")
        indexes = [models.Index(fields=["workspace", "color_code"])]
    def __str__(self): return self.color_name

class Product(WorkspaceScopedModel):
    product_id = models.AutoField(primary_key=True)
    billbee_id = models.BigIntegerField(null=True, blank=True)
    sku = models.CharField(max_length=100, blank=True, null=True)  # unique per workspace via Meta
    ean = models.CharField(max_length=50, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    product_type = models.ForeignKey(ProductType, null=True, blank=True, on_delete=models.SET_NULL)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # money-friendly
    is_personalized = models.BooleanField(default=False)
    pdf_fiche_technique = models.TextField(blank=True)
    assembly_time_minutes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "products"
        indexes = [
            models.Index(fields=["workspace", "sku"]),
            models.Index(fields=["workspace", "ean"]),
            models.Index(fields=["product_type"]),
        ]
        unique_together = (("workspace", "sku"),)
    def __str__(self): return f"{self.title} ({self.sku or 'no-sku'})"
