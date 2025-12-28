from __future__ import annotations
# Create your views here.

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from cart.models import Cart, CartItem
from products.models import Product

class AddCartItem(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
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

        # Get product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        cart, _ = Cart.objects.get_or_create(user=user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": 0}
        )

        new_quantity = cart_item.quantity + quantity

        # Check stock with total quantity
        if not product.is_in_stock:
            return Response(
                {"error": "Requested quantity exceeds available stock"},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = new_quantity
        cart_item.save()

        return Response(
            {
                "message": "Item added to cart successfully",
                "product_id": product.id,
                "quantity": cart_item.quantity
            },
            status=status.HTTP_200_OK
        )

class ViewCartItems(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            return Response({"items": []}, status=status.HTTP_200_OK)

        items = cart.items.all().values('id','product__id', 'product__name', 'quantity', 'product__price')
        return Response({"items": list(items)}, status=status.HTTP_200_OK)
    
class DeleteCartItems(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        user = request.user
        try:
            cart = Cart.objects.get(user=user)
            cart_item = CartItem.objects.get(cart=cart, id=item_id)
            cart_item.delete()
            return Response({"message": "Item deleted from cart successfully."}, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)
        

class UpdateQuantityCartItems(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        user = request.user
        new_quantity = request.data.get('new_quantity')
        
        
        try:
            new_quantity = int(new_quantity)
            if new_quantity < 1:
                return Response({"error": "Quantity must be more than 0."}, status=status.HTTP_400_BAD_REQUEST)
        
            cart = Cart.objects.get(user=user)
            cart_item = CartItem.objects.get(cart=cart, id=item_id)
            cart_item.quantity = new_quantity
            cart_item.save()
            return Response({"message": "Cart item quantity updated successfully."}, status=status.HTTP_200_OK)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found."}, status=status.HTTP_404_NOT_FOUND)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)
        
        