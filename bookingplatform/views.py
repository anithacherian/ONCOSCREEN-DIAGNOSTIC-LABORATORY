from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login, logout, get_user_model,update_session_auth_hash
from .models import *
from .forms import RegistrationForm, ContactForm, LoginForm, CustomPasswordResetForm,LabAdminRegistrationForm,LabPackageForm,StaffRegistrationForm,PatientProfileForm,BookingForm,LabTestForm,StaffEditForm,BookingSlotForm,MyPasswordChangeForm
from django.contrib.auth.forms import PasswordChangeForm
from .models import *
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from .forms import CustomPasswordResetForm
from .utils import calculate_age,get_lab_from_request
import razorpay,calendar
from django.conf import settings
from django.http import JsonResponse
import json 
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta,datetime
from django.db.models.deletion import ProtectedError
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.db.models import Count
from django.utils.dateparse import parse_date
from django.db.models import Sum,Count
from django.utils.timezone import now
from django.db.models import Q
from bookingplatform.utils import expire_pending_bookings,process_refund
import csv
from django.http import HttpResponse
from decimal import Decimal


CANCEL_WINDOW_MINUTES = 30



# Create your views here.

def homepage(request):
    category = PackageCategory.objects.all().order_by('?')[:6]
    return render(request, 'index.html',{
        'categorys':category
    })   



def aboutpage(request):
    return render(request,'about.html')

