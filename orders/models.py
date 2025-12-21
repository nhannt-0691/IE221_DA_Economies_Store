from django.db import models


class Order(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    SHIPPING = 'shipping'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    ORDER_STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (SHIPPING, 'Shipping'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=20)        
    customer_address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    order_status = models.CharField(max_length=30, choices=ORDER_STATUS_CHOICES,
        default=PENDING)
    ordered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE
    )
    price_at_order = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
