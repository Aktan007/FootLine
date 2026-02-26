import csv
from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from shop.models import (
    Category, Manufacturer, Supplier, Product,
    DeliveryPoint, UserProfile, Order, OrderItem
)


class Command(BaseCommand):
    help = 'Import data from CSV files in import/ folder'

    def handle(self, *args, **options):
        base_path = settings.BASE_DIR / 'import'
        
        self.stdout.write('Очистка базы данных...')
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Product.objects.all().delete()
        DeliveryPoint.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Category.objects.all().delete()
        Manufacturer.objects.all().delete()
        Supplier.objects.all().delete()
        
        self.stdout.write('\n1. Импорт товаров...')
        self.import_products(base_path / 'Tovar.csv')
        
        self.stdout.write('\n2. Импорт пунктов выдачи...')
        self.import_delivery_points(base_path / 'Пункты выдачи_import.csv')
        
        self.stdout.write('\n3. Импорт пользователей...')
        self.import_users(base_path / 'user_import.csv')
        
        self.stdout.write('\n4. Импорт заказов...')
        self.import_orders(base_path / 'Заказ_import.csv')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Импорт завершен!'))

    def import_products(self, file_path):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                if not row.get('Артикул') or not row.get('Цена'):
                    continue
                
                category, _ = Category.objects.get_or_create(
                    name=row['Категория товара']
                )
                
                manufacturer, _ = Manufacturer.objects.get_or_create(
                    name=row['Производитель']
                )
                
                supplier, _ = Supplier.objects.get_or_create(
                    name=row['Поставщик']
                )
                
                Product.objects.create(
                    article=row['Артикул'],
                    name=row['Наименование товара'],
                    unit=row['Единица измерения'] or 'шт.',
                    price=float(row['Цена']),
                    supplier=supplier,
                    manufacturer=manufacturer,
                    category=category,
                    discount=float(row['Действующая скидка']) if row.get('Действующая скидка') else 0,
                    quantity=int(row['Кол-во на складе']) if row.get('Кол-во на складе') else 0,
                    description=row.get('Описание товара', ''),
                    photo=f"products/{row['Фото']}" if row.get('Фото') else None
                )
                count += 1
        
        self.stdout.write(f'  Импортировано товаров: {count}')
        self.stdout.write(f'  Категорий: {Category.objects.count()}')
        self.stdout.write(f'  Производителей: {Manufacturer.objects.count()}')
        self.stdout.write(f'  Поставщиков: {Supplier.objects.count()}')

    def import_delivery_points(self, file_path):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            count = 0
            
            for row in reader:
                if row and row[0]:
                    DeliveryPoint.objects.create(address=row[0])
                    count += 1
        
        self.stdout.write(f'  Импортировано пунктов выдачи: {count}')

    def import_users(self, file_path):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            
            role_map = {
                'Администратор': 'admin',
                'Менеджер': 'manager',
                'Авторизованный клиент': 'client',
                'Авторизированный клиент': 'client',
                'Гость': 'guest',
            }
            
            for row in reader:
                if not row.get('Логин') or not row.get('Пароль'):
                    continue
                user = User.objects.create_user(
                    username=row['Логин'],
                    email=row['Логин'],
                    password=row['Пароль']
                )
                
                role = role_map.get(row['Роль сотрудника'], 'guest')
                if role == 'admin':
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()
                
                UserProfile.objects.create(
                    user=user,
                    role=role,
                    full_name=row['ФИО']
                )
                count += 1
        
        self.stdout.write(f'  Импортировано пользователей: {count}')

    def import_orders(self, file_path):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            
            status_map = {
                'Новый': 'pending',
                'В обработке': 'pending',
                'Завершен': 'completed',
                'Отменен': 'cancelled',
            }
            
            for row in reader:
                if not row.get('Номер заказа') or not row.get('Дата заказа'):
                    continue
                
                try:
                    delivery_point_idx = int(row['Адрес пункта выдачи']) - 1
                    delivery_point = DeliveryPoint.objects.all()[delivery_point_idx]
                except (IndexError, ValueError, TypeError):
                    delivery_point = None
                
                try:
                    order_date = datetime.strptime(row['Дата заказа'], '%Y-%m-%d %H:%M:%S')
                    delivery_date = datetime.strptime(row['Дата доставки'], '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    continue
                
                order = Order.objects.create(
                    order_number=int(row['Номер заказа']),
                    order_date=order_date,
                    delivery_date=delivery_date,
                    delivery_point=delivery_point,
                    customer_name=row.get('ФИО авторизированного клиента', ''),
                    code=int(row.get('Код для получения', 0) or 0),
                    status=status_map.get(row.get('Статус заказа', ''), 'pending')
                )
                
                articles_str = row.get('Артикул заказа', '')
                if not articles_str:
                    continue
                    
                parts = [p.strip() for p in articles_str.split(',')]
                
                for i in range(0, len(parts), 2):
                    if i + 1 < len(parts):
                        article = parts[i]
                        try:
                            quantity = int(parts[i + 1])
                        except ValueError:
                            continue
                        
                        try:
                            product = Product.objects.get(article=article)
                            OrderItem.objects.create(
                                order=order,
                                product=product,
                                quantity=quantity
                            )
                        except Product.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(f'  Товар {article} не найден')
                            )
                
                count += 1
        
        self.stdout.write(f'  Импортировано заказов: {count}')
        self.stdout.write(f'  Позиций в заказах: {OrderItem.objects.count()}')
