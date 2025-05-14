import json
import uuid
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, TemplateView, DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView

from .forms import RegistrationForm, ProductReviewForm
from store.interfaces.cart import CartServiceInterface
from store.services.cart_session import SessionCartService
from .models import (
    Order, OrderItem, Payment, Product, ProductVariant, ProductReview, Color, Size
)

from django.utils.translation import gettext as _
from .currency import get_exchange_rate


# ============================================================================
# Vistas para Productos
# ============================================================================

class ProductListView(ListView):
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = Product.objects.all()
        query = self.request.GET.get('q')
        color = self.request.GET.get('color')
        size = self.request.GET.get('size')
        gender = self.request.GET.get('gender')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        if query:
            queryset = queryset.filter(name__icontains=query)
        if color:
            queryset = queryset.filter(variants__color__name=color)
        if size:
            queryset = queryset.filter(variants__size__value=size)
        if gender:
            queryset = queryset.filter(gender=gender)
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Manejo de moneda
        selected_currency = self.request.GET.get('currency') or self.request.session.get('currency', 'COP')
        if selected_currency not in settings.CURRENCIES:
            selected_currency = 'USD'
        self.request.session['currency'] = selected_currency
        
        context['available_currencies'] = settings.CURRENCIES
        context['selected_currency'] = selected_currency
        
        # Resto del contexto existente
        context.update({
            'colors': Color.objects.all(),
            'sizes': Size.objects.all(),
            'genders': Product.GENDER_CHOICES,
            'query': self.request.GET.get('q', '')
        })
        
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # ==============================================
        # Manejo de moneda y conversión
        # ==============================================
        selected_currency = self.request.GET.get('currency') or self.request.session.get('currency', 'COP')
        if selected_currency not in settings.CURRENCIES:
            selected_currency = 'USD'
        self.request.session['currency'] = selected_currency
        
        exchange_rate = get_exchange_rate('USD', selected_currency)
        
        # ==============================================
        # Construcción de mapas de precios con conversión
        # ==============================================
        all_variants = product.variants.all()
        color_map = {}
        variant_map = {}
        
        for variant in all_variants:
            # Precio base (USD)
            price = variant.price_override if variant.price_override else product.base_price
            converted_price = price * exchange_rate
            
            # Mapa de colores
            if variant.color:
                color_id = variant.color.id
                if color_id not in color_map:
                    color_map[color_id] = {
                        "image_url": str(variant.images.first().image.url if variant.images.first() 
                                      else product.get_default_image_url()),
                        "price": str(price),
                        "converted_price": str(converted_price),
                        "color_name": variant.color.name,
                    }

            # Mapa de variantes
            color_id = variant.color.id if variant.color else 0
            size_id = variant.size.id if variant.size else 0

            if color_id not in variant_map:
                variant_map[color_id] = {}

            variant_img = (variant.images.first().image.url if variant.images.first() 
                          else color_map.get(color_id, {}).get("image_url", product.get_default_image_url()))

            variant_map[color_id][size_id] = {
                'variant_id': variant.id,
                'image_url': str(variant_img),
                'price': str(price),
                'converted_price': str(converted_price),
                'size_value': variant.size.value if variant.size else _("N/A")
            }

        # ==============================================
        # Configuración de contextos
        # ==============================================
        # Moneda y conversión
        context.update({
            'available_currencies': settings.CURRENCIES,
            'selected_currency': selected_currency,
            'exchange_rate': exchange_rate,
            'currency_symbol': '€' if selected_currency == 'EUR' else '$'
        })
        
        # Mapas de productos
        context.update({
            'color_map_json': json.dumps(color_map),
            'variant_map_json': json.dumps(variant_map),
            'colors': product.variants.exclude(color__isnull=True)
                           .values('color__id', 'color__name').distinct(),
            'sizes': product.variants.exclude(size__isnull=True)
                          .values('size__id', 'size__value').distinct()
        })
        
        # Selección por defecto de color/talla
        if color_map:
            default_color_id = list(color_map.keys())[0]
            context['default_color_id'] = default_color_id
            
            if default_color_id in variant_map:
                sizes_for_default = list(variant_map[default_color_id].keys())
                context['default_size_id'] = sizes_for_default[0] if sizes_for_default else None
            else:
                context['default_size_id'] = None
        else:
            context['default_color_id'] = None
            context['default_size_id'] = None
        
        # Reseñas y validación de compra
        context['reviews'] = product.reviews.all().order_by('-created_at')
        if self.request.user.is_authenticated:
            context['purchased'] = Order.objects.filter(
                user=self.request.user, 
                items__item__product=product
            ).exists()
            
            if context['purchased']:
                if self.request.GET.get('clear_form'):
                    context['review_form'] = ProductReviewForm()
                else:
                    try:
                        review = product.reviews.get(user=self.request.user)
                        context['user_review'] = review
                        context['review_form'] = ProductReviewForm(instance=review)
                    except ProductReview.DoesNotExist:
                        context['review_form'] = ProductReviewForm()
            else:
                context['review_form'] = None
        else:
            context['purchased'] = False
            context['review_form'] = None

        return context


