from django.db import models
from accounts.models import CustomUser
from django.utils import timezone

class Ticket(models.Model):
    TICKET_TYPES = [
        ('bus', 'Bus'),
        ('aeroplane', 'Aeroplane'),
    ]
    type = models.CharField(max_length=20, choices=TICKET_TYPES)
    event_name = models.CharField(max_length=100)
    venue = models.CharField(max_length=200)
    event_date = models.DateTimeField(default=timezone.now)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.event_name

class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    tickets = models.ManyToManyField(Ticket, through='CartItem')

    def __str__(self):
        return f"Cart of {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.ticket.event_name}"

class Booking(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tickets = models.ManyToManyField(Ticket, through='BookingItem')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    booking_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking by {self.user.username} on {self.booking_date}"

class BookingItem(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.ticket.event_name}"

# Create your models here.
