from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, TemplateView, DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from .models import Order, OrderItem, Payment, Product, ProductVariant, ProductReview
from .forms import RegistrationForm, ProductReviewForm
from django.urls import reverse, reverse_lazy
from django.utils import timezone
import uuid
from decimal import Decimal
from django.contrib import messages
import json

class ProductListView(ListView):
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'

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
        return redirect('order_list')

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