def servicepage(request):
    return render(request,'services.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def contactpage(request):
    form = ContactForm() 
    error = None
    success = None 
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            #Access cleaned data
            contact_name = form.cleaned_data['contact_name']
            contact_email = form.cleaned_data['contact_email']
            contact_subject = form.cleaned_data['contact_subject']
            contact_message = form.cleaned_data['contact_message']
            
            success = 'Your message has been sent successfully.'
            form = ContactForm() # reset form
        
        else:
            error = "Unable to send. Please try again"
    else:
        form = ContactForm()
        
    return render(request,'contact.html',{
        'form':form,
        'error': error,
        'success': success
        })

User = get_user_model()

#<!-- Patient Registration form Section -->
def patient_register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    form = RegistrationForm()
    if request.method == 'POST':
        form = RegistrationForm(request.POST) # Bind data into the RegistrationForm
        if form.is_valid():

            #create auth_user
            user=User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            user.role = 'PATIENT'
            user.save()

            #create patient profile
            PatientProfile.objects.create(
                user=user,
                first_name = form.cleaned_data['first_name'],
                last_name = form.cleaned_data['last_name'],
                dob = form.cleaned_data['dob'],
                mobile = form.cleaned_data['mobile']
            )
            
            messages.success(request,'Registred successfully. Please login with your credentials now')
            return redirect('login')
            
        
        else:
            messages.error(request,'Unable to register. Please try again')
    else:
        form = RegistrationForm()

    return render(request,'register.html',{
        'form':form
        })


#<!-- Labadmin Registration form Section -->
def labadmin_register_view(request):
    # Allow only ONE lab admin
    # if LabAdminProfile.objects.exists():
    #     messages.warning (request,'Lad Admin already exists. So login with your credentials')
    #     return redirect('login')

    if not request.user.is_superuser:
        messages.error(request, "Access denied. Only system administrator can create Lab Admin.")
        return redirect_after_login(request.user)
    
    form = LabAdminRegistrationForm()
    if request.method == 'POST':
        form = LabAdminRegistrationForm(request.POST) # Bind data into the LabAdminRegistrationForm
        if form.is_valid():
            print('llll')

            #create auth_user
            user=User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            print(user)
            user.role = 'LAB_ADMIN'
            user.save()

            #create patient profile
            LabAdminProfile.objects.create(
                user=user,
                lab_name=form.cleaned_data['lab_name'],
                mobile=form.cleaned_data['mobile']
                )
            
            messages.success(request,'Lab admin created successfully. Please login with your credentials.')
            return redirect('login')
        else:
            print(form.errors)
            messages.error(request,'Unable to register. Please try again')
    else:
        form = LabAdminRegistrationForm()

    return render(request,'labadmin/register.html',{
        'form':form
        })



#<!-- Login form Section -->
def login_view(request):
    if request.user.is_authenticated:
        return redirect_after_login(request.user)
    

    form = LoginForm()
    if request.method == 'POST':
        
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user =  authenticate(request,username=email,password=password)

            if user is not None:
                login(request, user)
                return redirect_after_login(user)
            else:
                messages.error(request,'Invalid email or password. Please try again')

    return render(request,'login.html',{
        'form':form
    })

def redirect_after_login(user):
    if not user.is_authenticated:
        return redirect('login')
    if user.is_superuser:
        return redirect('/admin/')
    
    if user.role =='PATIENT':
        return redirect('patient_dashboard')
    elif user.role == 'LAB_ADMIN':
        return redirect('lab_dashboard')
    elif user.role == 'STAFF':
        return redirect('staff_dashboard')
    
    return redirect('home')


#<!-- Reset form Section Start -->

# def PasswordResetView(request):
#     print('hiii')
#     form = CustomPasswordResetForm()
#     if request.method=='POST':
#         print('hi')
#         form = CustomPasswordResetForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             user=User.objects.filter(email=email)
#             print(user)
#             return redirect('home')
#         else:
#             messages.error(request,'Email id does not exist')
#     return render(request,'rest_password.html',{
#         'form':form
#     })

class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/password_reset_email.html'
#<!-- Reset form Section End -->


#<!-- Passowrd Change form Section Start -->

@login_required
def change_password(request):
    if request.method == 'POST':
        form = MyPasswordChangeForm(user=request.user,data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request,request.user)
            messages.success(request, "Your password has been updated successfully.")
            
            user = request.user
        
            if user.role == 'PATIENT':
                return redirect('patient_profile')
            elif user.role == 'LAB_ADMIN':
                return redirect('lab_dashboard')
            elif user.role == 'STAFF':
                return redirect('staff_dashboard')
            else:
                return redirect('login')
            
        # messages.error(request, "Uable to change.Please try again")
        
    
        
    else:
        form = MyPasswordChangeForm(user=request.user)

    return render(request,'auth/change_passowrd.html',{
        'form':form
    })
#<!-- Passowrd Change Section End -->

#<!-- Dashboard form Section Start -->

@login_required
def patient_dashboard(request):
    patient = request.user.patient_profile ## from Patient Profile model

    today = timezone.now().date()


    upcoming_test = Booking.objects.filter(
        patient=request.user,
        status='CONFIRMED',
        preferred_date__gte=today,
        expires_at__gt=timezone.now()
        ).count()
    completed_test = Booking.objects.filter(patient=request.user,status='COMPLETED').count()
    report_uploaded = Booking.objects.filter(patient=request.user,status='REPORT UPLOADED').count()
    print(upcoming_test)
    

    return render(request, 'patient/dashboard.html',{
        'patient': patient,
        'upcoming_test':upcoming_test,
        'completed_test':completed_test,
        'report_uploaded':report_uploaded,
        }
    )

@login_required   
def lab_dashboard(request):
    if request.user.role != 'LAB_ADMIN':
        return redirect('home')
    if request.user.role == 'LAB_ADMIN':
        lab  = get_lab_from_request(request)
    
    total_test = Booking.objects.filter(
        package__lab = lab
        ).exclude( 
            status__in = ['PENDING', 'CANCELLED', 'EXPIRED']
            ).count()
    completed_test = Booking.objects.filter(
        package__lab = lab,                           # model relationships form booking->package->lab model
        status__in = ['COMPLETED'] # status match 
    ).count()
    report_send = Booking.objects.filter(
        package__lab = lab,                           # model relationships form booking->package->lab model
        status__in = ['REPORT UPLOADED','COMPLETED'] # status match 
    ).count()
    
    # lab_profile = request.user.labadmin_profile

    return render(request, 'lab/dashboard.html',{
        'lab': lab,
        'total_test':total_test,
        'completed_test':completed_test,
        'report_send':report_send,
        }
    )
#<!-- Dashboard form Section End -->


@login_required   
def staff_dashboard(request):
    if request.user.role != 'STAFF':
        return redirect('home')
    
    staff_profile  = request.user.staffprofile
    count_test=staff_profile.lab
    

    total_test = Booking.objects.filter(
        package__lab = count_test
        ).exclude( 
            status__in = ['PENDING', 'CANCELLED', 'EXPIRED']
            ).count()
    sample_complete = Booking.objects.filter(
        package__lab = count_test,                           # model relationships form booking->package->lab model
        status__in = ['SAMPLE COLLECTED'] # status match 
    ).count()
    report_send = Booking.objects.filter(
        package__lab = count_test,                           # model relationships form booking->package->lab model
        status__in = ['REPORT UPLOADED','COMPLETED'] # status match 
    ).count()
    
    completed_test = Booking.objects.filter(
        package__lab = count_test,
        status__in = ['COMPLETED']
            ).count()
    cancelled_test = Booking.objects.filter(
        package__lab = count_test,                           # model relationships form booking->package->lab model
        status__in = ['CANCELLED'] # status match 
    ).count()
    pending_test = Booking.objects.filter(
        package__lab = count_test,                           # model relationships form booking->package->lab model
        status__in = ['PENDING'] # status match 
    ).count()
    
    

    return render(request, 'staff/dashboard.html',{
        'staff': staff_profile,
        'total_test':total_test,
        'sample_complete':sample_complete,
        'report_send':report_send,
        'completed_test':completed_test,
        'cancelled_test':cancelled_test,
        'pending_test':pending_test,


        }
    )
#<!--Create Staff Section Start -->

def generate_staff_id():
    last_staff = StaffProfile.objects.order_by('id').last()
    next_id = 1 if not last_staff else last_staff.id+1
    return f'STF-{next_id:04d}'

@login_required
def create_staff_view(request):
    if request.user.role != 'LAB_ADMIN':
        messages.error(request,'Unathorised access')
        return redirect('home')
    
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)

        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )

            user.role = 'STAFF'
            user.save()

            #create patient profile
            StaffProfile.objects.create(
                user=user,
                lab=get_lab_from_request(request),
                staff_id=generate_staff_id(),
                full_name=form.cleaned_data['full_name'],
                mobile=form.cleaned_data['mobile']
                )
            print(user)
            
            messages.success(request,'Staff registered successfully. Please login with your credentials.')
            return redirect('login')
        else:
            print(form.errors)
            messages.error(request,'Unable to register. Please try again')
    
    else:
        form =StaffRegistrationForm()

    return render(request,'lab/staff_register.html',{
        'form':form
    })

def staff_view_list(request):
    if request.user.role != 'LAB_ADMIN':
        return redirect('home')
    
    staff = StaffProfile.objects.all()
    page = Paginator(staff,5)
    
    page_number = request.GET.get('page')
    page_obj = page.get_page(page_number)

    return render(request,'lab/lab_staff_view.html',{
        'staffs':page_obj
    })

