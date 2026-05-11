from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# 1. Бренд (Dior, Chanel и т.д.)
class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name="Бренд")
    
    def __str__(self):
        return self.name

# 2. Тип аромата (Цветочные, Восточные и т.д.)
class ScentType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Тип аромата")
    
    def __str__(self):
        return self.name

# 3. Основная карточка товара (Общая инфо об аромате)
class Product(models.Model):
    GENDER_CHOICES = [
        ('men', 'Для мужчин'),
        ('women', 'Для женщин'),
        ('unisex', 'Унисекс'),
    ]

    name = models.CharField(max_length=200, verbose_name="Название")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name="Бренд")
    scent_type = models.ForeignKey(ScentType, on_delete=models.CASCADE, verbose_name="Тип аромата")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unisex', verbose_name="Для кого")
    description = models.TextField(verbose_name="Описание")
    main_image = models.ImageField(upload_to='products/', verbose_name="Основное фото")

    def __str__(self): 
        return f"{self.brand.name} - {self.name} ({self.get_gender_display()})"

# 4. Варианты объема (30мл, 50мл, 100мл) — здесь цена и наличие
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="Товар")
    volume = models.IntegerField(verbose_name="Объем (мл)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    stock = models.PositiveIntegerField(default=0, verbose_name="Остаток на складе")

    def __str__(self):
        return f"{self.product.name} - {self.volume} мл"

# 5. Корзина пользователя
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, verbose_name="Товар (объем)")
    quantity = models.PositiveIntegerField(default=1)

# 6. Заказы
class Order(models.Model):
    STATUS_CHOICES = [
        ('processing', 'В обработке'),
        ('warehouse', 'На складе'),
        ('pickup', 'В пункте выдачи'),
        ('delivered', 'Доставлено'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing', verbose_name="Статус")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Итого")
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, verbose_name="Товар (объем)")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    def __str__(self):
        return f"{self.product_variant} ({self.quantity} шт.)"

# 7. Отзывы
class Comment(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(verbose_name="Текст отзыва")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], 
        verbose_name="Оценка"
    )