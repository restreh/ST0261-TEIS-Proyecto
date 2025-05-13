import uuid
from decimal import Decimal
from pydantic import ValidationError
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

class Color(models.Model):
    name = models.CharField(_("Nombre"), max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Color")
        verbose_name_plural = _("Colores")

class Size(models.Model):
    CLOTHING = 'clothing'
    SHOE = 'shoe'
    SIZE_TYPES = [
        (CLOTHING, _("Ropa")),
        (SHOE, _("Calzado")),
    ]
    
    size_type = models.CharField(_("Tipo de talla"), max_length=10, choices=SIZE_TYPES)
    value = models.CharField(_("Valor"), max_length=10)
    
    def __str__(self):
        return f"{self.get_size_type_display()} - {self.value}"

    class Meta:
        unique_together = ('size_type', 'value')
        verbose_name = _("Talla")
        verbose_name_plural = _("Tallas")

class Product(models.Model):
    MALE = 'M'
    FEMALE = 'F'
    UNISEX = 'U'
    GENDER_CHOICES = [
        (MALE, _("Masculino")),
        (FEMALE, _("Femenino")),
        (UNISEX, _("Unisex")),
    ]
    
    name = models.CharField(_("Nombre"), max_length=255)
    gender = models.CharField(_("Género"), max_length=1, choices=GENDER_CHOICES)
    description = models.TextField(_("Descripción"), blank=True)
    materials = models.CharField(_("Materiales"), max_length=255, blank=True)
    care_guide = models.TextField(_("Guía de cuidado"), blank=True)
    base_price = models.DecimalField(_("Precio base"), max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_default_image_url(self):
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
        verbose_name = _("Producto")
        verbose_name_plural = _("Productos")

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name=_("Producto"))
    sku = models.CharField(_("SKU"), max_length=50, unique=True, blank=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Color"))
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Talla"))
    stock = models.PositiveIntegerField(_("Stock"), default=0)
    price_override = models.DecimalField(_("Precio especial"), max_digits=10, decimal_places=2, null=True, blank=True)

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
            raise ValidationError({'stock': _('El stock no puede ser negativo')})

    def __str__(self):
        return f"{self.product.name} - {self.sku}"

    class Meta:
        verbose_name = _("Variante de Producto")
        verbose_name_plural = _("Variantes de Producto")

class ProductImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images', verbose_name=_("Variante"))
    image = models.ImageField(_("Imagen"), upload_to='product_images/')
    is_default = models.BooleanField(_("Por defecto"), default=False)

    def __str__(self):
        return f"Imagen para {self.variant.sku}"

    class Meta:
        verbose_name = _("Imagen de Producto")
        verbose_name_plural = _("Imágenes de Producto")

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    shipping_address = models.CharField(_("Dirección"), max_length=255)
    phone_number = models.CharField(_("Teléfono"), max_length=20)
    wish_list = models.ManyToManyField('Product', blank=True, verbose_name=_("Lista de Deseados"))

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
    transaction_id = models.CharField(_("ID de transacción"), max_length=50, unique=True)
    amount = models.DecimalField(_("Monto"), max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(_("Fecha de pago"), auto_now_add=True)
    status = models.CharField(_("Estado"), max_length=20, default=_("Pendiente"))

    def __str__(self):
        return f"Pago {self.transaction_id} - {self.status}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pendiente', _("Pendiente")),
        ('Pagado', _("Pagado")),
        ('Cancelado', _("Cancelado")),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    order_date = models.DateTimeField(_("Fecha de la Orden"), auto_now_add=True)
    total = models.DecimalField(_("Total"), max_digits=10, decimal_places=2)
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(_("Estado"), max_length=20, choices=STATUS_CHOICES, default=_("Pendiente"))
    shipping_address = models.CharField(_("Dirección de envío"), max_length=255)
    enviado = models.BooleanField(_("Enviado"), default=False)
    entregado = models.BooleanField(_("Entregado"), default=False)

    def __str__(self):
        return f"Orden {self.id} - {self.status}"
    
    class Meta:
        verbose_name = _("Orden de Compra")
        verbose_name_plural = _("Órdenes de Compra")

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey('ProductVariant', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(_("Cantidad"))
    purchase_price = models.DecimalField(_("Precio de compra"), max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.item} x {self.quantity}"

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    comment = models.TextField(_("Comentario"))
    rating = models.PositiveSmallIntegerField(_("Calificación"))
    created_at = models.DateTimeField(_("Fecha de creación"), auto_now_add=True)

    def __str__(self):
        return f"Reseña de {self.user.username} - {self.rating}"

    class Meta:
        verbose_name = _("Reseña de Producto")
        verbose_name_plural = _("Reseñas de Producto")