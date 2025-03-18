from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, TemplateView, DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.http import HttpResponse
from .models import Order, OrderItem, Payment, Product, ProductVariant, ProductReview, Color, Size
from .forms import RegistrationForm, ProductReviewForm
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
import uuid
from decimal import Decimal
from django.contrib import messages
import json
from django.conf import settings
from django.core.mail import send_mail

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

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
        context['colors'] = Color.objects.all()
        context['sizes'] = Size.objects.all()
        context['genders'] = Product.GENDER_CHOICES
        context['query'] = self.request.GET.get('q', '')
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        all_variants = product.variants.all()

        color_map = {}
        for variant in all_variants:
            if variant.color:
                color_id = variant.color.id
                if color_id not in color_map:
                    if variant.images.first():
                        color_img = variant.images.first().image.url
                    else:
                        color_img = product.get_default_image_url()
                    if variant.price_override:
                        color_price = variant.price_override
                    else:
                        color_price = product.base_price
                    color_map[color_id] = {
                        "image_url": str(color_img),
                        "price": str(color_price),
                        "color_name": variant.color.name,
                    }


        variant_map = {}
        for variant in all_variants:
            color_id = variant.color.id if variant.color else 0
            size_id = variant.size.id if variant.size else 0

            if color_id not in variant_map:
                variant_map[color_id] = {}

            if variant.images.first():
                variant_img = variant.images.first().image.url
            else:
                variant_img = color_map.get(color_id, {}).get("image_url", product.get_default_image_url())

            if variant.price_override:
                final_price = variant.price_override
            else:
                final_price = product.base_price

            variant_map[color_id][size_id] = {
                'variant_id': variant.id,
                'image_url': str(variant_img),
                'price': str(final_price),
                'size_value': variant.size.value if variant.size else "N/A"
            }


        colors = product.variants.exclude(color__isnull=True).values('color__id', 'color__name').distinct()
        sizes = product.variants.exclude(size__isnull=True).values('size__id', 'size__value').distinct()

        context['color_map_json'] = json.dumps(color_map)
        context['variant_map_json'] = json.dumps(variant_map)
        context['colors'] = colors
        context['sizes'] = sizes

        if color_map:
            default_color_id = list(color_map.keys())[0]
            context['default_color_id'] = default_color_id
        else:
            context['default_color_id'] = None

        if context['default_color_id'] and context['default_color_id'] in variant_map:
            sizes_for_default = list(variant_map[context['default_color_id']].keys())
            if sizes_for_default:
                default_size_id = sizes_for_default[0]
                context['default_size_id'] = default_size_id
            else:
                context['default_size_id'] = None
        else:
            context['default_size_id'] = None

        context['reviews'] = product.reviews.all().order_by('-created_at')
        user = self.request.user
        purchased = False
        if user.is_authenticated:
            purchased = Order.objects.filter(user=user, items__item__product=self.get_object()).exists()
        context['purchased'] = purchased
        if purchased and user.is_authenticated:
            if self.request.GET.get('clear_form'):
                context['review_form'] = ProductReviewForm()
            else:
                try:
                    review = self.get_object().reviews.get(user=user)
                    context['user_review'] = review
                    context['review_form'] = ProductReviewForm(instance=review)
                except ProductReview.DoesNotExist:
                    context['review_form'] = ProductReviewForm()
        return context


class CartMixin:
    """Mixin para obtener y guardar el carrito en la sesión."""
    def get_cart(self, request):
        return request.session.get('cart', {})

    def save_cart(self, request, cart):
        request.session['cart'] = cart
        request.session.modified = True

class AddToCartView(View, CartMixin):
    def post(self, request, product_id):
        variant_id = request.POST.get('variant_id')
        quantity = request.POST.get('quantity', 1)

        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 1
        if quantity < 1:
            quantity = 1

        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id)
            price = variant.price_override if variant.price_override else variant.product.base_price
            key = f"variant-{variant_id}"
        else:
            product = get_object_or_404(Product, id=product_id)
            price = product.base_price
            key = str(product_id)

        cart = self.get_cart(request)
        if key in cart:
            cart[key]['quantity'] += quantity
        else:
            cart[key] = {'quantity': quantity, 'price': str(price)}
        self.save_cart(request, cart)
        return redirect('cart_detail')

class RemoveFromCartView(View, CartMixin):

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1

        cart = self.get_cart(request)
        key = str(product_id)
        if key in cart:
            if quantity >= cart[key]['quantity']:
                del cart[key]
            else:
                cart[key]['quantity'] -= quantity
            self.save_cart(request, cart)
        return redirect('cart_detail')

class CartDetailView(TemplateView, CartMixin):
    template_name = 'store/cart_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_cart(self.request)
        items = []
        total = Decimal('0.00')
        for key, details in cart.items():
            quantity = details['quantity']
            price = Decimal(details['price'])
            if key.startswith("variant-"):
                variant_id = key.split("-")[1]
                variant = get_object_or_404(ProductVariant, id=variant_id)
                product = variant.product
                subtotal = price * quantity
                total += subtotal
                items.append({
                    'variant': variant,
                    'product': product,
                    'quantity': quantity,
                    'price': price,
                    'subtotal': subtotal,
                })
            else:
                product_id = int(key)
                product = get_object_or_404(Product, id=product_id)
                subtotal = price * quantity
                total += subtotal
                items.append({
                    'variant': None,
                    'product': product,
                    'quantity': quantity,
                    'price': price,
                    'subtotal': subtotal,
                })
        context['cart_items'] = items
        context['total'] = total
        return context


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


