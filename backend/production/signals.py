from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import FilamentTransaction

@receiver([post_save, post_delete], sender=FilamentTransaction)
def update_filament_stock(sender, instance, **kwargs):
    f = instance.filament
    # recompute from scratch to stay consistent
    total_in = f.transactions.filter(kind__in=["in","adjustment"]).aggregate(s=models.Sum("quantity_grams"))["s"] or 0
    total_out = f.transactions.filter(kind__in=["out","waste"]).aggregate(s=models.Sum("quantity_grams"))["s"] or 0
    f.current_stock_grams = total_in - total_out
    f.save(update_fields=["current_stock_grams", "updated_at"])
