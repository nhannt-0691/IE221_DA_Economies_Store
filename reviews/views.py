from itertools import product
from django.shortcuts import render
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from products.models import Product
from orders.models import Order
from django.utils import timezone
import reviews
from reviews.models import Reviews

def build_review_data(review):
    def to_local(dt):
        return timezone.localtime(dt).strftime("%Y-%m-%d %H:%M:%S") if dt else None
    return {
        "id": review.id,
        "user": review.user.id,
        "order": review.order.id,
        "product": review.product.id,
        "star": review.star,
        "comment": review.comment,
        "created_at": to_local(review.created_at),
        "updated_at": to_local(review.updated_at),
    }
    
    
# Create your views here.
class GetProductReviewsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        reviews = Reviews.objects.filter(user=user)
        reviews_data = [build_review_data(review) for review in reviews]
        
        return Response(
            {"reviews": reviews_data},
            status=status.HTTP_200_OK
        )
        
class CreateProductReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        order_id = request.data.get("order_id")
        product_id = request.data.get("product_id")
        star = request.data.get("star", 5)
        comment = request.data.get("comment", "")

        if not order_id or not product_id:
            return Response(
                {"error": "order_id and product_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not (1 <= int(star) <= 5):
            return Response(
                {"error": "Star must be between 1 and 5"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Lấy order
        try:
            order = Order.objects.get(
                id=order_id,
                user=user,
                order_status=Order.COMPLETED
            )
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found, not completed, or not belong to user"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Lấy product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Không cho review trùng
        if Reviews.objects.filter(
            user=user,
            order=order,
            product=product
        ).exists():
            return Response(
                {"error": "You have already reviewed this product"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Tạo review
        review = Reviews.objects.create(
            user=user,
            order=order,
            product=product,
            star=star,
            comment=comment
        )

        return Response(
            {
                "message": "Review created successfully",
                "review": build_review_data(review)
            },
            status=status.HTTP_201_CREATED
        )

        
class GetAllProductReviewsView(APIView):
    
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        reviews = Reviews.objects.filter(product=product)
        reviews_data = [build_review_data(review) for review in reviews]
        
        return Response(
            {"reviews": reviews_data},
            status=status.HTTP_200_OK
        )
        
class UpdateProductReviewsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, review_id):
        user = request.user
        star = request.data.get("star")
        comment = request.data.get("comment")
        
        try:
            review = Reviews.objects.get(id=review_id, user=user)
        except Reviews.DoesNotExist:
            return Response(
                {"error": "Review not found or does not belong to user"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if star and (1 <= int(star) <= 5):
            review.star = star
        if comment is not None:
            review.comment = comment
            
        review.save()
        
        return Response(
            {"message": "Review updated successfully", "review": build_review_data(review)},
            status=status.HTTP_200_OK
        )
        
class DeleteProductReviewView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, review_id):
        user = request.user
        
        try:
            review = Reviews.objects.get(id=review_id, user=user)
        except Reviews.DoesNotExist:
            return Response(
                {"error": "Review not found or does not belong to user"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        review.delete()
        
        return Response(
            {"message": "Review deleted successfully"},
            status=status.HTTP_200_OK
        )