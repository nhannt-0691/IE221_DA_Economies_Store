from __future__ import annotations
from time import timezone
from urllib import request
from django.shortcuts import render
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from rest_framework.permissions import IsAdminUser
from decimal import Decimal, InvalidOperation

class ProductListView(APIView):
    def get(self, request):
        products = Product.objects.filter(is_deleted=False)
        products = Product.objects.all().values('id', 'name', 'description', 'price','image_url', 'category_id','specification', 'brand', 'is_in_stock', 'created_at', 'updated_at')

        #Brand
        brand_param = request.query_params.get('brand')
        if brand_param:
            brand_list = [b.strip() for b in brand_param.split(',') if b.strip()]
            products = products.filter(brand__in=brand_list)
        #Category
        category_param = request.query_params.get('category')
        if category_param:
            category_list = [c.strip() for c in category_param.split(',') if c.strip()]
            products = products.filter(category__name__in=category_list).distinct()
        #Price
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')

        try:
            if min_price:
                products = products.filter(price__gte=Decimal(min_price))
            if max_price:
                products = products.filter(price__lte=Decimal(max_price))
        except InvalidOperation:
            return Response(
                {"error": "Invalid price format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        products = products.values(
            'id', 'name', 'description', 'price',
            'image_url', 'category_id',
            'specification', 'brand',
            'is_in_stock', 'created_at', 'updated_at'
        )

        return Response(products, status= status.HTTP_200_OK)

class ProductDetailView(APIView):
    def get(self, request, product_id):
        try:
            product = (
                Product.objects
                .filter(is_deleted=False)
                .values(
                    'id', 'name', 'description', 'price',
                    'image_url', 'category_id',
                    'specification', 'brand',
                    'is_in_stock', 'created_at', 'updated_at'
                )
                .get(id=product_id)
            )
            return Response(product, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

def build_product_data(product):
    def to_local(dt):
        return timezone.localtime(dt).strftime("%Y-%m-%d %H:%M:%S") if dt else None
    return {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': str(product.price),
        'image_url': product.image_url,
        'category_id': product.category_id, 
        'specification': product.specification,
        'brand': product.brand,
        'is_in_stock': product.is_in_stock,
        'created_at': to_local(product.created_at),
        'updated_at': to_local(product.updated_at),
    }
    
class CreateProductView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        data = request.data
        required_fields = ['name', 'price', 'category_id', 'brand' ]
        missing_fields = [f for f in required_fields if not data.get(f)]
        if missing_fields:
            return Response(
                {"error": "Missing required fields", "fields": missing_fields},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            price = Decimal(data['price'])
            if price <= 0:
                return Response({"error": "Price must be greater than 0"}, status=400)
        except (InvalidOperation, TypeError):
            return Response({"error": "Price must be a number"}, status=400)

        is_in_stock = True
        if 'is_in_stock' in data:
            val = str(data['is_in_stock']).lower()
            is_in_stock = val in ['true', '1', 'yes']

        product = Product.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            price=price,
            image_url=data.get('image_url', ''),
            category_id=data['category_id'],
            specification=data.get('specification', {}),
            brand=data['brand'],
            is_in_stock=is_in_stock
        )

        return Response(
            {
                "message": "Product created successfully.",
                "product": build_product_data(product)
            },
            status=status.HTTP_201_CREATED
        )

class UpdateProductView(APIView):
    permission_classes = [IsAdminUser]

    allow_field = ['description', 'price', 'image_url', 'is_in_stock', 'specification']

    def patch(self, request, product_id):
        data = request.data

        invalid_fields = [field for field in data if field not in self.allow_field]
        if invalid_fields:
            return Response(
                {"error": "These fields are not allowed to update", "fields": invalid_fields},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        for field in self.allow_field:
            if field in data:
                value = data[field]

                if field == 'price':
                    try:
                        price = Decimal(value)
                        if price <= 0:
                            return Response({"error": "Price must be greater than 0"}, status=400)
                        setattr(product, field, price)
                    except (InvalidOperation, TypeError):
                        return Response({"error": "Price must be a number"}, status=400)

                elif field == 'is_in_stock':
                    setattr(product, field, str(value).lower() in ['true', '1', 'yes'])

                else:
                    setattr(product, field, value)

        product.save()

        return Response({
            "message": "Product updated successfully",
            "product": build_product_data(product)
        }, status=status.HTTP_200_OK)


class DeleteProductView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id, is_deleted=False)
            product.is_deleted = True
            product.deleted_at = timezone.now()
            product.save(update_fields=['is_deleted', 'deleted_at'])

            return Response(
                {"message": "Product soft deleted successfully."},
                status=status.HTTP_200_OK
            )

        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class RestoreProductView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id, is_deleted=True)

            product.is_deleted = False
            product.deleted_at = None
            product.save(update_fields=['is_deleted', 'deleted_at'])

            return Response(
                {
                    "message": "Product restored successfully.",
                    "product": build_product_data(product)
                },
                status=status.HTTP_200_OK
            )

        except Product.DoesNotExist:
            return Response(
                {"error": "Deleted product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

class DeletedProductListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        products = Product.objects.filter(is_deleted=True)

        data = [build_product_data(p) for p in products]

        return Response(
            {"deleted_products": data},
            status=status.HTTP_200_OK
        )