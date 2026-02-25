from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin

# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # list_display = ('username', 'email', 'role') 
    pass

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile', 'created_at')  

admin.site.register(Lab)
admin.site.register(LabAdminProfile)
admin.site.register(PackageCategory)
admin.site.register(LabPackage)
admin.site.register(StaffProfile)
admin.site.register(Booking)
admin.site.register(BookingSlot)
admin.site.register(Payment)
admin.site.register(TestReport)
admin.site.register(Notification)

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ('name', 'result_type', 'is_active')
    list_filter = ('result_type', 'is_active')
    search_fields = ('name',)