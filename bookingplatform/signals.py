from django.db.models.signals import post_save
from django.dispatch import receiver
from bookingplatform.models import User, PatientProfile, LabAdminProfile


# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if not created:
#         return

#     if created:
#         if instance.role == 'PATIENT': 
#             PatientProfile.objects.create(user=instance)
#         elif instance.role == 'LAB_ADMIN':
#             LabAdminProfile.objects.create(user=instance)
