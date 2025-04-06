from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('ticket/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:ticket_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('booking-confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('payment-success/', views.payment_success, name='payment_success'),
]