@login_required
def staff_edit(request,pk): #primary key insted of id
    if request.user.role != 'LAB_ADMIN':
        return redirect('home')
    lab = get_lab_from_request(request)

    staff =  get_object_or_404(
        StaffProfile,
        pk=pk,
        lab=lab
        )

    if request.method == 'POST':
        form = StaffEditForm(request.POST,instance=staff)
        if form.is_valid():
            form.save()

            messages.success(request,'Staff Details Edited Successufully')
            return redirect('staff_view_list')
        
        else:
            messages.error(request,'Unable to edit the staff details. Pleae try again')
            
    else:
        form = StaffEditForm(instance=staff) 


    return render(request,'lab/edit_staff.html',{
        'form':form,
        'staff':staff
    })

@login_required
def staff_delete(request,pk):
    if request.user.role != 'LAB_ADMIN':
        return redirect('home')
    lab = get_lab_from_request(request)    

    staff =  get_object_or_404(
        StaffProfile,
        pk=pk,
        lab=lab
        )
    
    if request.method == 'POST':
        user = staff.user

        if user:
            user.delete()
    
    return redirect('staff_view_list')



#<!-- Staff Section End -->

#<!-- Create Packages Section Start -->

def create_package(request):
    if request.user.role != 'LAB_ADMIN':
        return redirect('home')
    
    if request.method=='POST':
        form = LabPackageForm(request.POST)
        if form.is_valid():
            package = form.save(commit=False) #  Create object in memory (M2M data is NOT saved yet)
            package.lab = get_lab_from_request(request)
            package.save()
            form.save_m2m() #Save the M2M data (like 'tests') using the new ID

            messages.success(request,'Package Added Successfully')
            return redirect('lab_dashboard')
        else:
            print(form.errors)
            messages.error(request,'Unable to Add Package. Please Try Again.')
    else:
        # print(form.errors)        
        form = LabPackageForm()
    
    return render(request,'lab/create_package.html', {'form': form})

        



#<!-- Create Packages Section End -->


#<!-- Packages View Section Start -->

def all_categories_view(request):
    category = PackageCategory.objects.all()


    return render(request, 'category.html',{
        'category':category
    })





def category_packages_view(request,pk):
    category = PackageCategory.objects.get(id=pk)
    print(category)
    
    packages = LabPackage.objects.filter(
        category=category,
        is_active=True
    )
    #apply filters
    gender = request.GET.get('gender')
    age = request.GET.get('age')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if gender:
        packages = packages.filter(
            Q(gender=gender) | Q(gender='BOTH')
        )
        
    if age:
        age = int(age)
        packages = packages.filter(
            Q(min_age__lte=age) | Q(min_age__isnull=True),
            Q(max_age__gte=age) | Q(max_age__isnull=True)
        )

    if min_price:
        packages = packages.filter(price__gte=min_price)

    if max_price:
        packages = packages.filter(price__lte=max_price)

    return render(request, 'category_packages.html',{
    'category': category,
    'packages':packages
    })

def packages_detail_view(request, pk):
    packages = get_object_or_404(
        LabPackage,
        id=pk,
        is_active=True
    )

    category = packages.category   # 👈 get category from package

    return render(request, 'packages_details.html', {
        'package': packages,
        'category': category
    })


# def packages_detail_view(request, pk):
#     package = get_object_or_404(
#         LabPackage,
#         id=pk,
#         is_active=True
#     )

#     category = package.category   # 👈 get category from package

#     return render(request, 'packages_details.html', {
#         'package': package,
#         'category': category
    # })



#<!-- Packages Section End -->

#<!-- LABADMIN View Packages Section  START -->
@login_required
def lab_packages_list_view(request):
    if request.user.role != 'LAB_ADMIN':
        return redirect('home')

    lab = get_lab_from_request(request)

    # Base queryset
    packages = LabPackage.objects.filter(
        lab=lab
    ).select_related('category')

    # Filters
    category_id = request.GET.get('category')
    packages_search = request.GET.get('packages', '').strip()

    if category_id:
        packages = packages.filter(category__id=category_id)

    if packages_search:
        packages = packages.filter(name__icontains=packages_search)

    # Pagination
    paginator = Paginator(packages, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Global categories
    categories = PackageCategory.objects.all()

    return render(
        request,
        'lab/lab_view_packages_list.html',
        {
            'package_page': page_obj,
            'categories': categories,
            'selected_category': category_id,
            'packages_search': packages_search,
        }
    )


@login_required
def lab_packages_edit(request,pk): #primary key insted of id
    if request.user.role != 'LAB_ADMIN':
        return redirect('home')
    
    lab = get_lab_from_request(request) 

    packages =  get_object_or_404(
        LabPackage,
        pk=pk,
        lab=lab
        )
    category = PackageCategory.objects.all()

    if request.method == 'POST':
        form = LabPackageForm(request.POST,instance=packages)
        if form.is_valid():
            form.save()

            messages.success(request,'Package Edited Successufully')
            return redirect('lab_view_package')
        
        else:
            messages.error(request,'Unable to edit the package. Pleae try again')

    else:
        form = LabPackageForm(instance=packages)        


    return render(request,'lab/edit_package.html',{
        'form':form,
        'categorys':category
    })

@login_required
def lab_packages_delete(request,package_id):
    if request.user.role != 'LAB_ADMIN':
        return redirect('home')
    
    lab = get_lab_from_request(request)    

    packages =  get_object_or_404(
        LabPackage,
        id=package_id,
        lab=lab
        )
    try:
        if request.method == 'POST':
            packages.delete()        
            messages.success(request, "Package deleted successfully.")

    except ProtectedError:
        messages.error(
            request,
            "This package cannot be deleted because it has existing bookings. "
            "You can deactivate it instead."
        )
    
    
    return redirect('lab_view_package')
    
#<!--LABADMIN View  Packages Section End -->

#<!--LABADMIN View  Lab Test Section STart -->
@login_required
def lab_test_list(request):
    lab = get_lab_from_request(request)

    labtest = LabTest.objects.all()
    search_query = request.GET.get('labtest', '').strip()


    if search_query:
        labtest = labtest.filter(name__icontains=search_query)

    page = Paginator(labtest,5)
    page_number = request.GET.get('page')
    page_obj = page.get_page(page_number)


    return render(request,'lab/lab_labtest_list.html',
                  {
                      'labtest_page':page_obj,
                      'search_query':search_query,

                  })
@login_required
def lab_test_create(request):
    if request.user.role != 'LAB_ADMIN':
        return redirect('home')
    
    lab = get_lab_from_request(request)

    if request.method == 'POST':
        form = LabTestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,'Lab test added successfully'
            )
            return redirect('lab_test_list'
            )
        else:
            for field,errors in form.errors.items():
                for error in errors:
                    if 'already exists' in error:
                        messages.error(request, f"Duplicate entry: {error}")
                    else:
                        messages.error(request,f"Error in {field}: {error}")

                

    else:
        form = LabTestForm()

    return render(request,'lab/create_test.html',{
        'form':form
    })

