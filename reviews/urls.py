from django.urls import path
from .views import (
    CreateProductReviewView,
    GetProductReviewsView,
    UpdateProductReviewsView,
    DeleteProductReviewView,
    GetAllProductReviewsView
)

urlpatterns = [
    path('', GetProductReviewsView.as_view(), name='get_product_reviews'),
    path('add/', CreateProductReviewView.as_view(), name='create_review'),
    path('<int:review_id>/update/', UpdateProductReviewsView.as_view(), name='update_review'),
    path('<int:product_id>/', GetAllProductReviewsView.as_view(), name='reviews_home'),
    path('<int:review_id>/delete/', DeleteProductReviewView.as_view(), name='delete_review'),
    
    
]