from django import forms
from django.contrib.auth import get_user_model
import re
from django.core.validators import RegexValidator
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm,PasswordChangeForm
from .models import LabPackage,PatientProfile,Booking,LabTest,BookingSlot,StaffProfile
from ckeditor.widgets import CKEditorWidget
from django.utils.timezone import now
from django.db.models import F


#<!-- Contact form Section -->
class ContactForm(forms.Form):
    contact_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class':'form-control',
            'placeholder':'Your Name'
            })
        )
    contact_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class':'form-control',
            'placeholder':'Your Email'
            })
            )
    contact_subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class':'form-control',
            'placeholder':'Subject',
        })
    )
    contact_message = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={
            'class':'form-control',
            'placeholder': 'Message',
            'rows':5
        })
    )


#<!-- Registration form Section -->

mobile_validator = RegexValidator(
    regex = r'^[6-9]\d{9}$',
    message = 'Enter 10 digit mobile number'

)

User = get_user_model()
class RegistrationForm(forms.ModelForm):
    #fiels not in auth user(email,password)
    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your First Name'
            })
        )
    
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Last Name'
            })
        )
    
    dob = forms.DateField(
        widget=forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        )
    
    mobile = forms.CharField(
        validators=[mobile_validator],
        widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Mobile',
                'required': 'required',
                'pattern': '[6-9]{1}[0-9]{9}',
                'title': 'Enter a valid 10-digit mobile number',
                'inputmode': 'numeric',
                'maxlength': '10'
            })
        )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Password',
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'right',
                'title': 'Password must has minimum 8 character, 1 uppercase,1 number & 1 special character'
            })
        )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Password'
            })
        )
    
    class Meta:
        model = User #registr form is linked to user table
        fields = ['email','password'] #auth user fields only here
        widgets = {
            'email' : forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email',
                'required': True
            })
        }


    #password match validation
    def clean(self): #used when you want to validate more than one field together
        cleaned_data =  super().clean() #Collects all valid field values& Puts them into a dictionary called cleaned_data
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match')
        return cleaned_data 
        
    #unique email address validation
    def clean_email(self):
        email = self.cleaned_data.get('email')  #retive safe data after validation 
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered')
        return email
    
    #condition password
    def clean_password(self):
        password = self.cleaned_data.get('password')

        if len(password) < 8:
            raise forms.ValidationError('Password must be atleast 8 characters')
        if not re.search(r'[A-Z]',password):
            raise forms.ValidationError('Password must contain atleast one uppercase letter')
        if not re.search(r'\d',password):
            raise forms.ValidationError('Password must contain atleast one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]',password):
            raise forms.ValidationError('Password must containt 1 special character')
        
        return password
    

    
#<!-- Registration form Section End -->

#<!-- Login form Section Start -->
class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class':'form-control',
            'placeholder':'Your Email'
        })
    )
    password = forms.CharField(
        max_length=25,
        widget=forms.PasswordInput(attrs={
            'class':'form-control',
            'placeholder':'Your Password'
        })
    )
#<!-- Login form Section End -->

#<!-- Lab Admn Registration form Section Start -->

