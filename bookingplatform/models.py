from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from ckeditor.fields import RichTextField
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.utils import timezone
from datetime import timedelta


#--------------------------------------#
# Custom User model
#--------------------------------------#

class User(AbstractUser):
    ROLE_CHOICES = (
        ('PATIENT', 'Patient'),
        ('LAB_ADMIN', 'Lab Admin'),
        ('STAFF', 'Staff'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='PATIENT'
    )

    def __str__(self):
        return self.username or self.email

#--------------------------------------#
# Patient Profile model
#--------------------------------------#

class PatientProfile(models.Model):
    GENDER_CHOICES = (
        ('MALE','Male'),
        ('FEMALE','Female'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='patient_profile'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    mobile = models.CharField(max_length=13)

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True
    )
    address = models.TextField(
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

#--------------------------------------#
# Lab Profile model
#--------------------------------------#

class Lab(models.Model):
    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=15)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
#--------------------------------------#
# Lab Admin Profile model
#--------------------------------------#

class LabAdminProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='labadmin_profile'
    )
    lab = models.ForeignKey(
        Lab,
        on_delete=models.CASCADE,
        related_name='lab_admins'
    )
    name = models.CharField(max_length=100, blank=True)
    mobile = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.user.email    
#--------------------------------------#
# Package Category model
#--------------------------------------#
class PackageCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=255,
        help_text='Font Awesome icons(e.g. fa-dna, fa-heartbeat)',
        blank=True
    )

    def __str__(self):
        return self.name

#--------------------------------------#
# Lab Package model
# one lab-one package
#--------------------------------------#

class LabTest(models.Model):
    RESULT_TYPE_CHOICES = (
        ('NUMERIC','Numeric'),
        ('BINARY','Positive / Negative'),
        ('TEXT','Text'),
        ('IMAGING', 'Imaging /Scan'),
    )

    name = models.CharField(max_length=255,unique=True,db_collation="nocase")
    description = models.TextField()

    result_type = models.CharField(
        max_length=20,
        choices=RESULT_TYPE_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)


    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    class Meta:
        
        ordering = ['-name']

class LabPackage(models.Model): #labprofile is deleted will delete all packages
    HOME_COLLECTION_CHOICES = (
        ('YES', 'Home Collection Available'),
        ('NO', 'Lab Visit Required'),
        )
    #one lab has many packages
    lab = models.ForeignKey(
        Lab,
        on_delete=models.CASCADE,
        related_name='packages'
    )


    category = models.ForeignKey(
        PackageCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='packages'
    )

    name = models.CharField(max_length=255)
    intro_heading = models.CharField(
        max_length=255,
         help_text="Eg: What is Breast Cancer?"
         )
    intro_description = RichTextField()
    tests = models.ManyToManyField(
        LabTest,
        related_name='packages',
        blank=True
    )
    risk_factors = RichTextField()
    age_recommendation = RichTextField()
    min_age = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text='Minimum age in years'
    )
    max_age = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        help_text='Maximum age in years'
    )
    gender = models.CharField(
        max_length=10,
        choices=(
            ('MALE','Male'),
            ('FEMALE','Female'),
            ('BOTH','Both'))        
    )
    recommended_age_text = models.CharField(max_length=255,null=True,blank=True)
    price = models.DecimalField(max_digits=8,decimal_places=2)
    report_time = models.CharField(max_length=100)
    home_collection = models.CharField(
        max_length=3,
        choices=HOME_COLLECTION_CHOICES,
        default='NO'
        )
    is_active = models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    


#--------------------------------------#
# Staff model
#--------------------------------------#

class StaffProfile(models.Model):
    DESIGNATION_CHOICES = (
        ('TECH', 'Lab Technician'),
        ('PHLEB', 'Phlebotomist'),
        ('RECEP', 'Receptionist'),
        ('COUNS', 'Counselor'),
        ('OTHER', 'Other'),
    )
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='staffprofile'
        )
    lab = models.ForeignKey(
        Lab,
        on_delete=models.CASCADE
        )
    staff_id = models.CharField(max_length=255,unique=True)
    full_name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=15)
    designation = models.CharField(
        max_length=10,
        choices=DESIGNATION_CHOICES,
        blank=True,
        null=True
    )
    other_designation = models.CharField(max_length=50, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.staff_id} -{self.full_name}'
    
class BookingSlot(models.Model):

    COLLECTION_CHOICES = (
        ('LAB', 'Lab Visit'),
        ('HOME', 'Home Collection'),
    )

    RESOURCE_TYPE_CHOICES = (
        ('EXCLUSIVE', 'Exclusive Resource'),  # scan / machine
        ('SHARED', 'Shared Resource'),        # blood collection,etc
    )

    SLOT_CHOICES = (
        ('10-11', '10:00 AM - 11:00 AM'),
        ('11-12', '11:00 AM - 12:00 PM'),
        ('13-14', '1:00 PM - 2:00 PM'),
        ('14-15', '2:00 PM - 3:00 PM'),
    )

    date = models.DateField()
    time_slot = models.CharField(max_length=10, choices=SLOT_CHOICES)

    collection_type = models.CharField(
        max_length=10,
        choices=COLLECTION_CHOICES
    )

    resource_type = models.CharField(
        max_length=10,
        choices=RESOURCE_TYPE_CHOICES
    )

    max_bookings = models.PositiveIntegerField(default=1)
    booked_count = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    def is_available(self):
        return self.booked_count < self.max_bookings
    
    def __str__(self):
        return f'{self.get_time_slot_display()} -  {self.collection_type}'
    
    #avoid duplicate slot lab-shared slots for same time
    class Meta:
        unique_together = (
            'date',
            'time_slot',
            'collection_type',
            'resource_type',
        )
        ordering = ['-date', '-time_slot']

