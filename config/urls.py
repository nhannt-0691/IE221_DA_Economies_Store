"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from accounts.views import ChangePasswordView, RegisterAPI, LoginAPIView, UpdateProfileView, UserListAPIView, ChangeAccountStatusAPIView, GetProfileView
from cart.views import AddCartItem, DeleteCartItems, UpdateQuantityCartItems, ViewCartItems
from categories.views import CategoryListView
from products.views import CreateProductView, DeleteProductView, ProductDetailView, ProductListView, UpdateProductView


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API accounts
    path('api/accounts/register/', RegisterAPI.as_view(), name='register'),

    # JWT auth
    path('api/auth/login/', LoginAPIView.as_view(), name='token_obtain_pair'),
    
    # User profile
    path('api/accounts/profile/', GetProfileView.as_view(), name='get_profile'),
    path('api/accounts/update_profile/', UpdateProfileView.as_view(), name='update_profile'),
    path('api/accounts/change_password/', ChangePasswordView.as_view(), name='change_password'),
    
    #ADMIN
    #User list
    path('api/users/user_list/', UserListAPIView.as_view(), name='user_list'),
    
    #banned user
    path('api/users/is_active/user_id=<int:user_id>', ChangeAccountStatusAPIView.as_view(), name='change_user_status'),
    
    #categories
    path('api/categories/category_list', CategoryListView.as_view(), name='category_list'),
    
    #products
    path('api/products/product_list', ProductListView.as_view(), name='product_list'),
    path('api/products/product_detail/product_id=<int:product_id>', ProductDetailView.as_view(), name='product_detail'),
    path('api/products/create_product/', CreateProductView.as_view(), name='create_product'),
    path('api/products/update_product/product_id=<int:product_id>', UpdateProductView.as_view(), name='update_product'),
    path('api/products/delete_product/product_id=<int:product_id>', DeleteProductView.as_view(), name='delete_product'),
    
    #cart 
    path('api/cart/add_item/', AddCartItem.as_view(), name='add_cart_item'),
    path('api/cart/view_items/', ViewCartItems.as_view(), name='view_cart_items'),
    path('api/cart/delete_item/item_id=<int:item_id>', DeleteCartItems.as_view(), name='delete_cart_item'),
    path('api/cart/update_quantity/item_id=<int:item_id>', UpdateQuantityCartItems.as_view(), name='update_cart_item'),
]