class LabAdminRegistrationForm(forms.ModelForm):

    lab_name = forms.CharField(
    max_length=100,
    widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your First Name'
        })
    )

    mobile = forms.CharField(
        validators=[mobile_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mobile Number',
            'required': 'required',
            'pattern': '[6-9]{1}[0-9]{9}',
            'title': 'Enter a valid 10-digit mobile number',
            'inputmode': 'numeric',
            'maxlength': '10'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    )
    class Meta:
        model = User
        fields = ['email']   # only User fields here

        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match')

        return cleaned_data
    
#<!-- Lab Admn Registration form Section End -->

#<!-- Staff Registration form Section Start -->
class StaffRegistrationForm(forms.ModelForm):
    
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class':'form-control',
            'placeholder': 'Staff full name'
        })
    )

    mobile = forms.CharField(
    validators=[mobile_validator],
    widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Mobile Number',
        'required': 'required',
        'pattern': '[6-9]{1}[0-9]{9}',
        'title': 'Enter a valid 10-digit mobile number',
        'inputmode': 'numeric',
        'maxlength': '10'
    })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class':'form-control',
            'placeholder': 'Password'
        })
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class':'form-control',
            'placeholder': 'Confirm Password'
        })
    )

    class Meta:
        model = User
        fields = ['email']
        widgets ={
            'email': forms.EmailInput(attrs={
                'class':'form-control',
                'placeholder':'Email'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered')
        return email
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError('Password must contain at least one uppercase letter')
        if not re.search(r'\d', password):
            raise forms.ValidationError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError('Password must contain 1 special character')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password !=confirm_password:
            self.add_error('confirm_password','Passwords do not match')
        
        return cleaned_data
    
    def save(self,commit=True,lab=None):
        #create user
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        user.role = 'STAFF'
        user.is_active = True

        if commit:
            user.save()

            #create staff profile
            StaffProfile.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                mobile=self.cleaned_data['mobile'],
                lab=lab
            )
    
        return user

#<!-- Staff Registration form Section End -->

#<!-- Staff Edit form Section Start -->
class StaffEditForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = [
            'full_name',
            'mobile',
            'designation',
            'other_designation',
            'is_active'
        ]

        widgets = {
            'full_name':forms.TextInput(attrs={
                'class':'form-control'
            }),'mobile':forms.TextInput(attrs={
                'class':'form-control'
            }),'designation':forms.Select(attrs={
                'class':'form-control'
            }),'other_designation':forms.TextInput(attrs={
                'class':'form-control'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        designation = cleaned_data.get('designation')
        other_designation = cleaned_data.get('other_designation')

        #prevents empty other field
        if designation == 'OTHER'and not other_designation:
            self.add_error(
                'other_designation',
                'Please specify designation'
            )

        if designation != 'OTHER':
            cleaned_data['other_designation'] = ''

        return cleaned_data

#<!-- Staff Edit form Section End -->



class CustomPasswordResetForm(PasswordResetForm):
    pass
class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control w-100',
            'placeholder': 'Enter new password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control w-100',
            'placeholder': 'Confirm new password'
        })

    
#<!-- Reset form Section End -->

#<!-- Change Password form Section Start -->

class MyPasswordChangeForm(PasswordChangeForm):
    def clean_new_password1(self):
        old_password = self.cleaned_data.get("old_password")
        new_password = self.cleaned_data.get("new_password1")

        if old_password and new_password and old_password == new_password:
            raise forms.ValidationError(
                "Your new password cannot be the same as your old password."
            )
        return new_password


#<!-- Change Password form Section EBD -->

#<!-- Lab Package form form Section Start -->
class LabPackageForm(forms.ModelForm):
    gender = forms.ChoiceField(
        choices=LabPackage._meta.get_field('gender').choices,
        widget=forms.RadioSelect,
        required=True
    )
    intro_description = forms.CharField(
        widget=CKEditorWidget()
    )
    
    risk_factors = forms.CharField(
        widget=CKEditorWidget()
    )
    age_recommendation = forms.CharField(
        widget=CKEditorWidget()
    )
    tests = forms.ModelMultipleChoiceField(
        queryset=LabTest.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = LabPackage
        fields = '__all__'
        exclude = ['lab', 'tests_included']

        widgets ={
            'category' :forms.Select(attrs={
                'class': 'form-select',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder':'Enter package name'
            }),
            'intro_heading': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder':'Enter Intro'
            }),
            'min_age':forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder':'Min age'
            }),
            'max_age':forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder':'Min age'
            }),
            'home_collection': forms.Select(attrs={
                'class': 'form-control'
                }),
            'price': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder':'Enter Price'
            }),
            'report_time': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder':'e.g. 24 hours',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            })
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tests'].queryset = LabTest.objects.filter(is_active=True)


#<!-- Lab Package form form Section End -->
class LabTestForm(forms.ModelForm):
    class Meta:
        model = LabTest
        fields = '__all__'
        
        widgets = {
            'name': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Test name (e.g. Mammogram)'
            }),
            'description': forms.TextInput(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Short description'
            }),
            'result_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

#<!-- Lab Test form form Section Start -->

#<!-- Lab Test form form Section End -->


#<!-- Patient Profile form Section Start -->

