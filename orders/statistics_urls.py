from django.urls import path
from .views import RevenueStatisticsView

urlpatterns = [
    path('revenue/', RevenueStatisticsView.as_view(), name='revenue_statistics'),
]
