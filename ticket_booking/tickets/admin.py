from django.contrib import admin
from .models import Ticket, Cart, CartItem, Booking, BookingItem

# Register your models here.

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'type', 'price', 'available')
    list_filter = ('type', 'available')
    search_fields = ('event_name', 'description')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'ticket', 'quantity')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_price', 'booking_date')
    list_filter = ('booking_date',)

@admin.register(BookingItem)
class BookingItemAdmin(admin.ModelAdmin):
    list_display = ('booking', 'ticket', 'quantity')
