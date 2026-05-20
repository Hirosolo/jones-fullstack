#!/usr/bin/python
import hashlib
import os
import random
import re
import arrow
import socket
from hashlib import sha1
from urllib.parse import urljoin

import requests
import strgen
from django.core.exceptions import ValidationError
from django.templatetags.static import static
from django.utils.text import slugify
from django_ace import AceWidget
from unidecode import unidecode


def safe_static(path, fallback=''):
    """static() raises ValueError under CompressedManifestStaticFilesStorage
    when the referenced asset isn't in the manifest. Serializers reference
    a default OG image that isn't always bundled, so a missing asset should
    not 500 an entire product listing — fall back silently."""
    try:
        return static(path)
    except Exception:
        return fallback


def slugify2(value):
    """
    Tạo slug từ chuỗi.
    Sử dụng thư viện unidecode để chuyển đổi các ký tự Unicode thành ký tự ASCII.
    """
    if not value:
        return 'no-name'
    return slugify(unidecode(value))


def generate_sha1(string, salt=None):
    """
    Generates a sha1 hash for supplied string. Doesn't need to be very secure
    because it's not used for password checking. We got Django for that.

    :param string:
        The string that needs to be encrypted.

    :param salt:
        Optionally define your own salt. If none is supplied, will use a random
        string of 5 characters.

    :return: Tuple containing the salt and hash.

    """
    if not salt:
        salt = sha1(str(random.random()).encode('utf-8')).hexdigest()[:5]
    h = sha1(salt.encode('utf-8') + str(string).encode('utf-8')).hexdigest()
    return salt, h


def hash_md5(str_: str):
    """
    Tạo mã băm MD5 từ chuỗi.
    """
    return hashlib.md5(str_.encode('utf-8')).hexdigest()


def bytes_to_str(bytes_text):
    """
    Chuyển đổi bytes thành chuỗi.
    """
    try:
        # trong trường hợp url là kiểu bytes
        return bytes_text.decode("utf-8")
    except AttributeError:
        return str(bytes_text)


# this is not intended to be an all-knowing IP address regex
IP_RE = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
IPV6_RE = re.compile(
    r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))')


def get_ip(request):
    """
    Hàm này sẽ trả về địa chỉ IP của người dùng truy cập trang web. Nếu người dùng đó đang sử dụng proxy, có thể sẽ có
    nhiều địa chỉ IP được liệt kê, trong trường hợp đó hàm sẽ chỉ lấy địa chỉ IP đầu tiên trong danh sách.
    Hàm này cũng sẽ xử lý trường hợp địa chỉ IP được lưu trong HTTP_X_FORWARDED_FOR thay vì REMOTE_ADDR.

    **NOTE** Hàm này được lấy từ django-tracking (MIT LICENSE)
                https://code.google.com/p/django-tracking/
    """

    # if neither header contain a value, just use local loopback
    x = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
    ip_address = ''
    if x:
        # make sure we have one and only one IP
        try:
            ip_address = IP_RE.match(x)
            if ip_address:
                ip_address = ip_address.group(0)
            else:
                ipv6 = IPV6_RE.match(x)
                if ipv6:
                    ip_address = ipv6.group(0)
                else:
                    # no IP, probably from some dirty proxy or other device
                    # throw in some bogus IP
                    ip_address = '10.0.0.1'

        except IndexError:
            pass
    return ip_address


def is_valid_ipv4_address(address):
    """
    Kiểm tra xem địa chỉ IP có hợp lệ không.
    """
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # Không hỗ trợ inet_pton
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # Không phải địa chỉ IPv4 hợp lệ
        return False
    return True


def annotate_js_bool(val):
    """
    Chuyển đổi giá trị boolean sang chuỗi 'true' hoặc 'false' để sử dụng trong JavaScript.
    """
    return True if val == 'true' else False


def mean(numbers):
    """
    Trình trung bình của một mảng gồm các phần tử là số.
    :param list numbers:
    :return:
    :rtype: float
    """
    return float(sum(numbers)) / max(len(numbers), 1) if numbers else 0


def replace_webp_ext(url: str):
    """
    Thay thế đường dẫn file ảnh với webp.
    """
    path_, ext = url.rsplit('.', maxsplit=1)
    if ext.lower() in ['jpg', 'jpeg', 'gif', 'png', 'webp']:
        return f'{path_}.webp'
    return


