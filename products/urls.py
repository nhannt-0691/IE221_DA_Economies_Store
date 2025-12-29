from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    CreateProductView,
    UpdateProductView,
    DeleteProductView,
    DeletedProductListView,
    RestoreProductView,
)

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('<int:product_id>/', ProductDetailView.as_view(), name='product_detail'),

    path('create/', CreateProductView.as_view(), name='create_product'),
    path('<int:product_id>/update/', UpdateProductView.as_view(), name='update_product'),
    path('<int:product_id>/delete/', DeleteProductView.as_view(), name='delete_product'),

    path('deleted/', DeletedProductListView.as_view(), name='list_deleted_products'),
    path('<int:product_id>/restore/', RestoreProductView.as_view(), name='restore_product'),
]
