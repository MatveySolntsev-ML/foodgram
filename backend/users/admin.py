from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Subscription, User


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    list_display = ("id", "username", "email", "first_name", "last_name")
    search_fields = ("username", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("Аватар", {"fields": ("avatar",)}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author")
    search_fields = ("user__username", "author__username")
