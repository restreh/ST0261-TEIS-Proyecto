from store.interfaces.cart import CartServiceInterface

class SessionCartService(CartServiceInterface):
    """Gestiona el carrito usando la sesión de Django."""

    SESSION_KEY = 'cart'

    def get(self, request):
        return request.session.get(self.SESSION_KEY, {})

    def save(self, request, cart):
        request.session[self.SESSION_KEY] = cart
        request.session.modified = True

    def add(self, request, *, variant_id=None, product_id, quantity, price):
        cart = self.get(request)
        if variant_id:
            key = f"variant-{variant_id}"
        else:
            key = str(product_id)

        if key in cart:
            cart[key]['quantity'] += quantity
        else:
            cart[key] = {'quantity': quantity, 'price': str(price)}
        self.save(request, cart)

    def remove(self, request, *, variant_id=None, product_id, quantity):
        cart = self.get(request)
        key = f"variant-{variant_id}" if variant_id else str(product_id)
        if key in cart:
            if quantity >= cart[key]['quantity']:
                del cart[key]
            else:
                cart[key]['quantity'] -= quantity
            self.save(request, cart)
