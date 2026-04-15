from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import ClientProfile, User


@receiver(post_save, sender=User)
def ensure_client_profile(sender, instance, **kwargs):
    if instance.role == User.Roles.CLIENT:
        ClientProfile.objects.get_or_create(user=instance)
