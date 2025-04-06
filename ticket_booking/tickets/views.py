import json
import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F, Sum
from django.utils import timezone
from .models import Ticket, Cart, CartItem, Booking, BookingItem

def home(request):
    # Get search parameters
    from_city = request.GET.get('from')
    to_city = request.GET.get('to')
    travel_date = request.GET.get('date')

    # Start with all available tickets
    tickets = Ticket.objects.filter(available=True)

    # Apply filters if search parameters are provided
    if from_city:
        tickets = tickets.filter(venue__icontains=from_city)
    if to_city:
        tickets = tickets.filter(event_name__icontains=to_city)
    if travel_date:
        date_obj = timezone.datetime.strptime(travel_date, '%Y-%m-%d').date()
        tickets = tickets.filter(event_date__date=date_obj)

    context = {
        'tickets': tickets,
        'from_city': from_city,
        'to_city': to_city,
        'travel_date': travel_date,
        'khalti_public_key': settings.KHALTI_PUBLIC_KEY
    }
    return render(request, 'tickets/home.html', context)

def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    tax_amount = round(ticket.price * 0.13, 2)  # 13% tax
    total_price = ticket.price + tax_amount
    
    context = {
        'ticket': ticket,
        'tax_amount': tax_amount,
        'total_price': total_price,
        'khalti_public_key': settings.KHALTI_PUBLIC_KEY
    }
    return render(request, 'tickets/ticket_detail.html', context)

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(cart__user=request.user).select_related('ticket')
    
    # Calculate totals
    cart_total = sum(item.ticket.price * item.quantity for item in cart_items)
    tax_amount = round(cart_total * 0.13, 2)  # 13% tax
    total_with_tax = cart_total + tax_amount
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'tax_amount': tax_amount,
        'total_with_tax': total_with_tax
    }
    return render(request, 'tickets/cart.html', context)

@login_required
def add_to_cart(request, ticket_id):
    if request.method == 'POST':
        ticket = get_object_or_404(Ticket, id=ticket_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            ticket=ticket,
            defaults={'quantity': 1}
        )
        if not created:
            cart_item.quantity = F('quantity') + 1
            cart_item.save()
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
def update_cart(request, item_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            
            if action == 'increase':
                cart_item.quantity = F('quantity') + 1
            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity = F('quantity') - 1
                else:
                    cart_item.delete()
                    return JsonResponse({'success': True})
            
            cart_item.save()
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False}, status=400)

@login_required
def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    total_price = sum(item.ticket.price * item.quantity for item in cart.cartitem_set.all())
    
    if request.method == 'POST':
        # Create the booking
        booking = Booking.objects.create(
            user=request.user,
            total_price=total_price
        )
        
        # Add items to booking
        for cart_item in cart.cartitem_set.all():
            BookingItem.objects.create(
                booking=booking,
                ticket=cart_item.ticket,
                quantity=cart_item.quantity
            )
        
        # Clear the cart
        cart.cartitem_set.all().delete()
        
        return redirect('booking_confirmation', booking_id=booking.id)
    
    return render(request, 'tickets/checkout.html', {
        'cart': cart,
        'total_price': total_price
    })

@csrf_exempt
@login_required
def verify_payment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
    try:
        # Get the payment data
        data = json.loads(request.body)
        token = data.get("token")
        amount = data.get("amount")
        ticket_id = data.get("ticket_id")

        if not all([token, amount, ticket_id]):
            return JsonResponse({"error": "Missing required parameters"}, status=400)

        # Verify with Khalti
        headers = {
            "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "token": token,
            "amount": amount
        }

        # Make request to Khalti
        response = requests.post(
            settings.KHALTI_VERIFY_URL,
            json=payload,
            headers=headers
        )
        
        resp_data = response.json()
        
        if response.status_code == 200:
            # Payment successful, create booking
            ticket = get_object_or_404(Ticket, id=ticket_id)
            
            # Create booking
            booking = Booking.objects.create(
                user=request.user,
                total_price=float(amount)/100  # Convert paisa to rupees
            )
            
            # Add ticket to booking
            BookingItem.objects.create(
                booking=booking,
                ticket=ticket,
                quantity=1,
                price=ticket.price
            )
            
            # Clear the cart after successful booking
            Cart.objects.filter(user=request.user).delete()
            
            return JsonResponse({
                "status": "success",
                "message": "Payment Successful",
                "data": resp_data
            })
        else:
            return JsonResponse({
                "status": "error",
                "message": "Payment Verification Failed",
                "data": resp_data
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    context = {
        'booking': booking
    }
    return render(request, 'tickets/booking_confirmation.html', context)

def payment_success(request):
    return render(request, 'tickets/payment_success.html')