class Booking(models.Model):

    slot =models.ForeignKey(
        BookingSlot,
        on_delete=models.PROTECT, #Slot should not be deleted if bookings exist
        null=True,
        blank=True,
        related_name='bookings'
    )
    
    STATUS_CHOICES = (
        ('PENDING','Pending'),
        ('CONFIRMED','Confirmed'),
        ('SAMPLE COLLECTED','Sample Collected'),
        ('REPORT UPLOADED', 'Report Uploaded'),
        ('COMPLETED','Completed'),
        ('CANCELLED','Cancelled'),
        ('EXPIRED', 'Expired'),
    )

    COLLECTION_CHOICES = (
        ('HOME','Home Collection'),
        ('LAB','Lab Visit'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('PENDING','Pending'),
        ('SUCCESS','Success'),
        ('REFUNDED', 'Refunded'),
        ('FAILED','Failed'),
    )

    #Relations

    #if user delete booking deleted
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = 'bookings'
    )

    #
    package = models.ForeignKey(
        LabPackage,
        on_delete=models.PROTECT, #safeyt feature to preven deleting a package if booking attached to it
        related_name='bookings'
    )

    #appointment detaisl

    preferred_date = models.DateField()

    collection_type = models.CharField(
        max_length=10,
        choices=COLLECTION_CHOICES,
        default='LAB'
    )
    amount = models.PositiveIntegerField(default=0)

    #BOOKING LIFECYCLE
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    #MOCK PAYMENT
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING'
    )

    #Optional notes
    notes = models.TextField(
        null=True,
        blank=True,
        help_text='Patient or lab remarks'
    )

    #Timestamps

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank= True)

    
    def clean(self):
        # preferred_date may be None during form binding
        if self.preferred_date and self.preferred_date < now().date():
            raise ValidationError({
                'preferred_date': 'You cannot book for past dates.'
            })

        # SAFE package check
        if self.package_id and self.collection_type:
            if self.package.home_collection == 'NO' and self.collection_type != 'LAB':
                raise ValidationError({
                    'collection_type': 'Home collection not allowed for this package'
                })
    def can_cancel(self):
        if self.status == 'PENDING':
            return True
        
        if self.status == 'CONFIRMED' and self.payment and self.payment.paid_at:
            return timezone.now() <= self.payment.paid_at + timedelta(minutes=30)
        
        return False
            
    @property
    def lab(self):
        return self.package.lab

    def __str__(self):
        slot_info = self.slot.time_slot if self.slot else "No Slot Assigned"
        # return f'Booking #{self.id} -  {self.patient.email}'
        return f'Booking #{self.id} | {self.preferred_date} {slot_info} -  {self.collection_type}'
    

class Payment(models.Model):

    # 1 Booking ↔ 1 Payment
    booking = models.OneToOneField(
        'Booking',
        on_delete=models.CASCADE,
        related_name='payment'
    )
    lab = models.ForeignKey(
    'Lab',
    on_delete=models.CASCADE,
    related_name='payments'
)

    #1 Patient ↔ Many Payments
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    razorpay_order_id = models.CharField(
        max_length=100,
        blank = True,
        null = True
    )
    razorpay_payment_id = models.CharField(max_length=255,blank = True,null = True,)
    razorpay_signature = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=10,
        choices=(
            ('PENDING', 'Pending'),
            ('SUCCESS', 'Success'),
            ('REFUNDED', 'Refunded'),
            ('FAILED', 'Failed'),
        ),
        default='PENDING'
    )
    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    @property
    def can_be_refunded(self):
        print("Id:", self.id)
        # print("Status:", self.status)
        # print("Now:", timezone.now())
        # print("Created:", self.created_at)
        print("Booking status:", self.booking.status)
        print("payment status:", self.booking.payment.status)
        if self.status != 'SUCCESS' or self.booking.status == 'CANCELLED':
            return False

        refund_deadline = self.created_at + timedelta(hours=24)

        if timezone.now() > refund_deadline:
            return False

        if self.booking.status == 'SAMPLE COLLECTED':
            return False

        return True

    
    # def can_be_refunded(self):
    #     """Returns True if payment is successful and within 24 hours."""
    #     if self.status != 'SUCCESS':
    #         return False
    #     # If created_at + 24 hours is greater than now, it's still refundable
    #     return timezone.now() < (self.created_at + timedelta(hours=24))

    def __str__(self):
        return f'Payment #{self.id} -{self.status}'
    
class TestReport(models.Model):
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='report'
    )
    file = models.FileField(upload_to='reports/')
    uploaded_at =models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report for Booking #{self.booking.id}-{self.booking.patient.patient_profile.first_name} "
    

class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message