# ============================================================================
# Vistas relacionadas con el Carrito
# ============================================================================

class AddToCartView(View):
    cart_service: CartServiceInterface = SessionCartService()

    def post(self, request, product_id):
        variant_id = request.POST.get('variant_id')
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1
        if quantity < 1:
            quantity = 1

        # Calcular precio según variante o producto base
        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id)
            price = variant.price_override if variant.price_override else variant.product.base_price
        else:
            product = get_object_or_404(Product, id=product_id)
            price = product.base_price

        # Delegar lógica de carrito al servicio
        self.cart_service.add(
            request,
            variant_id=variant_id,
            product_id=product_id,
            quantity=quantity,
            price=price
        )
        return redirect('cart_detail')


class RemoveFromCartView(View):
    cart_service: CartServiceInterface = SessionCartService()

    def post(self, request, product_id):
        variant_id = request.POST.get('variant_id')
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1
        if quantity < 1:
            quantity = 1

        # Delegar eliminación al servicio
        self.cart_service.remove(
            request,
            variant_id=variant_id,
            product_id=product_id,
            quantity=quantity
        )
        return redirect('cart_detail')


class CartDetailView(TemplateView):
    template_name = 'store/cart_detail.html'
    cart_service: CartServiceInterface = SessionCartService()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener carrito crudo desde servicio
        cart = self.cart_service.get(self.request)

        # ====================================================================
        # Manejo de moneda y conversión
        # ====================================================================
        selected_currency = (
            self.request.GET.get('currency') or
            self.request.session.get('currency', 'COP')
        )
        if selected_currency not in settings.CURRENCIES:
            selected_currency = 'USD'
        self.request.session['currency'] = selected_currency

        exchange_rate = get_exchange_rate('USD', selected_currency)

        # ====================================================================
        # Procesamiento del carrito con conversión
        # ====================================================================
        items = []
        total_usd = Decimal('0.00')
        total_converted = Decimal('0.00')

        for key, details in cart.items():
            quantity = details['quantity']
            price_usd = Decimal(details['price'])
            subtotal_usd = price_usd * quantity

            # Precios convertidos
            price_converted = price_usd * exchange_rate
            subtotal_converted = subtotal_usd * exchange_rate

            if key.startswith('variant-'):
                variant_id = int(key.split('-')[1])
                variant = get_object_or_404(ProductVariant, id=variant_id)
                product = variant.product
                has_variant = True
            else:
                product_id = int(key)
                variant = None
                product = get_object_or_404(Product, id=product_id)
                has_variant = False

            items.append({
                'variant': variant,
                'product': product,
                'quantity': quantity,
                'price_usd': price_usd,
                'price_converted': price_converted,
                'subtotal_usd': subtotal_usd,
                'subtotal_converted': subtotal_converted,
                'has_variant': has_variant,
            })

            total_usd += subtotal_usd
            total_converted += subtotal_converted

        # ====================================================================
        # Configuración del contexto
        # ====================================================================
        context.update({
            'cart_items': items,
            'total_usd': total_usd,
            'total_converted': total_converted,
            'available_currencies': settings.CURRENCIES,
            'selected_currency': selected_currency,
            'exchange_rate': exchange_rate,
            'currency_symbol': '€' if selected_currency == 'EUR' else '$'
        })

        return context


# ============================================================================
# Vistas de Autenticación y Registro
# ============================================================================

class UserRegistrationView(FormView):
    template_name = 'store/registration.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        profile = user.profile
        profile.shipping_address = form.cleaned_data.get('shipping_address')
        profile.phone_number = form.cleaned_data.get('phone_number')
        profile.save()
        return super().form_valid(form)


# ============================================================================
# Vistas para Favoritos
# ============================================================================

class AddWishView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        profile = request.user.profile
        profile.wish_list.add(product)
        messages.success(request, _("Producto añadido a favoritos"))
        return redirect('wish_list')


class RemoveWishView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        profile = request.user.profile
        profile.wish_list.remove(product)
        messages.success(request, _("Producto eliminado de favoritos"))
        return redirect('wish_list')


class WishListView(LoginRequiredMixin, TemplateView):
    template_name = 'store/wish_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['wish_list'] = self.request.user.profile.wish_list.all()
        return context


# ============================================================================
# Vistas de Órdenes de Compra
# ============================================================================

class CreateOrderView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        if not cart:
            messages.warning(request, _("Tu carrito está vacío"))
            return redirect('product_list')

        total = Decimal('0.00')
        for key, details in cart.items():
            total += Decimal(details['price']) * details['quantity']

        shipping_address = request.user.profile.shipping_address

        order = Order.objects.create(
            user=request.user,
            total=total,
            shipping_address=shipping_address,
            status=_("Pendiente"),
        )

        for key, details in cart.items():
            if key.startswith("variant-"):
                variant_id = key.split("-")[1]
                variant = get_object_or_404(ProductVariant, id=variant_id)
            else:
                product = get_object_or_404(Product, id=int(key))
                variant = product.variants.first()
            OrderItem.objects.create(
                order=order,
                item=variant,
                quantity=details['quantity'],
                purchase_price=Decimal(details['price']),
            )
        request.session['cart'] = {}
        messages.success(request, _("Orden creada exitosamente"))
        return redirect('order_list')