@login_required
def lab_test_edit(request,pk):
    if request.user.role != 'LAB_ADMIN':
        return redirect('home')
    
    lab = get_lab_from_request(request)

    test=get_object_or_404(LabTest,pk=pk)

    if request.method == 'POST':
        form = LabTestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()

            messages.success(request, 'Test updated successfully')
            return redirect('lab_test_list')
        
    else:
        form = LabTestForm(instance=test)

    return render(request,'lab/edit_test.html',{
        'form':form,
        'test':test
    })

@login_required
def lab_test_delete(request,pk):
    if request.user.role != 'LAB_ADMIN':
        return redirect('home')

    test = get_object_or_404(LabTest, pk=pk)
    
    if test.packages.exists():
        messages.error( request, 'This test is already used in a package and cannot be deleted.' )
        return redirect('lab_test_list')
    
    if request.method == 'POST':
        test.delete()
        messages.success(request, 'Test deleted successfully')
    
    return redirect('lab_test_list')
        
#<!--LABADMIN View  Lab Test Section End -->

#<!--PATIENT PROFILE Section START -->
@login_required
def patient_profile(request):
    profile = request.user.patient_profile



    return render(request,'patient/my_profile.html',{
        'profile':profile
    })

#
@login_required
def patient_profile_edit(request):
    if request.user.role != 'PATIENT':
        return redirect('home')
    
    profile = request.user.patient_profile

    if request.method=='POST':
        form = PatientProfileForm(request.POST,instance=profile)
        if form.is_valid():
            form.save()

            messages.success(request,'Profile Updated Successufully')
            return redirect('patient_profile')
        else:
            messages.success(request,'Profile Unable to updated. Please Try again')
    else:
        form = PatientProfileForm(instance=profile)

    return render(request,'patient/edit_patient_profile.html',{
        'form':form
        })

   
#<!--PATIENT PROFILE Section End -->

#<!--Booking Section Start -->
def book_package(request, pk=None):
    # 🔐 Auth & Role check (unchanged)
    if not request.user.is_authenticated or request.user.role != 'PATIENT':
        messages.error(request,'Please login as patient to book a test.')
        return redirect('login')

    profile = request.user.patient_profile
    if not profile.gender or not profile.address or not profile.dob:
        messages.warning(request, 'Please complete your profile before booking.')
        return redirect('edit_patient_profile')

    # --- 1. INITIAL SETUP ---
    package = None
    initial = {}

    # Pre-load package if pk is in URL (e.g., /booking/new/2/)
    if pk:
        package = get_object_or_404(LabPackage, pk=pk, is_active=True)
        initial['package'] = package
        if package.home_collection == 'NO':
            initial['collection_type'] = 'LAB'

    if request.method == 'POST':
        # --- 2. HANDLE DATA ---
        # post_data = request.POST.copy()
        
        # # If pk exists, ensure the package ID is in the data 
        # # (Fixes the issue where disabled fields don't submit)
            
        # if pk and 'package' not in post_data:
        #     post_data['package'] = str(pk)
        form = BookingForm(request.POST)

        # --- 3. SLOT CHECK LOGIC ---
        if 'check_slots' in request.POST:
            if pk:
                form.fields['package'].disabled = True
                form.initial['package'] = package 

            if package and package.home_collection == 'NO':
                    form.initial['collection_type'] = 'LAB'
            
            # We return early here to show available slots
            return render(request, 'patient/book_package.html', {
                'form': form,
                'package': package,
                'package_locked': True,
                'package_home_map': form.package_home_map, # Required for JS
                'today': timezone.now().date(),
            })

        # --- 4. FINAL BOOKING LOGIC ---
        if form.is_valid():
            booking = form.save(commit=False)
            booking.patient = request.user
            
            # Use the package we loaded at the start
            selected_package = booking.package
            selected_slot = booking.slot

            # Validate Age
            age = calculate_age(profile.dob)
            if age < selected_package.min_age or (selected_package.max_age and age > selected_package.max_age):
                messages.error(request, 'You are not eligible for this package based on age.')
                return redirect('edit_patient_profile')

            # Force business logic (Safety check)
            if selected_package.home_collection == 'NO':
                booking.collection_type = 'LAB'

            booking.amount = selected_package.price

            try:
                with transaction.atomic():
                    booking.status = 'PENDING'
                    booking.expires_at = timezone.now() + timedelta(minutes=15)
                    
                    slot = BookingSlot.objects.select_for_update().get(pk=selected_slot.pk)
                    if slot.booked_count >= slot.max_bookings:
                        messages.error(request, 'Selected slot is already full.')
                        return redirect(request.path)

                    slot.booked_count = F('booked_count') + 1
                    slot.save(update_fields=['booked_count'])
                    booking.save()

                    Payment.objects.create(
                        booking=booking,
                        lab=selected_package.lab,
                        patient=request.user,
                        amount=booking.amount,
                        status='PENDING'
                    )
                return redirect('payment', booking_id=booking.id)

            except Exception as e:
                print(f"DEBUG ERROR: {e}") 
                messages.error(request, 'Slot booking failed. Please try again.')
                return redirect(request.path)
        
        else:
            print("FORM ERRORS:", form.errors.as_data())
            # Form invalid path (e.g. missing date)
            if pk:
                form.fields['package'].disabled = True
                form.initial['package'] = package
    
    else:
        # --- 5. GET REQUEST ---
        form = BookingForm(initial=initial)
        if pk:
            form.fields['package'].disabled = True

    # Common return for GET and failed POST
    return render(request, 'patient/book_package.html', {
        'form': form,
        'package': package,
        'today': timezone.now().date(),
        'package_locked': bool(pk),
        'package_home_map': form.package_home_map,
    })

