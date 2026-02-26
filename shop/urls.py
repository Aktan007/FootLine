from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('guest/', views.products_list_guest, name='products_guest'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('products/', views.products_list, name='products_list'),
    path('products/<str:article>/edit/', views.edit_product, name='edit_product'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<str:article>/delete/', views.delete_product, name='delete_product'),
    path('orders/', views.orders_list, name='orders_list'),
    path('orders/<int:order_id>/edit/', views.edit_order, name='edit_order'),
    path('orders/add/', views.add_order, name='add_order'),
    path('orders/<int:order_id>/delete/', views.delete_order, name='delete_order'),
]
