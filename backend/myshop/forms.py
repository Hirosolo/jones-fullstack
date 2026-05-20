from ckeditor.widgets import CKEditorWidget
from django import forms
from django_ace import AceWidget

from myshop.models import Brand, Category, Tag, Product, Review


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


class ProductAdminForm(forms.ModelForm):
    """
    Form quản lý sản phẩm
    """
    class Meta:
        model = Product
        fields = '__all__'
        widgets = build_widgets(
            ['desc_short', 'desc_short_safe', 'desc', 'desc_safe', 'seller_notes', 'seller_notes_safe']
        )


class ProductBrandAdminForm(forms.ModelForm):
    """
    Form quản lý thương hiệu sản phẩm
    """
    class Meta:
        model = Brand
        fields = '__all__'
        widgets = build_widgets(
            ['desc', 'desc_safe']
        )


class ProductCategoryAdminForm(forms.ModelForm):
    """
    Form quản lý danh mục sản phẩm
    """
    class Meta:
        model = Category
        fields = '__all__'
        widgets = build_widgets(
            ['desc', 'desc_safe']
        )


class ProductTagAdminForm(forms.ModelForm):
    """
    Form quản lý tag sản phẩm
    """
    class Meta:
        model = Tag
        fields = '__all__'
        widgets = build_widgets(
            ['desc', 'desc_safe']
        )


class ProductReviewAdminForm(forms.ModelForm):
    """
    Form quản lý đánh giá sản phẩm
    """
    class Meta:
        model = Review
        fields = '__all__'
        widgets = build_widgets (
            ['content', 'content_safe']
        )
