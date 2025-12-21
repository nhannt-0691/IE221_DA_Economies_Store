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
                'price_at_order': str(item.price_at_order)
            } for item in order.items.all()
        ],
        'total_amount': str(order.total_amount),
        'payment_method': order.payment_method,
        'order_status': order.order_status,
        'ordered_at': to_local(order.ordered_at),
        
    }
    
from django.db import transaction

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        data = request.data

        cart_items = data.get("cart_items", [])
        if not cart_items:
            return Response({"error": "Cart is empty"}, status=400)

        total_amount = Decimal("0.00")
        order_items_data = {}
        product_ids = []

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

        order = Order.objects.create(
            user=user,
            customer_name=data.get("customer_name"),
            customer_phone=data.get("customer_phone"),
            customer_address=data.get("customer_address"),
            payment_method=data.get("payment_method"),
            order_status=data.get("order_status", 'Pending'),
            ordered_at=timezone.now(),
            total_amount=Decimal("0.00"),
        )

        for product in products:
            quantity = order_items_data[product.id]
            price = Decimal(product.price)

            total_amount += price * quantity

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_order=price
            )

            product_ids.append(product.id)

        order.total_amount = total_amount
        order.save(update_fields=["total_amount"])

        CartItem.objects.filter(
            cart__user=user,
            product_id__in=product_ids
        ).delete()

        return Response(
            {
                "message": "Order created successfully",
                "order": build_order_data(order)
            },
            status=201
        )

        
class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        orders = Order.objects.filter(user=user).order_by('ordered_at')
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

class UpdateOrderStatusView(APIView):
    permission_classes = [IsAdminUser]
    
    def put(self, request, order_id):
        data = request.data
        new_status = data.get("new_status")
        new_status = new_status.strip().lower()
        
        VALID_STATUSES = [status for status, _ in Order.ORDER_STATUS_CHOICES]

        if new_status not in VALID_STATUSES:
            return Response(
                {"error": "Invalid order status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        
        order.order_status = new_status
        order.save()
        
        return Response({       
            "message": "Order status updated successfully",
            "order": build_order_data(order)
        }, status=status.HTTP_200_OK)