class PatientProfileForm(forms.ModelForm):
    gender = forms.ChoiceField(
        choices=PatientProfile._meta.get_field('gender').choices,
        widget=forms.RadioSelect,
        required=True
    )
    class Meta:
        model = PatientProfile
        fields = [
            'first_name',
            'last_name',
            'dob',
            'mobile',
            'gender',
            'address'
        ]

        widgets = {
            'first_name':forms.TextInput(attrs={
                'class':'form-control'
            }),'last_name':forms.TextInput(attrs={
                'class':'form-control'
            }),'dob':forms.DateInput(attrs={
                'type':'date',
                'class':'form-control'
            }),'mobile':forms.TextInput(attrs={
                'class':'form-control'
            }),'address':forms.Textarea(attrs={
                'class':'address',
                'rows':3,
                'placeholder':'Enter full address',
                'required':True
            })
        }

#<!-- Patient Profile form Section End -->

#<!-- Booking form Section End -->
class BookingForm(forms.ModelForm):
    slot = forms.ModelChoiceField(
        queryset=BookingSlot.objects.none(),
        widget=forms.RadioSelect(attrs={'class': 'slot-radio'}),
        empty_label=None, #REMOVE EMPTY SLOTS
        required=True
        )

    class Meta:
        model = Booking
        fields = ['package', 'preferred_date', 'collection_type', 'slot']

        widgets = {
            'package': forms.Select(attrs={'class': 'form-select'}),
            'preferred_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': now().date(),
            }),
            'collection_type': forms.RadioSelect(attrs={
                # 'class':"form-check-input"
            }),
            
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.no_slots_available = False
        

        # only active packages
        packages = LabPackage.objects.filter(is_active=True)
        self.fields['package'].queryset = packages
        self.fields['package'].widget.attrs.update({
            'class':'form-select',
            'id':'id_package'
        })
        self.package_home_map={
            str(pkg.id): pkg.home_collection
            for pkg in packages
        }
        # IMPORTANT: slot is a ModelChoiceField now
        self.fields['slot'].queryset = BookingSlot.objects.none()
        self.fields['slot'].required = True

        package_id = self.data.get('package')
        preferred_date = self.data.get('preferred_date')
        collection_type = self.data.get('collection_type')

        #force lab when home collection nota allowed
        if package_id:
            try:
                package = LabPackage.objects.get(pk=package_id)
                if package.home_collection == 'NO':
                    collection_type = 'LAB'
                    self.initial['collection_type'] = 'LAB'
            except LabPackage.DoesNotExist:
                pass

            #load slots only when date + collection_type exist

        if preferred_date and  collection_type:
            qs = BookingSlot.objects.filter(
                date= preferred_date,
                collection_type=collection_type,
                is_active=True,
                booked_count__lt=F('max_bookings')
            ).order_by('time_slot')

            if qs.exists():
                self.fields['slot'].queryset = qs

            else:
                self.no_slots_available = True
        print("FORM DATA:", self.data)

    def clean_collection_type(self):
        collection_type = self.cleaned_data.get('collection_type')
        package = self.cleaned_data.get('package')

        if package and package.home_collection == 'NO':
            return 'LAB'
        return collection_type       

#<!--Booking form  Section End -->

#<!--BookingSlot form  Section Start -->
class BookingSlotForm(forms.ModelForm):
    class Meta:
        model = BookingSlot
        fields = [
            'date',
            'time_slot',
            'collection_type',
            'resource_type',
            'max_bookings',
            'is_active',
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'type':'date',
                'class':'form-control'
            }),
            '': forms.Select(attrs={
                'class': 'form-select'
            }),
            'time_slot' :forms.Select(attrs={
                'class':'form-control'
            }),
            'resource_type':forms.Select(attrs={
                'class':'form-control'
            }),
            'max_bookings':forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),        

        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #🔐 if slot already has bookings 
        if self.instance.pk and self.instance.booked_count > 0:
            for field in ['date','time_slot','collection_type','resource_type','max_bookings']:
                self.fields[field].disabled=True

    def clean_max_bookings(self):
        max_bookings = self.cleaned_data['max_bookings']

        #show error when user set limit less than booked count
        if self.instance.pk and self.instance.booked_count > max_bookings:
            raise forms.ValidationError('Max bookings cannot be less than already booked count')
        
        return max_bookings

#<!--BookingSlot form  Section End -->