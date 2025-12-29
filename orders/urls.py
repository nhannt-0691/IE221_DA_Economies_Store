from django.urls import path
from .views import (
    CreateOrderView,
    OrderListView,
    OrderDetailView,
    DeleteOrderView,
    UpdateInfoStatusView,
    AdminOrderListView,
    AdminUpdateOrderStatusView,
)

urlpatterns = [
    path('', OrderListView.as_view(), name='order_list'),
    path('create/', CreateOrderView.as_view(), name='create_order'),
    path('<int:order_id>/', OrderDetailView.as_view(), name='order_detail'),
    path('<int:order_id>/delete/', DeleteOrderView.as_view(), name='delete_order'),
    path('<int:order_id>/update/', UpdateInfoStatusView.as_view(), name='update_order'),

    # admin
    path('admin/', AdminOrderListView.as_view(), name='admin_order_list'),
    path('admin/<int:order_id>/update_status/', AdminUpdateOrderStatusView.as_view(), name='update_order_status'),
]
