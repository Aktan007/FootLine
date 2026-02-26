from django.contrib import admin
from .models import (
    Category, Manufacturer, Supplier, Product,
    UserProfile, DeliveryPoint, Order, OrderItem
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('article', 'name', 'price', 'quantity', 'discount', 'category')
    list_filter = ('category', 'supplier', 'manufacturer')
    search_fields = ('article', 'name', 'description')
    readonly_fields = ('article',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'role', 'user')
    list_filter = ('role',)
    search_fields = ('full_name', 'user__username')


@admin.register(DeliveryPoint)
class DeliveryPointAdmin(admin.ModelAdmin):
    list_display = ('address',)
    search_fields = ('address',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'order_date', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('order_number', 'customer_name')
    inlines = [OrderItemInline]
    readonly_fields = ('order_number',)
