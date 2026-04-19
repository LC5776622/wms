# from django.contrib.auth import get_user_model
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.core.mail import send_mail
# from django.conf import settings

# # User = get_user_model()

# # @receiver(post_save, sender=User)
# # def send_new_user_email(sender, instance, created, **kwargs):
# #     if created:
# #         subject = 'New User Registered'
# #         message = f'A new user {instance.username} has registered in your app.'
# #         from_email = settings.DEFAULT_FROM_EMAIL
# #         recipient_list = ['pradeep.bisht@fisglobal.com']
# #         send_mail(subject, message, from_email, recipient_list)
