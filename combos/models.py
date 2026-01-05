from django.db import models

# Create your models here.
class Combo(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    combo_price = models.DecimalField(max_digits=13, decimal_places=2)

    is_auto_apply = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    max_apply_quantity = models.PositiveIntegerField(null=True, blank=True)

    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ComboItem(models.Model):
    combo = models.ForeignKey(
        Combo,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('combo', 'product')

    def __str__(self):
        return f"{self.combo.name} - {self.product.name} x {self.quantity}"
