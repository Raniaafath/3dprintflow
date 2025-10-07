from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import OrderItem


@receiver([post_save, post_delete], sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    order = instance.order
    if order.totals_locked:
        return
    order.recompute_total()
    order.save(update_fields=["total_cost", "updated_at"])
