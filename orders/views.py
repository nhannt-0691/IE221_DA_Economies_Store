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
from django.db.models import Sum, Count, Avg
from datetime import datetime
from utils.email import send_order_email
from combos.models import Combo, ComboItem
from django.db.models import Q

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
                'price_at_order': float(item.price_at_order) 
            } for item in order.items.all()
        ],
        'rank_at_time': order.rank_at_time,
        'subtotal_amount': float(order.subtotal_amount),  
        'discount_amount': float(order.discount_amount), 
        'final_amount': float(order.final_amount),        
        'payment_method': order.payment_method,
        'order_status': order.order_status,
        'ordered_at': to_local(order.ordered_at),
    }


from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        data = request.data

        # =====================================================
        # 1️⃣ LẤY CART
        # =====================================================
        cart_items = CartItem.objects.select_related("product").filter(
            cart__user=user
        )

        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=400)

        # =====================================================
        # 2️⃣ GOM SỐ LƯỢNG SẢN PHẨM
        # =====================================================
        order_items_data = {}
        product_ids = []

        for item in cart_items:
            if item.quantity <= 0:
                return Response(
                    {"error": "Quantity must be greater than 0"},
                    status=400
                )

            order_items_data[item.product_id] = (
                order_items_data.get(item.product_id, 0) + item.quantity
            )

        # =====================================================
        # 3️⃣ LOCK PRODUCT & TÍNH SUBTOTAL GỐC
        # =====================================================
        products = Product.objects.select_for_update().filter(
            id__in=order_items_data.keys()
        )

        if products.count() != len(order_items_data):
            return Response({"error": "Some products not found"}, status=404)

        subtotal_amount = Decimal("0.00")

        for product in products:
            quantity = order_items_data[product.id]
            subtotal_amount += product.price * quantity
            product_ids.append(product.id)

        # =====================================================
        # AUTO APPLY COMBO (DÙNG combo_price TRONG DB)
        # =====================================================
        valid_combos = Combo.objects.filter(
            is_active=True,
            is_auto_apply=True
        ).filter(
            Q(max_apply_quantity__isnull=True) | Q(max_apply_quantity__gt=0)
        )

        subtotal_after_combo = subtotal_amount
        applied_combos = []

        def get_combo_apply_times(order_items, combo):
            """
            Tính combo apply được bao nhiêu lần
            """
            combo_items = ComboItem.objects.filter(combo=combo)
            times = []

            for ci in combo_items:
                if ci.product_id not in order_items:
                    return 0
                times.append(order_items[ci.product_id] // ci.quantity)

            return min(times) if times else 0

        for combo in valid_combos:
            apply_times = get_combo_apply_times(order_items_data, combo)

            if apply_times <= 0:
                continue

            if combo.max_apply_quantity is not None:
                apply_times = min(apply_times, combo.max_apply_quantity)

            #  THAY GIÁ LẺ → GIÁ COMBO
            subtotal_after_combo -= combo.actual_combo_price * apply_times
            subtotal_after_combo += combo.combo_price * apply_times

            # Trừ quantity đã dùng cho combo
            for ci in ComboItem.objects.filter(combo=combo):
                order_items_data[ci.product_id] -= ci.quantity * apply_times

            applied_combos.append({
                "combo_id": combo.id,
                "apply_times": apply_times,
                "combo_price": combo.combo_price
            })

            # Giảm lượt áp dụng combo
            if combo.max_apply_quantity is not None:
                combo.max_apply_quantity -= apply_times
                combo.save(update_fields=["max_apply_quantity"])

        combo_discount = subtotal_amount - subtotal_after_combo

        # =====================================================
        # RANK DISCOUNT
        # =====================================================
        rank, bonus_percent = get_rank_by_amount(user.total_spent)

        rank_discount = (
            subtotal_after_combo * Decimal(bonus_percent) / Decimal(100)
        )

        final_amount = subtotal_after_combo - rank_discount

        # =====================================================
        # TẠO ORDER (CHỈ 1 LẦN)
        # =====================================================
        order = Order.objects.create(
            user=user,
            customer_name=data.get("customer_name"),
            customer_phone=data.get("customer_phone"),
            customer_address=data.get("customer_address"),
            payment_method=data.get("payment_method"),

            subtotal_amount=subtotal_amount,
            discount_amount=combo_discount + rank_discount,
            final_amount=final_amount,
            rank_at_time=rank,
        )

        # =====================================================
        # TẠO ORDER ITEMS
        # =====================================================
        for product in products:
            qty = order_items_data.get(product.id, 0)
            if qty > 0:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    price_at_order=product.price
                )

        # =====================================================
        # CLEAR CART
        # =====================================================
        CartItem.objects.filter(
            cart__user=user,
            product_id__in=product_ids
        ).delete()

        send_order_email(request, user)

        return Response(
            {
                "message": "Order created successfully",
                "order_id": order.id,
                "applied_combos": applied_combos,
                "subtotal": subtotal_amount,
                "combo_discount": combo_discount,
                "rank_discount": rank_discount,
                "final_amount": final_amount,
            },
            status=201
        )

class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        orders = (
            Order.objects
            .filter(user=user)
            .order_by('-ordered_at')
            .prefetch_related('items__product')
        )
        
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
            if order.order_status != Order.PENDING:
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
                
                if order.order_status != Order.PENDING:
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
        
class RevenueStatisticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from_date = request.GET.get("from")
        to_date = request.GET.get("to")

        orders = Order.objects.filter(order_status=Order.COMPLETED)

        # Lọc theo thời gian nếu có
        if from_date:
            try:
                from_date = datetime.strptime(from_date, "%Y-%m-%d")
                orders = orders.filter(ordered_at__date__gte=from_date)
            except ValueError:
                return Response(
                    {"error": "Invalid from date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if to_date:
            try:
                to_date = datetime.strptime(to_date, "%Y-%m-%d")
                orders = orders.filter(ordered_at__date__lte=to_date)
            except ValueError:
                return Response(
                    {"error": "Invalid to date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        stats = orders.aggregate(
            total_orders=Count("id"),
            total_revenue=Sum("final_amount"),
            average_order_value=Avg("final_amount")
        )

        return Response(
            {
                "from": request.GET.get("from"),
                "to": request.GET.get("to"),
                "total_orders": stats["total_orders"] or 0,
                "total_revenue": float(stats["total_revenue"] or 0),
                "average_order_value": float(stats["average_order_value"] or 0),
            },
            status=status.HTTP_200_OK
        )
