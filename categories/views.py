from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Category

class CategoryListView(APIView):
    def get(self, request):
        categories = Category.objects.all().values('id', 'name', 'description', 'created_at', 'updated_at')
        return Response(categories, status= status.HTTP_200_OK)