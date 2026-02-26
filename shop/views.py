from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import (
    Product, UserProfile, Order, OrderItem, DeliveryPoint,
    Category, Manufacturer, Supplier
)
from .forms import ProductForm, OrderForm
import json


def login_view(request):
    """Представление для входа пользователя"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('shop:dashboard')
        else:
            messages.error(request, 'Неверный логин или пароль')
    
    return render(request, 'shop/login.html')


def products_list_guest(request):
    """Представление для просмотра товаров гостем (без фильтрации)"""
    products = Product.objects.all().order_by('article')
    
    context = {
        'products': products,
        'user_role': 'guest',
    }
    
    return render(request, 'shop/products_list.html', context)


@login_required(login_url='shop:login')
def dashboard(request):
    """Главный экран после входа"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = None
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'shop/dashboard.html', context)


@login_required(login_url='shop:login')
def products_list(request):
    """Представление для просмотра товаров (с фильтрацией и поиском для менеджера и админа)"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect('shop:login')
    
    # Проверяем роль пользователя
    if profile.role == 'guest':
        # Гости видят все товары без фильтрации
        products = Product.objects.all().order_by('article')
        has_filters = False
    elif profile.role == 'client':
        # Клиенты видят все товары без фильтрации
        products = Product.objects.all().order_by('article')
        has_filters = False
    elif profile.role in ['manager', 'admin']:
        # Менеджер и администратор имеют доступ к фильтрации
        products = Product.objects.all()
        has_filters = True
        
        # Поиск по всем текстовым полям
        search_query = request.GET.get('search', '').strip()
        if search_query:
            products = products.filter(
                Q(article__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(manufacturer__name__icontains=search_query) |
                Q(supplier__name__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        # Фильтр по поставщику
        supplier_id = request.GET.get('supplier', '').strip()
        if supplier_id:
            products = products.filter(supplier_id=supplier_id)
        
        # Сортировка по количеству на складе
        sort_qty = request.GET.get('sort_quantity', '')
        if sort_qty == 'asc':
            products = products.order_by('quantity')
        elif sort_qty == 'desc':
            products = products.order_by('-quantity')
        else:
            products = products.order_by('article')
        
        products = products.select_related('category', 'manufacturer', 'supplier')
    
    # Получаем список поставщиков для фильтра
    suppliers = Supplier.objects.all().order_by('name')
    
    context = {
        'products': products,
        'user_role': profile.role,
        'profile': profile,
        'has_filters': has_filters,
        'suppliers': suppliers,
        'search_query': request.GET.get('search', ''),
        'selected_supplier': request.GET.get('supplier', ''),
        'sort_quantity': request.GET.get('sort_quantity', ''),
    }
    
    return render(request, 'shop/products_list.html', context)


@login_required(login_url='shop:login')
def add_product(request):
    """Добавление нового товара (только для администратора)"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect('shop:login')
    
    if profile.role != 'admin':
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('shop:products_list')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Товар "{product.name}" успешно добавлен')
            return redirect('shop:products_list')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'profile': profile,
        'is_edit': False,
    }
    
    return render(request, 'shop/product_form.html', context)


@login_required(login_url='shop:login')
def edit_product(request, article):
    """Редактирование товара (только для администратора)"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect('shop:login')
    
    if profile.role != 'admin':
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('shop:products_list')
    
    product = get_object_or_404(Product, article=article)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Товар "{product.name}" успешно обновлен')
            return redirect('shop:products_list')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'profile': profile,
        'is_edit': True,
    }
    
    return render(request, 'shop/product_form.html', context)


@login_required(login_url='shop:login')
def delete_product(request, article):
    """Удаление товара (только для администратора)"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect('shop:login')
    
    if profile.role != 'admin':
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('shop:products_list')
    
    product = get_object_or_404(Product, article=article)
    
    # Проверяем, есть ли товар в заказах
    if OrderItem.objects.filter(product=product).exists():
        messages.error(request, f'Товар "{product.name}" присутствует в заказах и не может быть удален')
        return redirect('shop:products_list')
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Товар "{product_name}" успешно удален')
        return redirect('shop:products_list')
    
    context = {
        'product': product,
        'profile': profile,
    }
    
    return render(request, 'shop/product_confirm_delete.html', context)


@login_required(login_url='shop:login')
def orders_list(request):
    """Представление для просмотра заказов"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect('shop:login')
    
    if profile.role not in ['manager', 'admin']:
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('shop:dashboard')
    
    orders = Order.objects.all().order_by('-order_date')
    
    context = {
        'orders': orders,
        'profile': profile,
    }
    
    return render(request, 'shop/orders_list.html', context)


@login_required(login_url='shop:login')
def add_order(request):
    """Добавление нового заказа (только для администратора)"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect('shop:login')
    
    if profile.role != 'admin':
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('shop:orders_list')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(request, f'Заказ #{order.order_number} успешно добавлен')
            return redirect('shop:orders_list')
    else:
        form = OrderForm()
    
    context = {
        'form': form,
        'profile': profile,
        'is_edit': False,
    }
    
    return render(request, 'shop/order_form.html', context)


@login_required(login_url='shop:login')
def edit_order(request, order_id):
    """Редактирование заказа (только для администратора)"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect('shop:login')
    
    if profile.role != 'admin':
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('shop:orders_list')
    
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Заказ #{order.order_number} успешно обновлен')
            return redirect('shop:orders_list')
    else:
        form = OrderForm(instance=order)
    
    context = {
        'form': form,
        'order': order,
        'profile': profile,
        'is_edit': True,
    }
    
    return render(request, 'shop/order_form.html', context)


@login_required(login_url='shop:login')
def delete_order(request, order_id):
    """Удаление заказа (только для администратора)"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return redirect('shop:login')
    
    if profile.role != 'admin':
        messages.error(request, 'У вас нет доступа к этой странице')
        return redirect('shop:orders_list')
    
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        order_number = order.order_number
        order.delete()
        messages.success(request, f'Заказ #{order_number} успешно удален')
        return redirect('shop:orders_list')
    
    context = {
        'order': order,
        'profile': profile,
    }
    
    return render(request, 'shop/order_confirm_delete.html', context)


def logout_view(request):
    """Выход пользователя"""
    logout(request)
    return redirect('shop:login')
