from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import FormView
from .models import Order, OrderItem, Payment, Product, ProductVariant
from .forms import RegistrationForm
from django.urls import reverse_lazy
from django.utils import timezone
import uuid
from decimal import Decimal
from django.contrib import messages

class ProductListView(ListView):
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'

class CartMixin:
    """Mixin para obtener y guardar el carrito en la sesión."""
    def get_cart(self, request):
        return request.session.get('cart', {})

    def save_cart(self, request, cart):
        request.session['cart'] = cart
        request.session.modified = True

class AddToCartView(View, CartMixin):

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1
        if quantity < 1:
            quantity = 1

        cart = self.get_cart(request)
        key = str(product_id)
        if key in cart:
            cart[key]['quantity'] += quantity
        else:
            cart[key] = {'quantity': quantity, 'price': str(product.base_price)}
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
        total = 0
        for pid, details in cart.items():
            product = get_object_or_404(Product, id=pid)
            quantity = details['quantity']
            price = product.base_price
            subtotal = price * quantity
            total += subtotal
            items.append({
                'product': product,
                'quantity': quantity,
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
        for pid, details in cart.items():
            total += Decimal(details['price']) * details['quantity']

        shipping_address = request.user.profile.shipping_address

        order = Order.objects.create(
            user=request.user,
            total=total,
            shipping_address=shipping_address,
            status="Pendiente",
        )

        for pid, details in cart.items():
            product = get_object_or_404(Product, id=pid)
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