#<!--Booking Section End -->
@login_required
def payment(request,booking_id):
    if not request.user.is_authenticated:
        return redirect('home')

    if request.user.role != 'PATIENT':
        return redirect('home')
    
    now = timezone.now()
    today = now.date()
   
    
    booking = get_object_or_404(Booking, pk=booking_id, patient=request.user)

     # NEW: If already paid or confirmed, send them away
    if booking.status == 'CONFIRMED' or booking.payment_status == 'SUCCESS':
        messages.info(request, "You have already paid for this booking.")
        return redirect('my_bookings')

    expire_pending_bookings()
    booking.refresh_from_db()

    if booking.status == 'EXPIRED':
        messages.error(request,'Sorry the booking has expired. Please book again')
        return redirect('book_any_package')

    else:
        print("No payment related to booking")

    

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))

    #create razorpay order

    order = client.order.create({
        'amount': booking.amount * 100,
        'currency':'INR',
        'receipt':f'booking_{booking.id}',
        'payment_capture':1
    })

    booking.razorpay_order_id = order['id']
    booking.save()
    print('pppp')

    return render(request,'patient/payment.html',{
        'booking':booking,
        'razorpay_key':settings.RAZORPAY_KEY_ID,
        'order_id':order['id']
    })

@csrf_exempt
def payment_success(request, booking_id):
    if not request.user.is_authenticated or request.user.role != 'PATIENT':
        return JsonResponse({'error': 'Unauthorized'}, status=403)    
    
    # 1. FETCH THE BOOKING FIRST (This fixes the UnboundLocalError)
    try:
        booking = Booking.objects.get(pk=booking_id, patient=request.user)
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)

    # 2. NOW you can check the status
    if booking.status == 'EXPIRED':
        return JsonResponse({'error': 'Booking expired'}, status=400)
    
    # 3. Process the JSON data
    try:
        data = json.loads(request.body)
        
        with transaction.atomic():
            payment = booking.payment # OneToOne relation
            payment.status = 'SUCCESS'
            payment.paid_at = timezone.now()
            payment.razorpay_payment_id = data.get('razorpay_payment_id')
            payment.razorpay_order_id = data.get('razorpay_order_id')
            payment.razorpay_signature = data.get('razorpay_signature')
            payment.save()

            booking.status = 'CONFIRMED'
            booking.payment_status = 'SUCCESS'
            booking.save()
            
        return JsonResponse({"status": "ok"})
        
    except Exception as e:
        print(f"ERROR: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def payment_failed(request, booking_id):
    if not request.user.is_authenticated or request.user.role != 'PATIENT':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    data = json.loads(request.body)

    booking = Booking.objects.get(
        pk=booking_id,
        patient=request.user
    )
    payment = booking.payment # OneToOne relation
    payment.status = 'FAILED'
    payment.save(update_fields=['status'])

    booking.payment_status = 'FAILED'
    booking.save(update_fields=['payment_status'])

    return JsonResponse({
        "status": "failed",
        "message": "Payment was cancelled or failed"
    })




# bookings list
@login_required
def my_bookings(request):
    if not request.user.is_authenticated:
        return redirect('home')

    if request.user.role != 'PATIENT':
        return redirect('home')

    now = timezone.now()
    today = now.date()
    expire_pending_bookings()

    #  AUTO-EXPIRE PENDING BOOKINGS (TIME-BASED)
    

    bookings = Booking.objects.filter(
        patient=request.user
    ).order_by('-created_at')

    paginator = Paginator(bookings, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'patient/booking_list.html', {
        'bookings': page_obj,
        'today': today,   # 👈 REQUIRED for template
        'now': now,
    })


# cancel booking
@login_required
def cancel_booking(request,booking_id):
    if not request.user.is_authenticated:
        return redirect('home')

    if request.user.role != 'PATIENT':
        return redirect('home')
     
    booking = get_object_or_404(Booking, pk=booking_id,patient=request.user)
    if request.method == 'POST':
        print('ssss')

        if booking.status not in ['PENDING','CONFIRMED']:
            messages.error(request,'This booking cannot be cancelled')
            return redirect('my_bookings')
        print(booking.status)

        if booking.status == 'CONFIRMED':
            payment = booking.payment
            
            if not payment.paid_at:
                messages.error(request,'Cancellation window expired')
                return redirect('my_bookings')
            
            cancel_deadline = payment.paid_at + timedelta(minutes=CANCEL_WINDOW_MINUTES)

            if timezone.now() > cancel_deadline:
                messages.error(request,'Cancellation is allowed only within 30 minutes after payment.')
                return redirect('my_bookings')

        
        with transaction.atomic():
            if booking.slot:
                slot = BookingSlot.objects.select_for_update().get(pk=booking.slot.pk)
                slot.booked_count = F('booked_count')-1
                slot.save(update_fields=['booked_count'])

            booking.status = 'CANCELLED'
            booking.save(update_fields=['status'])
        
        messages.success(request,'Booking cancelled successfully')
        return redirect('my_bookings')
    
    return redirect('my_bookings')

# view bookings by lab staff and lab admin
@login_required
def lab_booking_list(request):
    if request.user.role not in ['LAB_ADMIN','STAFF']:
        return redirect('home')
    
    if request.user.role == 'LAB_ADMIN':
        lab  = get_lab_from_request(request)
    else:
        lab  = request.user.staffprofile.lab

    bookings = Booking.objects.filter(
        package__lab = lab).exclude(
        status__in= ['PENDING', 'CANCELLED', 'EXPIRED'] # status match 
    )

    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if status:
        bookings = bookings.filter(status=status)

    if start_date:
        bookings = bookings.filter(created_at__date__gte=parse_date(start_date))

    if end_date:
        bookings = bookings.filter(created_at__date__lte=parse_date(end_date))

    print("Status from URL:", status)

    
    bookings = bookings.select_related(
        'patient__patient_profile', #patient in booking model points user wich point to patient profile
        'slot',
        'package'
    ).order_by('preferred_date','slot__time_slot').reverse()  #grab these 3 data in a single trip with a single query like join
   
    # print(lab, type(lab))

    page = Paginator(bookings,5)
    page_number = request.GET.get('page')
    page_obj = page.get_page(page_number)


    return render(request,'lab/booking_list.html',{
        'bookings':page_obj,
        'status':status,
        'start_date':start_date or '',
        'end_date':end_date or '',
    })

#mark_sample_collected by lad admin and lab staff

def mark_sample_collected(request,pk):
    user = request.user

    if request.user.role not in ['LAB_ADMIN','STAFF']:
        messages.error(request, "You are not authorized to perform this action.")
        return redirect('home')
    
    if user.role == 'LAB_ADMIN':
        lab = user.labadmin_profile.lab
    else:
        lab = user.staffprofile.lab

    booking = get_object_or_404(
        Booking,
        pk=pk,
        package__lab = lab,
        status='CONFIRMED'
    )

    #update when requierd
    booking.status = 'SAMPLE COLLECTED'
    booking.updated_at = timezone.now()
    booking.save(update_fields=['status','updated_at'])

    messages.success(request,f"Sample collected for {booking.patient.patient_profile.first_name}.")

    return redirect('lab_booking_list')
    
#slot add, edit ,delete by lad admin----------------
@login_required
def create_slot(request):
    if request.user.role != 'LAB_ADMIN':
        messages.error(request,'Access denied')
        return redirect('home')
    
    if request.method == 'POST':
        form = BookingSlotForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,'Slot added successfully')
            return redirect('slot_list')
        
    else:
        form = BookingSlotForm()
        print("Form Errors:", form.errors.as_data())

    return render(request,'lab/slot_form.html',{
        'form':form,
        'title':'Create a Slot',
        'is_edit':False
    })

