import uuid
from decimal import Decimal

from pydantic import ValidationError

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify


class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Color"
        verbose_name_plural = "Colores"


class Size(models.Model):
    CLOTHING = 'clothing'
    SHOE = 'shoe'
    SIZE_TYPES = [
        (CLOTHING, 'Ropa'),
        (SHOE, 'Calzado'),
    ]
    
    size_type = models.CharField(max_length=10, choices=SIZE_TYPES, verbose_name="Tipo de talla")
    value = models.CharField(max_length=10, verbose_name="Valor")
    
    def __str__(self):
        return f"{self.get_size_type_display()} - {self.value}"

    class Meta:
        unique_together = ('size_type', 'value')
        verbose_name = "Talla"
        verbose_name_plural = "Tallas"


class Product(models.Model):
    MALE = 'M'
    FEMALE = 'F'
    UNISEX = 'U'
    GENDER_CHOICES = [
        (MALE, 'Masculino'),
        (FEMALE, 'Femenino'),
        (UNISEX, 'Unisex'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Nombre")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Género")
    description = models.TextField(blank=True, verbose_name="Descripción")
    materials = models.CharField(max_length=255, blank=True, verbose_name="Materiales")
    care_guide = models.TextField(blank=True, verbose_name="Guía de cuidado")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio base")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_default_image_url(self):
        """
        Retorna la URL de la imagen por defecto del producto.
        Busca una variante que tenga una imagen marcada como is_default=True;
        si no la encuentra, utiliza la primera variante y la primera imagen asociada.
        """
        variant = self.variants.filter(images__is_default=True).first()
        if not variant:
            variant = self.variants.first()
        if variant:
            image = variant.images.first()
            if image:
                return image.image.url
        return None

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="Producto")
    sku = models.CharField(max_length=50, unique=True, blank=True, verbose_name="SKU")
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Color")
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Talla")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio especial")

    def save(self, *args, **kwargs):
        if not self.sku:
            base_sku = slugify(
                f"{self.product.id}-"
                f"{self.color.name if self.color else 'NOCOLOR'}-"
                f"{self.size.value if self.size else 'NOSIZE'}"
            )
            self.sku = f"{base_sku.upper()[:45]}"
        super().save(*args, **kwargs)

    def clean(self):
        if self.stock < 0:
            raise ValidationError({'stock': 'El stock no puede ser negativo'})

    def __str__(self):
        return f"{self.product.name} - {self.sku}"

    class Meta:
        verbose_name = "Variante de Producto"
        verbose_name_plural = "Variantes de Producto"


class ProductImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images', verbose_name="Variante")
    image = models.ImageField(upload_to='product_images/', verbose_name="Imagen")
    is_default = models.BooleanField(default=False, verbose_name="Por defecto")

    def __str__(self):
        return f"Imagen para {self.variant.sku}"

    class Meta:
        verbose_name = "Imagen de Producto"
        verbose_name_plural = "Imágenes de Producto"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    shipping_address = models.CharField(max_length=255, verbose_name="Dirección")
    phone_number = models.CharField(max_length=20, verbose_name="Teléfono")
    wish_list = models.ManyToManyField('Product', blank=True, verbose_name="Lista de Deseados")

    def __str__(self):
        return f"Perfil de {self.user.username}"


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
    else:
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            Profile.objects.get_or_create(user=instance)


class Payment(models.Model):
    transaction_id = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Pendiente")

    def __str__(self):
        return f"Pago {self.transaction_id} - {self.status}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pendiente', 'Pendiente'),
        ('Pagado', 'Pagado'),
        ('Cancelado', 'Cancelado'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de la Orden")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pendiente")
    shipping_address = models.CharField(max_length=255, verbose_name="Dirección de envío")
    enviado = models.BooleanField(default=False)
    entregado = models.BooleanField(default=False)

    def __str__(self):
        return f"Orden {self.id} - {self.status}"
    
    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey('ProductVariant', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name="Cantidad")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de compra")

    def __str__(self):
        return f"{self.item} x {self.quantity}"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    comment = models.TextField(verbose_name="Comentario")
    rating = models.PositiveSmallIntegerField(verbose_name="Calificación")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reseña de {self.user.username} - {self.rating}"

    class Meta:
        verbose_name = "Reseña de Producto"
        verbose_name_plural = "Reseñas de Producto"
