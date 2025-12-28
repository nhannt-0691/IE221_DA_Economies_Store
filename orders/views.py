from __future__ import annotations

from django.shortcuts import render
from django.db import models
from .models import Order, OrderItem
from accounts.models import User
from products.models import Product
from cart.models import CartItem
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, IsAdminUser 
from django.db import transaction
from decimal import Decimal
from accounts.constants import get_rank_by_amount

def build_order_data(order):
    def to_local(dt):
        return timezone.localtime(dt).strftime("%Y-%m-%d %H:%M:%S") if dt else None
    return {
        'id': order.id,
        'user_id': order.user_id,
        'customer_name': order.customer_name,
        'customer_phone': order.customer_phone,
        'customer_address': order.customer_address,
        'cart_items': [
            {
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price_at_order': float(item.price_at_order)  # <-- convert
            } for item in order.items.all()
        ],
        'rank_at_time': order.rank_at_time,
        'subtotal_amount': float(order.subtotal_amount),   # <-- convert
        'discount_amount': float(order.discount_amount),   # <-- convert
        'final_amount': float(order.final_amount),         # <-- convert
        'payment_method': order.payment_method,
        'order_status': order.order_status,
        'ordered_at': to_local(order.ordered_at),
    }

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        data = request.data

        cart_items = data.get("cart_items", [])
        if not cart_items:
            return Response({"error": "Cart is empty"}, status=400)

        subtotal_amount = Decimal("0.00")
        order_items_data = {}
        product_ids = []

        # Gom số lượng
        for item in cart_items:
            product_id = item.get("product_id")
            quantity = int(item.get("quantity", 1))

            if quantity <= 0:
                return Response(
                    {"error": "Quantity must be greater than 0"},
                    status=400
                )

            order_items_data[product_id] = (
                order_items_data.get(product_id, 0) + quantity
            )

        products = Product.objects.select_for_update().filter(
            id__in=order_items_data.keys()
        )

        if products.count() != len(order_items_data):
            return Response({"error": "Some products not found"}, status=404)

        # Tính subtotal
        for product in products:
            quantity = order_items_data[product.id]
            subtotal_amount += Decimal(product.price) * quantity
            product_ids.append(product.id)

        rank, bonus_percent = get_rank_by_amount(user.total_spent)

        discount_amount = (
            subtotal_amount * Decimal(bonus_percent) / Decimal(100)
        )
        final_amount = subtotal_amount - discount_amount

        # Tạo order
        order = Order.objects.create(
            user=user,
            customer_name=data.get("customer_name"),
            customer_phone=data.get("customer_phone"),
            customer_address=data.get("customer_address"),
            payment_method=data.get("payment_method"),

            subtotal_amount=subtotal_amount,
            rank_at_time=rank,
            discount_amount=discount_amount,
            final_amount=final_amount,
        )

        # Tạo order items
        for product in products:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=order_items_data[product.id],
                price_at_order=product.price
            )

        # Xóa cart
        CartItem.objects.filter(
            cart__user=user,
            product_id__in=product_ids
        ).delete()

        return Response(
            {
                "message": "Order created successfully",
                "order_id": order.id,
                "rank_at_time": rank,
                "subtotal_amount": subtotal_amount,
                
                "bonus_percent": bonus_percent,
                "discount_amount": discount_amount,
                "final_amount": final_amount
            },
            status=201
        )


        
class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        orders = Order.objects.filter(user=user).order_by('-final_amount')
        
        orders_data = [build_order_data(order) for order in orders]
        return Response({"orders": orders_data}, status=200)


    
class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        user = request.user
        try:
            order = Order.objects.get(id=order_id, user=user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        order_data = build_order_data(order)
        return Response({"order": order_data}, status=200)
    
class DeleteOrderView(APIView):
    permission_classes =  [IsAuthenticated]
    
    def delete(self, request, order_id):
        user = request.user
        try:
            order = Order.objects.get(id=order_id, user=user)
            if order.order_status != 'Pending':
                return Response({"error": "Only pending orders can be deleted"}, status=400)
            order.delete()
            return Response({"message": "Order deleted successfully"}, status=200)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)
        
class UpdateInfoStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    allow_field = ['customer_name', 'customer_phone', 'customer_address']
    
    def patch(self, request, order_id):
        user = request.user
        data = request.data

        invalid_fields = [field for field in data if field not in self.allow_field]
        if invalid_fields:
            return Response(
                {"error": "These fields are not allowed to update", "fields": invalid_fields},
                status=status.HTTP_400_BAD_REQUEST
            )

        try: 
            order = Order.objects.get(id = order_id, user=user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        
        for field in self.allow_field:
            if field in data:
                value = data[field]
                
                if order.order_status != 'Pending':
                    return Response({"error": "Only pending orders can be updated"}, status=400)
                setattr(order, field, value)

        order.save()

        return Response({
            "message": "Order information updated successfully",
            "order": build_order_data(order)
        }, status=status.HTTP_200_OK)
        
        
#ADMIN VIEWS 
class AdminOrderListView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        orders = Order.objects.all().order_by('ordered_at')
        orders_data = [build_order_data(order) for order in orders]
        return Response({"orders": orders_data}, status=200)
    
    
    
ALLOWED_TRANSITIONS = {
    Order.PENDING: [Order.CONFIRMED, Order.CANCELLED],
    Order.CONFIRMED: [Order.SHIPPING, Order.CANCELLED],
    Order.SHIPPING: [Order.COMPLETED, Order.CANCELLED],
    Order.COMPLETED: [],
    Order.CANCELLED: [],
}
class AdminUpdateOrderStatusView(APIView):
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def put(self, request, order_id):
        new_status = request.data.get("new_status")

        if not new_status:
            return Response(
                {"error": "new_status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_status = new_status.strip().lower()

        VALID_STATUSES = [s for s, _ in Order.ORDER_STATUS_CHOICES]
        if new_status not in VALID_STATUSES:
            return Response(
                {"error": "Invalid order status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = (
                Order.objects
                .select_for_update()
                .select_related("user")
                .get(id=order_id)
            )
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        current_status = order.order_status

        if new_status not in ALLOWED_TRANSITIONS[current_status]:
            return Response(
                {
                    "error": f"Cannot change status from {current_status} to {new_status}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user = order.user

        if new_status == Order.COMPLETED:
            if order.order_status == Order.COMPLETED:
                return Response(
                    {"error": "Order already completed"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            order.completed_at = timezone.now()

            user.total_spent += order.final_amount
            user.rank, _ = get_rank_by_amount(user.total_spent)
            user.save(update_fields=["total_spent", "rank"])

        order.order_status = new_status
        order.save()

        return Response(
            {
                "message": "Order status updated successfully",
                "order": build_order_data(order),
                "user_total_spent": str(user.total_spent),
                "user_rank": user.rank
            },
            status=status.HTTP_200_OK
        )