class CancelOrderView(LoginRequiredMixin, View):
    def post(self, request, order_id, *args, **kwargs):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.entregado or order.enviado:
            messages.error(request, _("No se puede cancelar una orden ya enviada o entregada."))
        elif order.status == _("Cancelada"):
            messages.error(request, _("La orden ya está cancelada."))
        else:
            order.status = _("Cancelado")
            order.save()
            messages.success(request, _("Orden cancelada correctamente."))
        return redirect('order_list')


class PayOrderView(LoginRequiredMixin, View):
    def post(self, request, order_id, *args, **kwargs):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.payment is None and order.status == _("Pendiente"):
            transaction_id = str(uuid.uuid4()).upper()[:12]
            payment = Payment.objects.create(
                transaction_id=transaction_id,
                amount=order.total,
                status=_("Pagado"),
            )
            order.payment = payment
            order.status = _("Pagado")
            order.save()
            self.send_payment_email(order)
            messages.success(request, _("Pago procesado exitosamente"))
        return redirect('order_list')

    def send_payment_email(self, order):
        subject = _('Confirmación de pago')
        message = (
            f'{_("Hola")} {order.user.first_name},\n\n'
            f'{_("Tu orden con ID")} {order.id} {_("ha sido procesada correctamente.")}\n'
            f'{_("Transacción")}: {order.payment.transaction_id}\n'
            f'{_("Total pagado")}: ${order.payment.amount:,.2f}\n\n'
            f'{_("Gracias por tu compra.")}'
        )
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [order.user.email]
        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        except Exception as e:
            print(f"Error al enviar el correo: {e}")


class OrderListView(LoginRequiredMixin, TemplateView):
    template_name = 'store/order_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = Order.objects.filter(user=self.request.user).order_by('-order_date')
        context['orders'] = orders
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'store/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        order_items = []
        for item in order.items.all():
            subtotal = item.purchase_price * item.quantity
            order_items.append({
                'item': item,
                'subtotal': subtotal,
            })
        context['order_items'] = order_items
        return context


# ============================================================================
# Vistas de Reseñas
# ============================================================================

class CreateReviewView(LoginRequiredMixin, CreateView):
    model = ProductReview
    form_class = ProductReviewForm
    template_name = 'store/review_form.html'

    def form_valid(self, form):
        product = get_object_or_404(Product, id=self.kwargs['product_id'])
        form.instance.product = product
        form.instance.user = self.request.user
        messages.success(self.request, _("Reseña creada exitosamente"))
        return super().form_valid(form)

    def get_success_url(self):
        url = reverse('product_detail', kwargs={'pk': self.kwargs['product_id']})
        return f"{url}?clear_form=1"


class UpdateReviewView(LoginRequiredMixin, UpdateView):
    model = ProductReview
    form_class = ProductReviewForm
    template_name = 'store/review_form.html'

    def form_valid(self, form):
        messages.success(self.request, _("Reseña actualizada exitosamente"))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('product_detail', kwargs={'pk': self.object.product.id})


class DeleteReviewView(LoginRequiredMixin, DeleteView):
    model = ProductReview
    template_name = 'store/review_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Reseña eliminada exitosamente"))
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('product_detail', kwargs={'pk': self.object.product.id})


@method_decorator(login_required, name='dispatch')
class GenerateOrderPdfView(View):
    def get(self, request, pk, *args, **kwargs):
        order = get_object_or_404(Order, pk=pk, user=request.user)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="orden_{order.id}.pdf"'

        pdf = SimpleDocTemplate(response, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            name='TitleStyle',
            fontSize=18,
            leading=22,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph(_("Orden #{order_id}").format(order_id=order.id), title_style))

        details = f"""
        <strong>{_("Fecha")}:</strong> {order.order_date.strftime('%d/%m/%Y')}<br/>
        <strong>{_("Estado")}:</strong> {order.status}<br/>
        <strong>{_("Dirección de envío")}:</strong> {order.shipping_address if order.shipping_address else '-'}
        """
        elements.append(Paragraph(details, styles['Normal']))

        elements.append(Paragraph("<br/><br/>", styles['Normal']))

        elements.append(Paragraph(f"<strong>{_('Productos')}:</strong>", styles['Normal']))

        data = [
            [
                _("Producto"), 
                _("Cantidad"), 
                _("Precio Unitario"), 
                _("Subtotal")
            ]
        ]
        for item in order.items.all():
            product = item.item.product
            subtotal = item.purchase_price * item.quantity
            data.append([
                product.name,
                str(item.quantity),
                f"${item.purchase_price:,.2f}",
                f"${subtotal:,.2f}"
            ])

        table = Table(data, colWidths=[150, 80, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.black),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(table)

        total_style = ParagraphStyle(
            name='TotalStyle',
            fontSize=14,
            leading=16,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph(f"{_('Total')}: ${order.total:,.2f}", total_style))

        pdf.build(elements)

        return response