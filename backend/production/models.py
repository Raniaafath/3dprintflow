from django.db import models

# Create your models here.
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError

# ---- Printers ----

class PrinterType(models.Model):
    printer_type_id = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    max_build_volume = models.CharField(max_length=50, blank=True)
    supported_materials = models.JSONField(default=list, blank=True)  # e.g. ["PLA","PETG"]
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "printer_types"
        ordering = ["type_name"]

    def __str__(self):
        return self.type_name


class Printer(models.Model):
    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        PRINTING = "printing", "Printing"
        MAINTENANCE = "maintenance", "Maintenance"
        ERROR = "error", "Error"

    printer_id = models.BigAutoField(primary_key=True)
    workspace = models.ForeignKey("core.Workspace", on_delete=models.CASCADE)
    machine_name = models.CharField(max_length=100)
    printer_type = models.ForeignKey(PrinterType, on_delete=models.PROTECT)
    connection_type = models.CharField(max_length=20, default="WiFi")
    printer_url = models.CharField(max_length=255, blank=True)
    api_user = models.CharField(max_length=100, blank=True)
    api_key = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OFFLINE)
    nozzle_temperature_max = models.IntegerField(default=300)
    bed_temperature_max = models.IntegerField(default=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "printers"
        indexes = [
            models.Index(fields=["workspace"]),
            models.Index(fields=["status"]),
            models.Index(fields=["printer_type"]),
        ]

    def __str__(self):
        return f"{self.machine_name} ({self.printer_type})"


# ---- Filament inventory ----

class Filament(models.Model):
    filament_id = models.BigAutoField(primary_key=True)
    workspace = models.ForeignKey("core.Workspace", on_delete=models.CASCADE)
    material = models.ForeignKey("catalog.Material", on_delete=models.PROTECT)
    color = models.ForeignKey("catalog.Color", on_delete=models.PROTECT)
    filament_name = models.CharField(max_length=100)
    filament_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    current_stock_grams = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    safety_stock_grams = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("500"))
    reorder_point_grams = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("1000"))
    cost_per_gram = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "filaments"
        indexes = [
            models.Index(fields=["workspace"]),
            models.Index(fields=["material", "color"]),
            models.Index(fields=["is_available"]),
        ]

    def __str__(self):
        return f"{self.filament_name} ({self.material}/{self.color})"


class FilamentTransaction(models.Model):
    class Kind(models.TextChoices):
        IN = "in", "In"
        OUT = "out", "Out"
        ADJUSTMENT = "adjustment", "Adjustment"
        WASTE = "waste", "Waste"

    transaction_id = models.BigAutoField(primary_key=True)
    filament = models.ForeignKey(Filament, on_delete=models.CASCADE, related_name="transactions")
    # we’ll add link to PrintJob below
    kind = models.CharField(max_length=12, choices=Kind.choices)
    quantity_grams = models.DecimalField(max_digits=12, decimal_places=3)
    previous_stock = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    new_stock = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    print_job = models.ForeignKey("production.PrintJob", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "filament_transactions"
        indexes = [
            models.Index(fields=["filament"]),
            models.Index(fields=["kind", "created_at"]),
        ]

    def clean(self):
        if self.quantity_grams is None or self.quantity_grams <= 0:
            raise ValidationError({"quantity_grams": "Quantity must be > 0"})

    def __str__(self):
        return f"{self.kind} {self.quantity_grams}g on {self.filament}"


# ---- Print jobs (minimal) ----

class PrintJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        QUEUED = "queued", "Queued"
        PRINTING = "printing", "Printing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    print_job_id = models.BigAutoField(primary_key=True)
    workspace = models.ForeignKey("core.Workspace", on_delete=models.CASCADE)
    order_item = models.ForeignKey("orders.OrderItem", on_delete=models.PROTECT, related_name="print_jobs")
    # We’ll link to ProductComponent later; for now, store the product and optional component label
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    component_label = models.CharField(max_length=100, blank=True)

    printer = models.ForeignKey(Printer, on_delete=models.SET_NULL, null=True, blank=True)
    filament_used = models.ForeignKey(Filament, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    priority = models.IntegerField(default=1)
    estimated_print_time = models.IntegerField(null=True, blank=True)  # minutes
    actual_print_time = models.IntegerField(null=True, blank=True)     # minutes
    material_used_grams = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "print_jobs"
        indexes = [
            models.Index(fields=["workspace"]),
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["printer"]),
        ]
        ordering = ["status", "-priority", "created_at"]

    def __str__(self):
        return f"Job #{self.print_job_id} → {self.product.title} x {self.order_item.quantity}"

    def clean(self):
        if self.priority is not None and self.priority < 1:
            raise ValidationError({"priority": "Priority must be ≥ 1"})