def get_random_code(length):
    """
    Tạo mã ngẫu nhiên với độ dài cố định.
    """
    return strgen.StringGenerator(r"[\d\w]{%s}" % length).render()


def get_random_code2(length, code):
    """
    Tạo mã ngẫu nhiên có độ dài và định dạng được chỉ định bởi tham số length và code.

    :param int length:
        Độ dài của mã ngẫu nhiên, là 1 số nguyên.

    :param code:
        Là kiểu giá trị của mã được tạo
        'a' - Mã chỉ chứa số và chữ cái viết hoa (alphanumeric).
        'c' - Mã chỉ chứa chữ cái viết hoa (char).
        'n' - Mã chỉ chứa số (num).
    """
    if code == "a":
        pattern = r"[\dA-Z]{%s}" % length
    elif code == "c":
        pattern = r"[A-Z]{%s}" % length
    elif code == "n":
        pattern = r"[\d]{%s}" % length
    else:
        raise ValueError("Giá trị của 'code' không hợp lệ, phải là 'a', 'c' hoặc 'n'.")

    # Sử dụng thư viện strgen để tạo mã ngẫu nhiên theo mẫu đã chọn
    return strgen.StringGenerator(pattern).render()


def gen_random_password(length=0, no_special_characters=False):
    """
    Tạo mật khẩu ngẫu nhiên.
    """
    from passwordgenerator import pwgenerator
    pw = pwgenerator.pw(no_special_characters=no_special_characters)
    return pw[:length] if length > 0 else pw


def verify_recaptcha(response_str, secret=''):
    """
    Xác nhận người dùng đã vượt qua Captcha hay chưa.
    :param str response_str:
    :param str secret:
    :return:
    :rtype: bool
    """
    from django.conf import settings
    url = 'https://www.google.com/recaptcha/api/siteverify'
    payload = {
        'secret': secret if secret else settings.RECAPTCHA_PRIVATE_KEY,
        'response': response_str,
    }
    r = requests.post(url, data=payload)
    if r.ok:
        data = r.json()
        return data['success']
    return False


def resolve_upload(name, filename, folder_name):
    """
    Tạo đường dẫn đến file upload.
    """
    from django.conf import settings
    extension = filename.split(".")[-1].lower() if "." in filename else "jpg"
    code = get_random_code(8)
    now = arrow.now().to(settings.TIME_ZONE)
    name_slug = slugify2(name)
    return f"{folder_name}/{now.format('YYYYMM')}/{name_slug}-{code}.{extension}"


def build_full_url(path: str):
    """
    Lấy đường dẫn đầy đủ của đường dẫn tương đối.
    """
    from django.conf import settings
    return urljoin(settings.SITE_URL, path)


def build_media_url(media_path: str):
    """
    Tạo URL tương đối cho media files.
    Trả về đường dẫn tương đối (ví dụ: /media/products/image.png) để frontend
    có thể proxy qua rewrite rule đến đúng backend server.
    """
    if not media_path:
        return ''
    
    # Nếu đã là URL đầy đủ, chuyển thành relative path
    if media_path.startswith(('http://', 'https://')):
        from urllib.parse import urlparse
        parsed = urlparse(media_path)
        return parsed.path
    
    # Đảm bảo bắt đầu bằng /
    if not media_path.startswith('/'):
        media_path = '/' + media_path
    
    # Đảm bảo có prefix /media/ nếu chưa có
    if not media_path.startswith('/media/'):
        from django.conf import settings
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        if not media_path.startswith(media_url):
            media_path = media_url + media_path.lstrip('/')
    
    return media_path


def validate_file_extension(value):
    """
    Kiểm tra xem có phải là file hoặc hình ảnh được cho phép hay không.
    """
    allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.webp']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f'Chỉ cho phép tải lên các định dạng file: {", ".join(allowed_extensions)}')


class DescAceWidgetMixin:
    """
    Mixin để thêm các widget Ace cho các trường description và description_safe
    """

    class Meta:
        widgets = {
            'desc': AceWidget(
                mode='text',
                theme='twilight',
                width='100%',
                height='200px',
                wordwrap=True,
                showprintmargin=True,
                showinvisibles=True,
                showgutter=True,
                fontsize=14,
                tabsize=4,
            ),
            'desc_safe': AceWidget(
                mode='html',
                theme='twilight',
                width='100%',
                height='200px',
                wordwrap=True,
                showprintmargin=True,
                showinvisibles=True,
                showgutter=True,
                fontsize=14,
                tabsize=4,
            ),
        }