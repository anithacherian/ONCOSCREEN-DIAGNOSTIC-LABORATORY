"""
URL configuration for oncoscreen project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from bookingplatform import views
from django.contrib.auth import views as auth_views
from bookingplatform.forms import CustomSetPasswordForm
from bookingplatform.views import CustomPasswordResetView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.homepage,name='home'),
    path('about',views.aboutpage,name='about'),
    path('services',views.servicepage,name='services'),
    path('contact',views.contactpage,name='contact'),

    path('login',views.login_view,name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register',views.patient_register_view),
    path('labadmin/register/',views.labadmin_register_view,name='labadmin_register'),

    path('password_reset/',
         CustomPasswordResetView.as_view(),
         name='password_reset'
         ),
    path(
        'password_reset_done',
        auth_views.PasswordResetDoneView.as_view(
            template_name='auth/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'reset-password-confirm/<uidb64>/<token>',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='auth/password_reset_confirm.html',
            form_class = CustomSetPasswordForm
        ),
        name='password_reset_confirm'
    ),
    path(
        'reset-password-complete',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='auth/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
    path('lab/dashboard/', views.lab_dashboard, name='lab_dashboard'),
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/myprofile/', views.patient_profile, name='patient_profile'),
    path('patient/profile/edit/', views.patient_profile_edit, name='edit_patient_profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('booking/new/', views.book_package, name='book_any_package'),
    path('booking/new/<int:pk>/', views.book_package, name='book_any_package'),
    path('booking/<int:booking_id>/payment/', views.payment, name='payment'),
    path('booking/payment_success/<int:booking_id>/', views.payment_success, name='payment_success'),
    path('bookings/', views.my_bookings, name='my_bookings'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('patient/notifications/',views.my_notifications,name='my_notifications'),
    path('patient/payments/<int:pk>/refund/', views.patient_refund_payment, name='patient_refund_payment'),

    path('all_categories_view/', views.all_categories_view, name='all_categories_view'),
    path('category_packages/<int:pk>/',views.category_packages_view,name='category_packages'),
    path('packages_detail/<int:pk>/', views.packages_detail_view, name='packages_detail'),

    path('lab/dashboard/create_package/', views.create_package, name='create_package'),
    path('lab/lab_view_package/', views.lab_packages_list_view, name='lab_view_package'),
    path('lab/lab_package_details/<int:pk>/', views.lab_packages_edit, name='lab_package_details'),
    path('lab/lab_package_delete/<int:package_id>/', views.lab_packages_delete, name='lab_package_delete'),
    path('lab/tests/', views.lab_test_list, name='lab_test_list'),
    path('lab/tests/add/', views.lab_test_create, name='lab_test_create'),
    path('lab/tests/edit/<int:pk>/', views.lab_test_edit, name='lab_test_edit'),
    path('lab/tests/<int:pk>/', views.lab_test_delete, name='lab_test_delete'),
    path('lab/dashboard/staff_register/',views.create_staff_view,name='staff_register'),
    path('lab/staff_view_list/',views.staff_view_list,name='staff_view_list'),
    path('lab/staff_edit/<int:pk>/',views.staff_edit,name='staff_edit'),
    path('lab/staff_delete/<int:pk>/', views.staff_delete, name='staff_delete'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('lab/bookings/', views.lab_booking_list, name='lab_booking_list'),
    path('bookings/mark_sample_collected/<int:pk>/', views.mark_sample_collected, name='mark_sample_collected'),
    path('slots/', views.slot_list, name='slot_list'),
    path('slots/create/', views.create_slot, name='create_slot'),
    path('slots/edit/<int:pk>/', views.edit_slot, name='edit_slot'),
    path('lab/slot/<int:pk>/', views.delete_or_disable_slot, name='delete_or_disable_slot'),
    path('lab/bookings/<int:pk>/upload-report/',views.upload_test_report,name='upload_test_report'),
    path('lab/bookings/<int:pk>/complete/',views.mark_booking_completed,name='mark_booking_completed'),
    path('lab/payments/', views.lab_payment_list, name='lab_payment_list'),
    path('lab/payments/<int:pk>/refund/', views.refund_payment, name='refund_payment'),
    # path("payments/export/", views.export_payments_csv, name="export_payments"),

    path('search_package_list', views.search_package_list, name='search_package_list'),


]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
