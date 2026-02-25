from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.
class PatientProfile(models.Model):
    user =  models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField()
    mobile = models.CharField(max_length=13)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.first_name
    
class User(AbstractUser):
    ROLE_CHOICES = (
        ('PATIENT','Patient'),
        ('LAB ADMIN','Lab Admin'),
        ('STAFF','Staff'),
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='PATIENT'
    )
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login, logout, get_user_model
from .models import *
from .forms import RegistrationForm, ContactForm, LoginForm, CustomPasswordResetForm
from .models import *
from django.contrib import messages 
from django.contrib.auth.decorators import login_required



# Create your views here.

def homepage(request):
    return render(request,'index.html')



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

#<!-- Registration form Section -->
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    form = RegistrationForm()
    if request.method == 'POST':
        form = RegistrationForm(request.POST) # Bind data into the RegistrationForm
        if form.is_valid():
            #Access cleaned data
            # first_name = form.cleaned_data['first_name']
            # last_name = form.cleaned_data['last_name']
            # dob = form.cleaned_data['dob']
            # mobile = form.cleaned_data['mobile']
            # email = form.cleaned_data['email']
            # password = form.cleaned_data['password']

            #create auth_user
            user=User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )

            #create patient profile
            PatientProfile.objects.create(
                user=user,
                first_name = form.cleaned_data['first_name'],
                last_name = form.cleaned_data['last_name'],
                dob = form.cleaned_data['dob'],
                mobile = form.cleaned_data['mobile']
            )
            
            messages.success(request,'Registred successfully. Please login with your credentials now')
            return redirect('/login')
            
        
        else:
            messages.error(request,'Unable to register. Please try again')
    else:
        form = RegistrationForm()

    return render(request,'register.html',{
        'form':form
        })


#<!-- Login form Section -->
def login_view(request):
    print('fist')
    if request.user.is_authenticated:
        return redirect_after_login(request.user)
    

    form = LoginForm()
    if request.method == 'POST': 
        print('hi')       
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )

        if user is not None:
            print('hiee') 
            login(request, user)
            return redirect_after_login(user)

    return render(request,'login.html',{
        'form':form
    })

def redirect_after_login(user):
    if user.role =='PATIENT':
        return redirect('patient_dashboard')
    elif user.role == 'LAB_ADMIN':
        return redirect('lab_dashboard')
    else:
        return redirect('home')


#<!-- Reset form Section Start -->

def PasswordResetView(request):
    form = CustomPasswordResetForm()
    if request.method=='POST':
        print('hi')
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user=User.objects.filter(email=email)
            print(user)
            return redirect('home')
        else:
            messages.error(request,'Email id does not exist')
    return render(request,'rest_password.html',{
        'form':form
    })


            


#<!-- Reset form Section End -->

@login_required
def patient_dashboard(request):
    patient = request.user.patient_profile ## from Patient Profile model
    return render(request, 'dashboard/patient/dashboard.html',
        {'patient': patient}
    )

@login_required   
def lab_dashboard(request):
    lab = request.user.labadmin_profile
    return render(request, 'dashboard/lab/dashboard.html',
        {'lab': lab}
    )
   


def packages(request):
    return render(request, 'dashboard/patient/packages.html')

def packages_detail_view(request):
    return render(request, 'dashboard/patient/packages-details.html')

path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='auth/password_reset.html',
             email_template_name='auth/password_reset_email.html',
             form_class=CustomPasswordResetForm
             ),
             name='password_reset'
             ),
    path(
        'password_reset_done',
        auth_views.PasswordResetDoneView.as_view(
            template_name='auth/password_reset_done.html'
        ),
        name='password_reset_done'
    ),


def lab_booking_list(request):
    if request.user.role not in ['LAB_ADMIN','STAFF']:
        return redirect('home')
    
    if request.user.role == 'LAB_ADMIN':
        lab  = get_lab_from_request(request)
    else:
        lab  = request.user.staffprofile.lab

    bookings = Booking.objects.filter(
        package__lab = lab,                           # model relationships form booking->package->lab model
        status__in = ['CONFIRMED','SAMPLE COLLECTED','REPORT UPLOADED','COMPLETED'] # status match 
    ).select_related(
        'patient__patient_profile', #patient in booking model points user wich point to patient profile
        'slot',
        'package'
    ).order_by('preferred_date','slot__time_slot').reverse()  #grab these 3 data in a single trip with a single query like join
    print(lab, type(lab))

    page = Paginator(bookings,5)
    page_number = request.GET.get('page')
    page_obj = page.get_page(page_number)


    return render(request,'lab/booking_list.html',{
        'bookings':page_obj
    })