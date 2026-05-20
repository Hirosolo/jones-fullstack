from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from profiles.models import Profile
from utils.common import get_random_code2


@receiver(post_save, sender=User)
def handle_user_post_save(sender, instance: User, created, **kwargs):
    """
    Tạo profile tương ứng khi thành viên đăng ký và mã thành viên tương ứng
    """
    # Nếu user mới được tạo thì tạo profile tương ứng
    if not Profile.objects.filter(user=instance).exists():
        code = get_random_code2(13, 'n')
        Profile.objects.create(
            user=instance,
            email=instance.email,
            code=code
        )

    # Nếu user đã tạo thì cập nhật thông tin profile
    if profile := Profile.objects.filter(user=instance).first():
        profile.email = instance.email
        profile.first_name = instance.first_name
        profile.last_name = instance.last_name
        profile.save()
