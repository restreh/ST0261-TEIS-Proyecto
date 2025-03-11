import nested_admin
from django.contrib import admin
from .models import Product, ProductVariant, Color, Size, ProductImage

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
