from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import (
    ProductListView, UserRegistrationView, AddWishView, RemoveWishView, WishListView,
    AddToCartView, RemoveFromCartView, CartDetailView, CreateOrderView, CancelOrderView,
    OrderListView, PayOrderView, OrderDetailView, ProductDetailView,
    CreateReviewView, UpdateReviewView, DeleteReviewView, GenerateOrderPdfView
)

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('product/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('product/<int:product_id>/review/create/', CreateReviewView.as_view(), name='create_review'),
    path('review/<int:pk>/edit/', UpdateReviewView.as_view(), name='edit_review'),
    path('review/<int:pk>/delete/', DeleteReviewView.as_view(), name='delete_review'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(template_name='store/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='product_list'), name='logout'),
    path('cart/', CartDetailView.as_view(), name='cart_detail'),
    path('cart/add/<int:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('cart/remove/<int:product_id>/', RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('order/create/', CreateOrderView.as_view(), name='create_order'),
    path('order/cancel/<int:order_id>/', CancelOrderView.as_view(), name='cancel_order'),
    path('order/pay/<int:order_id>/', PayOrderView.as_view(), name='pay_order'),
    path('order/', OrderListView.as_view(), name='order_list'),
    path('order/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('wish_list/', WishListView.as_view(), name='wish_list'),
    path('wish_list/add/<int:product_id>/', AddWishView.as_view(), name='add_wish'),
    path('wish_list/remove/<int:product_id>/', RemoveWishView.as_view(), name='remove_wish'),
    path('order/<int:pk>/pdf/', GenerateOrderPdfView.as_view(), name='order_pdf'),
]