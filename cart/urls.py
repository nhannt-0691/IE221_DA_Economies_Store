from django.urls import path
from .views import (
    AddCartItem,
    ViewCartItems,
    DeleteCartItems,
    UpdateQuantityCartItems,
)

urlpatterns = [
    path('', ViewCartItems.as_view(), name='view_cart_items'),
    path('add/', AddCartItem.as_view(), name='add_cart_item'),
    path('<int:item_id>/delete/', DeleteCartItems.as_view(), name='delete_cart_item'),
    path('<int:item_id>/update_quantity/', UpdateQuantityCartItems.as_view(), name='update_cart_item'),
]
