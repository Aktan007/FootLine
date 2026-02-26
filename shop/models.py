from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    """Категория товара"""
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Категории"


class Manufacturer(models.Model):
    """Производитель товара"""
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Производители"


class Supplier(models.Model):
    """Поставщик товара"""
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Поставщики"


class Product(models.Model):
    """Товар"""
    article = models.CharField(max_length=50, unique=True, primary_key=True)
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=20, default='шт.')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='products/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.article} - {self.name}"
    
    def get_final_price(self):
        """Получить цену с учетом скидки"""
        if self.discount > 0:
            discount_amount = self.price * (self.discount / 100)
            return round(self.price - discount_amount, 2)
        return self.price
    
    class Meta:
        verbose_name_plural = "Товары"


class UserProfile(models.Model):
    """Профиль пользователя"""
    USER_ROLES = [
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
        ('client', 'Авторизованный клиент'),
        ('guest', 'Гость'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=USER_ROLES)
    full_name = models.CharField(max_length=200)
    
    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"
    
    class Meta:
        verbose_name_plural = "Профили пользователей"


class DeliveryPoint(models.Model):
    """Пункт выдачи товара"""
    address = models.CharField(max_length=500)
    
    def __str__(self):
        return self.address
    
    class Meta:
        verbose_name_plural = "Пункты выдачи"


class Order(models.Model):
    """Заказ"""
    STATUS_CHOICES = [
        ('pending', 'В обработке'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]
    
    order_number = models.IntegerField(unique=True)
    products = models.ManyToManyField(Product, through='OrderItem')
    order_date = models.DateTimeField()
    delivery_date = models.DateTimeField()
    delivery_point = models.ForeignKey(DeliveryPoint, on_delete=models.SET_NULL, null=True)
    customer_name = models.CharField(max_length=200)
    code = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"Заказ #{self.order_number}"
    
    class Meta:
        verbose_name_plural = "Заказы"


class OrderItem(models.Model):
    """Товар в заказе"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    def __str__(self):
        return f"{self.order} - {self.product.name}"
    
    class Meta:
        verbose_name_plural = "Товары в заказах"
        unique_together = ('order', 'product')
