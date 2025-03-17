import nested_admin
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import (
    Product, ProductVariant, Color, Size, ProductImage,
    Order, OrderItem, Payment
)

class ProductImageInline(nested_admin.NestedTabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'is_default')
    verbose_name = "Imagen"
    verbose_name_plural = "Imágenes"

class ProductVariantInline(nested_admin.NestedStackedInline):
    model = ProductVariant
    extra = 1
    fields = ('color', 'size', 'stock', 'price_override')
    verbose_name = "Variante"
    verbose_name_plural = "Variantes"
    inlines = [ProductImageInline]

@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = ('name', 'gender', 'base_price', 'created_at')
    list_filter = ('gender', 'created_at')
    search_fields = ('name', 'description')
    fieldsets = (
        (None, {
            'fields': ('name', 'gender', 'base_price')
        }),
        ('Detalles', {
            'fields': ('description', 'materials', 'care_guide'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ProductVariantInline]

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    search_fields = ('name',)

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('size_type', 'value')
    list_filter = ('size_type',)
    search_fields = ('value',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('item', 'quantity', 'purchase_price')
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_date', 'total', 'status', 'enviado', 'entregado', 'shipping_address')
    list_filter = ('status', 'order_date', 'enviado', 'entregado')
    inlines = [OrderItemInline]
    readonly_fields = ('user', 'order_date', 'total', 'shipping_address', 'payment', 'status')
    fields = ('user', 'status', 'shipping_address', 'payment', 'enviado', 'entregado')
    
    def save_model(self, request, obj, form, change):
        if obj.status == 'Cancelado':
            if 'enviado' in form.changed_data or 'entregado' in form.changed_data:
                self.message_user(request, _("No se pueden actualizar los estados de una orden cancelada."), messages.ERROR)
                return
        
        if change:
            old_obj = Order.objects.get(pk=obj.pk)
            if old_obj.status == 'Pagado' and not old_obj.enviado and obj.enviado:
                for item in obj.items.all():
                    variant = item.item
                    if variant.stock < item.quantity:
                        self.message_user(
                            request,
                            _(f"Stock insuficiente para {variant.product.name} (Disponible: {variant.stock})."),
                            messages.ERROR
                        )
                        return
                    variant.stock -= item.quantity
                    variant.save()
                self.message_user(request, _("Orden marcada como 'Enviado' y stock descontado."), messages.SUCCESS)
            if old_obj.enviado and not old_obj.entregado and obj.entregado:
                self.message_user(request, _("Orden marcada como 'Entregado'."), messages.SUCCESS)
        super().save_model(request, obj, form, change)
