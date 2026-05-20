from django import forms
from django_ace import AceWidget

from utils.models import HomeSlider, StaticPage


def make_ace_widget(mode='text'):
    """
    Tạo widget AceEditor với các tùy chọn mặc định
    """
    return AceWidget(
        mode=mode,
        theme='twilight',
        width='100%',
        height='200px',
        wordwrap=True,
        showprintmargin=True,
        showinvisibles=True,
        showgutter=True,
        fontsize=14,
        tabsize=4,
    )


def build_widgets(fields):
    """
    Xây dựng widget cho các trường trong form
    """
    return {
        field: make_ace_widget('text') if not field.endswith('_safe') else make_ace_widget('html')
        for field in fields
    }


class HomeSliderAdminForm(forms.ModelForm):
    """
    Form quản lý slider trên trang chủ
    """
    class Meta:
        model = HomeSlider
        fields = '__all__'
        widgets = build_widgets(['desc', 'desc_safe'])


class StaticPageAdminForm(forms.ModelForm):
    """
    Form quản lý các trang tĩnh
    """
    class Meta:
        model = StaticPage
        fields = '__all__'
        widgets = build_widgets(['excerpt', 'excerpt_safe', 'content', 'content_safe'])

