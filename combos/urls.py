from django.urls import path
from .views import (
    ListComboView,
    AddProductToCombo,
    ResetComboTime,
    SetMaxQuantityView
)

urlpatterns = [
    path('', ListComboView.as_view(), name='combo_list'),
    path('<int:combo_id>/add', AddProductToCombo.as_view(), name='add_product_to_combo'),
    path('<int:combo_id>/reset_time', ResetComboTime.as_view(), name='reset_time'),
    path('<int:combo_id>/update_max_apply_quantity', SetMaxQuantityView.as_view(), name='reset_max_quantity')
  
]