@login_required
def edit_slot(request,pk):
    if request.user.role != 'LAB_ADMIN':
        messages.error(request,'Access denied')
        return redirect('home')
    
    slot = get_object_or_404(BookingSlot,pk=pk)

    if request.method == 'POST':
        form = BookingSlotForm(request.POST,instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request,'Slot updated successfully')
            return redirect('slot_list')
        
    else:
        form = BookingSlotForm(instance=slot)

        
    return render(request, 'lab/slot_form.html',{
            'form':form,
            'slot':slot,
            'title':'Edit Slot',
            'is_edit':True,
            'slot':slot,
        })
    
@login_required
def slot_list(request):
    if request.user.role != 'LAB_ADMIN':
        messages.error(request,'Access denied')
        return redirect('home')
    
    slots = BookingSlot.objects.all()

    # Get filter values
    date_filter = request.GET.get('date')
    collection_filter = request.GET.get('collection_type')
    resource_filter = request.GET.get('resource_type')
    active_filter = request.GET.get('is_active')
    available_filter = request.GET.get('available')

    if date_filter:
        slots = slots.filter(date=date_filter)
    if collection_filter:
        collection_filter = slots.filter(collection_filter=collection_filter)
    if resource_filter:
        resource_filter = slots.filter(resource_filter=resource_filter)
    if active_filter:
        active_filter = slots.filter(is_active=active_filter)
    if available_filter == '1':
        slots = slots.filter(booked_count__lt=models.F('max_bookings'))

     # Ordering
    slots = slots.order_by('-date', '-time_slot')

    

    page = Paginator(slots,5)
    page_number = request.GET.get('page')
    page_obj = page.get_page(page_number)
    
    return render(request,'lab/slot_list.html',{
        'slots':page_obj,
        'date_filter': date_filter,
        'collection_filter': collection_filter,
        'resource_filter': resource_filter,
        'active_filter': active_filter,
        'available_filter': available_filter,
    })

