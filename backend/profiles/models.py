# path: profiles/models.py
# Description: Định nghĩa các model cho ứng dụng profiles.
# Ứng dụng profiles chứa các model liên quan đến thông tin cá nhân của người dùng.
# Các model bao gồm Profile, Shipping.
# Các model này được sử dụng để lưu trữ thông tin cá nhân của người dùng, địa chỉ giao hàng, thông tin liên hệ,...

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django_countries.fields import CountryField

from utils.common import build_full_url


class Profile(models.Model):
    """
    Profile model
    """
    user = models.OneToOneField(
        User, blank=True, null=True,
        on_delete=models.CASCADE,
        related_name='user_profile_set', verbose_name='Người dùng',
        help_text='Người dùng tương ứng với hồ sơ.'
    )
    code = models.CharField(max_length=13, unique=True, help_text='Mã thành viên')

    first_name = models.CharField(max_length=255, blank=True, help_text='Tên người dùng', verbose_name='Tên')
    last_name = models.CharField(max_length=255, blank=True, help_text='Họ người dùng', verbose_name='Họ')
    email = models.EmailField(help_text='Email người dùng', verbose_name='Email')

    metadata = models.JSONField(blank=True, null=True, verbose_name='Dữ liệu mở rộng')
    admin_notes = models.TextField(blank=True, verbose_name='Ghi chú của quản trị viên')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')

    # IP và User-Agent của người dùng mới truy cập
    ip = models.GenericIPAddressField(blank=True, null=True)
    ua = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def url(self):
        """
        Trả về đường dẫn tới trang chi tiết của profile.
        Ví dụ: /profiles/profile-code/
        """
        return reverse('profiles:profile_detail_view', kwargs={'code': self.code})

    def get_absolute_url(self):
        """
        Trả về đường dẫn tới trang chi tiết của profile.
        """
        return self.url()

    def full_url(self):
        """
        Trả về đường dẫn đầy đủ tới trang chi tiết của profile.
        Ví dụ: https://example.com/profiles/profile-code/
        """
        return build_full_url(self.url())

    def full_name(self):
        """
        Trả về họ và tên đầy đủ của user.
        """
        if self.user:
            fullname = "%s %s" % (self.user.first_name, self.user.last_name)
            return fullname.strip()
        return ''

    def __str__(self):
        """
        Trả về tên của profile hoặc username của user nếu profile không có tên.
        """
        if self.full_name():
            return self.full_name()
        elif self.user:
            return self.user.username
        else:
            return 'No Profile'


class Shipping(models.Model):
    """
    Shipping model
    """
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE,
        related_name='profile_shippingaddress_set',
        null=True, blank=True, verbose_name='Hồ sơ',
        help_text='Hồ sơ người dùng'
    )
    address_book_name = models.CharField(
        max_length=255,
        help_text='Tên gợi nhớ của địa chỉ nhận hàng. Ví dụ: Địa chỉ 1, Địa chỉ 2,...',
        verbose_name='Tên địa chỉ'
    )
    first_name = models.CharField(
        max_length=255,
        help_text='Tên của người nhận hàng',
        verbose_name='Tên'
    )
    last_name = models.CharField(
        max_length=255,
        help_text='Họ của người nhận hàng',
        verbose_name='Họ'
    )
    email = models.EmailField(help_text='Địa chỉ Email của người nhận hàng', verbose_name='Email')
    street = models.CharField(
        max_length=255, help_text='Địa chỉ của người nhận hàng, gồm số nhà và tên đường,...',
        verbose_name='Địa chỉ cụ thể'
    )
    state = models.CharField(
        null=True, blank=True, max_length=255, help_text='Tên quận huyện người nhận hàng đang sống',
        verbose_name='Quận / Huyện'
    )
    city = models.CharField(
        max_length=255, blank=True, help_text='Tên thành phố, thị xã người nhận hàng đang sống',
        verbose_name='Thành Phố / Thị Xã'
    )
    country = models.CharField(
        CountryField(blank_label='(Chọn quốc gia)'),
        help_text='Quốc gia người nhận hàng đang sống'
    )
    zip_code = models.CharField(max_length=10, help_text='Mã bưu chính')
    is_default = models.BooleanField(
        default=False, help_text='Trường đánh dấu địa chỉ mặc định của người dùng.', verbose_name='Địa chỉ mặc định'
    )
    admin_notes = models.TextField(blank=True, help_text='Ghi chú của quản trị viên.')
    removed = models.BooleanField(default=False)

    def __str__(self):
        """
        Trả về tên của profile hoặc username của user nếu profile không có tên, hoặc trả về tên của khách hàng.
        """
        if self.profile:
            return f"Địa chỉ nhận hàng: {self.address_book_name} của {self.profile}."
        else:
            return f"Địa chỉ nhận hàng của Khách"

    def save(self, *args, **kwargs):
        """
        Ghi đè phương thức save của model, tự động cập nhật trạng thái mặc định nếu có.        """
        if self.is_default:
            Shipping.objects.filter(profile=self.profile, is_default=True).update(is_default=False)
        super(Shipping, self).save(*args, **kwargs)