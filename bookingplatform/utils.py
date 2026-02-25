from datetime import date
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import F
from .models import Booking
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
import logging
from django.conf import settings
import razorpay

# Set up logging to see errors in your terminal
logger = logging.getLogger(__name__)

def calculate_age(dob):
    if not dob:
        return None

    today = date.today()
    return today.year - dob.year - (
        (today.month, today.day) < (dob.month, dob.day)
    )
#helper-a small reusable function
def get_lab_from_request(request):
    user = request.user

    if user.role == 'LAB_ADMIN':
        return user.labadmin_profile.lab

    if user.role == 'STAFF':
        return user.staffprofile.lab

    raise PermissionDenied("No lab access")

def expire_pending_bookings(lab=None):
    now = timezone.now()
    expired_bookings = Booking.objects.filter(
        status='PENDING',
        expires_at__lt=now
    ).select_related('payment', 'slot')

    for booking in expired_bookings:
        with transaction.atomic():
            #  Update Booking status
            booking.status = 'EXPIRED'
            #  Update Booking's internal payment field
            booking.payment_status = 'FAILED' 
            booking.save(update_fields=['status', 'payment_status'])

            #  Update the actual Payment table record
            if hasattr(booking, 'payment'):
                p = booking.payment
                if p.status == 'PENDING':
                    p.status = 'FAILED'
                    p.save(update_fields=['status'])

            #  Release Slot
            if booking.slot and booking.slot.booked_count > 0:
                booking.slot.booked_count = F('booked_count') - 1
                booking.slot.save(update_fields=['booked_count'])
            
def process_refund(payment):
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        refund = client.payment.refund(
            payment.razorpay_payment_id,
            {
                "amount": int((payment.amount)*100)
            }
        )
    except Exception as e:
        print(f"RAZORPAY ERROR: {e}") 
        return False, str(e)
    booking=payment.booking
    
    #if refund succssful
    payment.status = 'REFUNDED'
    payment.save(update_fields=['status'])

    booking.payment_status = 'REFUNDED'
    booking.status = 'CANCELLED'
    booking.save(update_fields=['payment_status','status'])

    # Release slot
    if booking.slot and booking.slot.booked_count > 0:
        booking.slot.booked_count = F('booked_count') - 1
        booking.slot.save(update_fields=['booked_count'])

    return True, None