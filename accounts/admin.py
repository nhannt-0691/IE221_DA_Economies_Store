# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Extra info", {"fields": ("phone", "address", "updated_at")}),
    )

    readonly_fields = ("updated_at",)

    list_display = (
        "username", "email", "first_name", "last_name", "phone", "address",
        "is_staff", "is_active", "date_joined", "last_login", "updated_at"
    )
    search_fields = ("username", "email", "phone", "address")
    list_filter = ("is_staff", "is_active", "date_joined", "last_login", "updated_at")