@login_required
def delete_or_disable_slot(request,pk):
    if request.user.role != 'LAB_ADMIN':
        return redirect('home')

    slot = get_object_or_404(BookingSlot, pk=pk)
    print(slot.booked_count)

    # bookings = slot.bookings.all()
    # print("Bookings using this slot:")
    # for b in bookings:
    #     print(f"Booking ID: {b.id}, Patient: {b.patient.email}")

    active_bookings = slot.bookings.filter(
        status__in=['CONFIRMED', 'SAMPLE_COLLECTED','REPORT UPLOADED','COMPLETED'])
    
    #If slot already used, disable instead of delete
    if active_bookings.exists():
        slot.is_active = False
        slot.save(update_fields=['is_active'])
        messages.info(request,'Slot is disable. Existing booked unaffected')

        return redirect('slot_list')
    
    # 🧹 CLEAN UP inactive bookings FIRST
    slot.bookings.filter(
        status__in=['EXPIRED', 'CANCELLED']
    ).delete()

    slot.delete()
    messages.success(request,'Slot is deleted successfully.')       
    
    return redirect('slot_list')

#------------------------------------------------

#report add, edit ,delete by lad admin

#------------------------------------------------
@login_required
def upload_test_report(request,pk):
    if request.user.role not in['LAB_ADMIN','STAFF']:
        messages.error(request,'You are not authorized to upload reports')
        return redirect('home')
    
    lab = get_lab_from_request(request)

    
    booking = get_object_or_404(
        Booking,
        pk=pk,
        package__lab=lab,
        status__in=['SAMPLE COLLECTED','REPORT UPLOADED','COMPLETED']
    )

    if request.method == 'POST':
        if 'report_file' not in request.FILES:
            messages.error(request,'Please select a file')
            return redirect(request.META.get('HTTP_REFERER', 'lab_booking_list'))
        
        uploaded_file = request.FILES['report_file']
        
        report,created = TestReport.objects.get_or_create(booking=booking)
        report.file = uploaded_file
        report.save()
        Notification.objects.create(
            user=booking.patient,
            message = f'Your test report for {booking.package.name} is ready to download'
        )
        if created: #only for first upload not reuploads
            send_mail(
                subject= 'Your test report is ready',
                message=(
                    f'Hello {booking.patient.patient_profile.first_name} {booking.patient.patient_profile.last_name} or {booking.patient.email},\n\n'
                    f'Your test report for "{booking.package.name}" is now available.\n'
                    f"Please login to your account to download the report.\n\n"
                    f"Regards,\nOncoScreen Diagnostics"
                ),
                from_email=None,   # uses DEFAULT_FROM_EMAIL
                recipient_list=[booking.patient.email],
                fail_silently=True,
            )

        booking.status = 'REPORT UPLOADED'
        booking.save(update_fields=['status'])

        if created:
            messages.success(request,'Report uploaded successfully')
        else:
            messages.success(request,'Report updated successfully')
        
        return redirect('lab_booking_list')
    
    return redirect('lab_booking_list')



    
   
@login_required
def mark_booking_completed(request,pk):
    if request.user.role not in ['LAB_ADMIN']:
        messages.error(request, 'Not authorized')
        return redirect('home')
    
    lab = get_lab_from_request(request)

    booking = get_object_or_404(
        Booking,
        pk=pk,
        package__lab=lab,
        status='REPORT UPLOADED'
    )

    booking.status = 'COMPLETED'
    booking.save(update_fields=['status'])

    messages.success(request,'Booking marked as completed')

    return redirect('lab_booking_list')

#------------------------------------------#
# NOTFFICATION MAIL
#------------------------------------------#
@login_required
def my_notifications(request):
    if request.user.role != 'PATIENT':
        return redirect('home')
    
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    notifications = request.user.notifications.all().order_by('-created_at')
    page = Paginator(notifications,5)
    
    page_number = request.GET.get('page')
    page_obj = page.get_page(page_number)

    return render(request, 'patient/notifications.html', {
        'notifications': page_obj
    })