class AddWishView(LoginRequiredMixin, View):

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        profile = request.user.profile
        profile.wish_list.add(product)
        return redirect('wish_list')

class RemoveWishView(LoginRequiredMixin, View):

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        profile = request.user.profile
        profile.wish_list.remove(product)
        return redirect('wish_list')

class WishListView(LoginRequiredMixin, TemplateView):

    template_name = 'store/wish_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['wish_list'] = self.request.user.profile.wish_list.all()
        return context


class CreateOrderView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        cart = request.session.get('cart', {})
        if not cart:
            return redirect('product_list')

        total = Decimal('0.00')
        for key, details in cart.items():
            total += Decimal(details['price']) * details['quantity']

        shipping_address = request.user.profile.shipping_address

        order = Order.objects.create(
            user=request.user,
            total=total,
            shipping_address=shipping_address,
            status="Pendiente",
        )

        for key, details in cart.items():
            if key.startswith("variant-"):
                # Extraer el ID de la variante
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
        return redirect('order_list')

class CancelOrderView(LoginRequiredMixin, View):
    def post(self, request, order_id, *args, **kwargs):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.entregado or order.enviado:
            messages.error(request, "No se puede cancelar una orden ya enviada o entregada.")
        elif order.status == "Cancelado":
            messages.error(request, "La orden ya está cancelada.")
        else:
            order.status = "Cancelado"
            order.save()
            messages.success(request, "Orden cancelada correctamente.")
        return redirect('order_list')

class PayOrderView(LoginRequiredMixin, View):
    def post(self, request, order_id, *args, **kwargs):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.payment is None and order.status == "Pendiente":
            transaction_id = str(uuid.uuid4()).upper()[:12]
            payment = Payment.objects.create(
                transaction_id=transaction_id,
                amount=order.total,
                status="Pagado",
            )
            order.payment = payment
            order.status = "Pagado"
            order.save()

            self.send_payment_email(order)

        return redirect('order_list')

    def send_payment_email(self, order):
        subject = 'Confirmación de pago'
        message = (
            f'Hola {order.user.first_name},\n\n'
            f'Tu orden con ID {order.id} ha sido procesada correctamente.\n'
            f'Transacción: {order.payment.transaction_id}\n'
            f'Total pagado: ${order.payment.amount:.2f}\n\n'
            'Gracias por tu compra.'
        )
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [order.user.email]

        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            print(f"Correo enviado a {recipient_list[0]}")
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


class CreateReviewView(LoginRequiredMixin, CreateView):
    model = ProductReview
    form_class = ProductReviewForm
    template_name = 'store/review_form.html'
    
    def form_valid(self, form):
        product = get_object_or_404(Product, id=self.kwargs['product_id'])
        form.instance.product = product
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        url = reverse('product_detail', kwargs={'pk': self.kwargs['product_id']})
        return f"{url}?clear_form=1"

class UpdateReviewView(LoginRequiredMixin, UpdateView):
    model = ProductReview
    form_class = ProductReviewForm
    template_name = 'store/review_form.html'
    
    def get_success_url(self):
        return reverse('product_detail', kwargs={'pk': self.object.product.id})

class DeleteReviewView(LoginRequiredMixin, DeleteView):
    model = ProductReview
    template_name = 'store/review_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('product_detail', kwargs={'pk': self.object.product.id})


@method_decorator(login_required, name='dispatch')
class GenerateOrderPdfView(View):
    def get(self, request, pk, *args, **kwargs):
        
        order = get_object_or_404(Order, pk=pk, user=request.user)

        # Crear el response para PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="orden_{order.id}.pdf"'

        # Crear documento PDF
        pdf = SimpleDocTemplate(response, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Título de la orden
        title_style = ParagraphStyle(
            name='TitleStyle',
            fontSize=18,
            leading=22,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph(f"Orden #{order.id}", title_style))

        # Fecha, Estado y Dirección de envío
        details = f"""
        <strong>Fecha:</strong> {order.order_date.strftime('%d/%m/%Y')}<br/>
        <strong>Estado:</strong> {order.status}<br/>
        <strong>Dirección de envío:</strong> {order.shipping_address if order.shipping_address else '-'}
        """
        elements.append(Paragraph(details, styles['Normal']))

        # Espacio después de los detalles
        elements.append(Paragraph("<br/><br/>", styles['Normal']))

        # Título de productos
        elements.append(Paragraph("<strong>Productos:</strong>", styles['Normal']))

        # Definir datos de la tabla
        data = [['Producto', 'Cantidad', 'Precio Unitario', 'Subtotal']]
        for item in order.items.all():
            product = item.item.product
            subtotal = item.purchase_price * item.quantity
            data.append([
                product.name,
                str(item.quantity),
                f"${item.purchase_price:,.2f}",
                f"${subtotal:,.2f}"
            ])

        # Estilo de la tabla
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

        # Total de la orden
        total_style = ParagraphStyle(
            name='TotalStyle',
            fontSize=14,
            leading=16,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph(f"Total: ${order.total:,.2f}", total_style))

        # Crear el PDF
        pdf.build(elements)

        return response