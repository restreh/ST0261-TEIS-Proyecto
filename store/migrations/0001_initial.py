# Generated by Django 5.0.4 on 2025-03-11 07:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Color',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
            options={
                'verbose_name': 'Color',
                'verbose_name_plural': 'Colores',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Nombre')),
                ('gender', models.CharField(choices=[('M', 'Masculino'), ('F', 'Femenino'), ('U', 'Unisex')], max_length=1, verbose_name='Género')),
                ('description', models.TextField(blank=True, verbose_name='Descripción')),
                ('materials', models.CharField(blank=True, max_length=255, verbose_name='Materiales')),
                ('care_guide', models.TextField(blank=True, verbose_name='Guía de cuidado')),
                ('base_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Precio base')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Producto',
                'verbose_name_plural': 'Productos',
            },
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sku', models.CharField(blank=True, max_length=50, unique=True, verbose_name='SKU')),
                ('stock', models.PositiveIntegerField(default=0, verbose_name='Stock')),
                ('price_override', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Precio especial')),
                ('color', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.color', verbose_name='Color')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='store.product', verbose_name='Producto')),
            ],
            options={
                'verbose_name': 'Variante de Producto',
                'verbose_name_plural': 'Variantes de Producto',
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='product_images/', verbose_name='Imagen')),
                ('is_default', models.BooleanField(default=False, verbose_name='Por defecto')),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='store.productvariant', verbose_name='Variante')),
            ],
            options={
                'verbose_name': 'Imagen de Producto',
                'verbose_name_plural': 'Imágenes de Producto',
            },
        ),
        migrations.CreateModel(
            name='Size',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size_type', models.CharField(choices=[('clothing', 'Ropa'), ('shoe', 'Calzado')], max_length=10, verbose_name='Tipo de talla')),
                ('value', models.CharField(max_length=10, verbose_name='Valor')),
            ],
            options={
                'verbose_name': 'Talla',
                'verbose_name_plural': 'Tallas',
                'unique_together': {('size_type', 'value')},
            },
        ),
        migrations.AddField(
            model_name='productvariant',
            name='size',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.size', verbose_name='Talla'),
        ),
    ]