#------------------------------------------#
# PAYMENT MONITOR BY LAB ADMIN
# SEARCH FILTER
# EXPORT CSV
#------------------------------------------#
@login_required
def lab_payment_list(request):
    chart_type = request.GET.get('chart', 'daily')  
    lab = get_lab_from_request(request)

    expire_pending_bookings(lab=lab)
    payments = Payment.objects.filter(lab=lab)

    #filter
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_query = request.GET.get('search')

    if status:
        payments = payments.filter(status=status)

    if start_date:
        payments = payments.filter(created_at__date__gte=parse_date(start_date))

    if end_date:
        payments = payments.filter(created_at__date__lte=parse_date(end_date))

    if search_query:
        payments= payments.filter(
            Q(patient__email__icontains=search_query) |
            Q(booking__id__icontains=search_query) 
            
        )

    payments = payments.select_related('booking','patient').order_by('-created_at')

    if 'export' in request.GET:
        filename = f'payments_{datetime.now().strftime("%Y%m%d")}.csv'
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"' #download as csv insted of displying as text
        
        writer = csv.writer(response)

        #header row
        writer.writerow([
            "Booking ID",
            "Patient Email",
            "Amount",
            "Status",
            "Razorpay Order ID",
            "Razorpay Payment ID",
            "Paid At",
            "Created At",
        ])

        total_amount = Decimal('0.00')
        # Optional: Print the count to your console to debug while testing
        print(f"Found {payments.count()} payments for status {status}")

        for payment in payments:
            try:
                
                current_amount = payment.amount
                total_amount += current_amount 

                # 2. Use .get() or getattr to prevent crashes if relationships are missing then N/A
                booking_id = payment.booking.id if payment.booking else "N/A"
                patient_email = payment.patient.email if payment.patient else "No Email"

                writer.writerow([
                    booking_id,
                    patient_email,
                    current_amount,
                    payment.status,
                    payment.razorpay_order_id or '',
                    payment.razorpay_payment_id or '',
                    payment.paid_at.strftime('%Y-%m-%d %H:%M') if payment.paid_at else '',
                    payment.created_at.strftime('%Y-%m-%d %H:%M') if payment.created_at else '',

                ])
                #add total row

            except Exception as e:
                print(f"Error on Row {payment.id}: {str(e)}")

        writer.writerow([])
        writer.writerow(['','TOTAL',total_amount])


        return response
    
    

    stats = payments.values('status').annotate(total=Count('id')).order_by('status')

    #total revenuew
    total_revenue = payments.filter(status='SUCCESS').aggregate(total=Sum('amount'))['total'] or 0

    #Today collection
    today = timezone.now().date()
    today_collection = payments.filter(
        status='SUCCESS',
        created_at__date = today
    ).aggregate(total=Sum('amount'))['total']or 0


    #Pending Count
    pending_count = payments.filter(status='PENDING').count()

    failed_count = payments.filter(status='FAILED').count()
    #daily revneue
    labels = []
    revenues = []
    
    if chart_type == 'monthly':
        # Last 6 months
        for i in range(5, -1, -1):
            month_date = (today.replace(day=1) - timedelta(days=30*i))
            month_start = month_date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1)

            total = (
                Payment.objects.filter(
                    lab=lab,
                    status='SUCCESS',
                    created_at__gte=month_start,
                    created_at__lt=month_end
                ).aggregate(total=Sum('amount'))['total'] or 0
            )

            labels.append(calendar.month_abbr[month_start.month])
            revenues.append(float(total))

    else:
        # Default: Daily (Last 7 Days)
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)

            total = (
                Payment.objects.filter(
                    lab=lab,
                    status='SUCCESS',
                    created_at__date=day
                ).aggregate(total=Sum('amount'))['total'] or 0
            )

            labels.append(day.strftime("%d %b"))
            revenues.append(float(total))

    
    
    page = Paginator(payments,5)
    
    page_number = request.GET.get('page',1) #Get the page number from the URL (?page=2)


    #Get the correct page from the paginator

    page_obj = page.get_page(page_number)

    return render(request,'lab/payment_list.html',{
        'payments':page_obj,
        'stats':stats,
        'status_selected':status,
        'start_date':start_date or '',
        'end_date':end_date or '',
        'total_revenue': total_revenue,
        'today_collection': today_collection,
        'pending_count': pending_count,
        'failed_count': failed_count,
        'labels': labels,
        'revenues': revenues,
        'chart_type':chart_type
        # 'months': months, #for monthly revenue
        # 'revenues': revenues, #for monthly revenue

    })


#-----------------------------------------#
#REFUND AMOUNT
#-----------------------------------------#
#labadmin
@login_required
def refund_payment(request,pk):
    lab = get_lab_from_request(request)

    payment = get_object_or_404(Payment,pk=pk,lab=lab)

    #safety check

    if payment.status != 'SUCCESS':
        messages.error(request,'Refund not allowed')
        return redirect('lab_payment_list')
    
    booking = payment.booking

    #check 24hrs to show no refund allowed
    time_threshold = payment.created_at + timedelta(hours=24)
    if timezone.now()> time_threshold:
        messages.error(request,'Refund expired since 24hrs passed')
        return redirect('lab_payment_list')

    if request.method == 'POST':
        
        success,error = process_refund(payment)

        if success:
            messages.success(request, "Payment refunded successfully.")
            return redirect('lab_payment_list')
        

        messages.error(request, f"Refund failed: {error}")
        return redirect('lab_payment_list')
        
    
    return render(request, 'lab/payment_list.html', {
        'payment': payment
    })

#patient refund
@login_required
def patient_refund_payment(request,pk):
    if not request.user.is_authenticated or request.user.role != 'PATIENT':
        messages.error(request,'Please login as patient to book a test.')
        return redirect('login')

    profile = request.user.patient_profile

    payment = get_object_or_404(Payment,pk=pk,patient=request.user)

    #safety check

    
    booking = payment.booking

    if not payment.can_be_refunded:
        messages.error(request,'Refund not allowed')
        return redirect('my_bookings')



    if request.method == 'POST':
        
        success,error = process_refund(payment)

        if success:
            messages.success(request, "Payment refunded successfully.")
            return redirect('my_bookings')
        

        messages.error(request, f"Refund failed: {error}")
        return redirect('my_bookings')
        
    
    return render(request, 'patient/booking_list.html', {
        'payment': payment
    })


#-----------------------------------------#
#FILTER PACKAGE BY USER
#-----------------------------------------#
def search_package_list(request):

    packages = LabPackage.objects.filter(is_active=True)
    category_id = request.GET.get('category')
    gender = request.GET.get('gender')
    age = request.GET.get('age')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    #category filter

    if category_id:
        packages = packages.filter(category_id=category_id)
    if gender:
        packages = packages.filter(
            Q(gender=gender) | Q(gender='BOTH')
        )

    if age:
        try:
            age=int(age)
            packages = packages.filter(
                Q(min_age__lte=age) | Q(min_age__isnull=True),
                Q(max_age__gte=age) | Q(max_age__isnull=True)
            )
        except ValueError:
            pass #ignore invalid age input
    
    if min_price:
        packages = packages.filter(price__gte=Decimal(min_price))
    if max_price:
        packages = packages.filter(price__gte=Decimal(max_price))
        
    
    return render(request,"package_list.html", {
         "packages": packages
    })
