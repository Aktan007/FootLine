from django import forms
from .models import Product, Order, OrderItem, Category, Manufacturer, Supplier, DeliveryPoint
from PIL import Image


class ProductForm(forms.ModelForm):
    """Форма для добавления/редактирования товара"""
    
    class Meta:
        model = Product
        fields = ['article', 'name', 'unit', 'price', 'supplier', 'manufacturer', 
                  'category', 'discount', 'quantity', 'description', 'photo']
        widgets = {
            'article': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Артикул'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Наименование'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Единица измерения'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Цена', 'step': '0.01'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'manufacturer': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Скидка %', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Кол-во на складе', 'step': '1'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Описание', 'rows': 4}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            # Проверяем размер файла
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Размер фото не должен превышать 5МБ')
            
            # Проверяем расширение
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
            ext = photo.name.split('.')[-1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError('Поддерживаются только форматы: JPG, PNG, GIF')
        
        return photo
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Оптимизируем размер фото
        if self.cleaned_data.get('photo'):
            photo = self.cleaned_data['photo']
            img = Image.open(photo)
            img.thumbnail((300, 200), Image.Resampling.LANCZOS)
            
            # Сохраняем оптимизированное изображение
            img_format = 'PNG' if photo.name.lower().endswith('.png') else 'JPEG'
            img.save(photo.file, format=img_format, optimize=True)
            photo.file.seek(0)
        
        if commit:
            instance.save()
        
        return instance


class OrderForm(forms.ModelForm):
    """Форма для добавления/редактирования заказа"""
    
    class Meta:
        model = Order
        fields = ['order_number', 'order_date', 'delivery_date', 'delivery_point', 
                  'customer_name', 'code', 'status']
        widgets = {
            'order_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Номер заказа'}),
            'order_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'delivery_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'delivery_point': forms.Select(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ФИО клиента'}),
            'code': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Код получения'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class OrderItemForm(forms.ModelForm):
    """Форма для добавления товара в заказ"""
    
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Кол-во', 'step': '1'}),
        }
