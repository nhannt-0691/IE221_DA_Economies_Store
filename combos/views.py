from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from combos.models import Combo, ComboItem
from products.models import Product
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum, F
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_naive

# Create your views here.

def build_combo_data(combo):
    def to_local(dt):
        return timezone.localtime(dt).strftime("%Y-%m-%d %H:%M:%S") if dt else None
    return {
        'id': combo.id,
        'name': combo.name,
        'description': combo.description,
        'actual_combo_price': combo.actual_combo_price,
        'combo_price': combo.combo_price,
        'combo_items': [
            {
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
            } for item in combo.items.all()
        ],
        'is_auto_apply': combo.is_auto_apply,
        'is_active': combo.is_active,
        'max_apply_quantity': combo.max_apply_quantity,
        'start_at': to_local(combo.start_at),
        'end_at': to_local(combo.end_at),
        'created_at': to_local(combo.created_at),
        'updated_at': to_local(combo.updated_at)
        
        
    }
    
## for all user

class ListComboView(APIView):
    def get(self,request):
        combos = (
            Combo.objects.order_by('updated_at').prefetch_related('items__product')
            
        )
        combos_data = [build_combo_data(combo) for combo in combos]
        return Response({"combos": combos_data}, status=200)


## only admin


def recalc_combo_price(combo):
    total = (
        ComboItem.objects
        .filter(combo=combo)
        .aggregate(
            total=Sum(F("product__price") * F("quantity"))
        )["total"] or Decimal("0")
    )

    combo.actual_combo_price = total
    combo.combo_price = (total * Decimal("0.9")).quantize(Decimal("1"))
    combo.save(update_fields=["actual_combo_price", "combo_price"])

class AddProductToCombo(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, combo_id):
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity", 1)

        # Validate input
        if not product_id:
            return Response(
                {"error": "product_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            return Response(
                {"error": "quantity must be a positive integer"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get combo from URL
        try:
            combo = Combo.objects.get(id=combo_id)
        except Combo.DoesNotExist:
            return Response(
                {"error": "Combo not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create or update combo item
        combo_item, created = ComboItem.objects.get_or_create(
            combo=combo,
            product=product,
            defaults={"quantity": quantity}
        )

        if not created:
            combo_item.quantity += quantity
            combo_item.save()
            
        recalc_combo_price(combo)

        return Response(
            {
                "message": "Product added to combo successfully",
                "combo_id": combo.id,
                "product_id": product.id,
                "quantity": combo_item.quantity,
                "combos_data": build_combo_data(combo)
            },
            status=status.HTTP_201_CREATED
        )

class ResetComboTime(APIView):
    permission_classes = [IsAdminUser]
    
    def patch(self, request, combo_id):
        new_start_at = request.data.get("new_start_at")
        new_end_at = request.data.get("new_end_at")

        if not new_start_at and not new_end_at:
            return Response(
                {"error": "new_start_at or new_end_at is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        now = timezone.now()

        # Get combo
        try:
            combo = Combo.objects.get(id=combo_id)
        except Combo.DoesNotExist:
            return Response(
                {"error": "Combo not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        def parse_and_make_aware(value):
            dt = parse_datetime(value)
            if not dt:
                return None
            if is_naive(dt):
                dt = make_aware(dt)
            return dt

        # Parse datetime
        start_at = parse_and_make_aware(new_start_at) if new_start_at else combo.start_at
        end_at = parse_and_make_aware(new_end_at) if new_end_at else combo.end_at

        if new_start_at and not start_at:
            return Response(
                {"error": "Invalid new_start_at format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_end_at and not end_at:
            return Response(
                {"error": "Invalid new_end_at format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if new_start_at and start_at < now:
            return Response(
                {"error": "new_start_at must be greater than or equal to current time"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        if start_at and end_at and start_at >= end_at:
            return Response(
                {"error": "start_at must be earlier than end_at"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update fields
        combo.start_at = start_at
        combo.end_at = end_at
        combo.save(update_fields=["start_at", "end_at", "updated_at"])

        return Response(
            {
                "message": "Combo time updated successfully",
                "combo": build_combo_data(combo)
            },
            status=status.HTTP_200_OK
        )
        

class SetMaxQuantityView(APIView):
    permission_classes = [IsAdminUser]
    
    def put(self, request, combo_id):
        new_max_apply_quantity = request.data.get("new_max_apply_quantity")
        
        if not new_max_apply_quantity: 
            return Response(
                {"error": "The max apply quantity is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            value = int(new_max_apply_quantity)
        except (TypeError, ValueError):
            return Response(
                {"error": "max_apply_quantity must be an integer"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if value <= 0:
            return Response(
                {"error": "The max apply quantity must be greater than 0"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            combo = Combo.objects.get(id=combo_id)
        except Combo.DoesNotExist:
            return Response(
                {"error": "Combo not found"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        combo.max_apply_quantity = new_max_apply_quantity
        combo.save()

        return Response(
            {
                "message": "Max apply quantity updated successfully",
                "combo": build_combo_data(combo)
            },
            status=status.HTTP_200_OK
        )