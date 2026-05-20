import json
import re

from ckeditor.widgets import CKEditorWidget
from django import forms
from django_ace import AceWidget
from .models import ProductVariant

from pod_shop.models import Brand, Category, Tag, Product, Review
from .models import Product, ProductVariant, ProductColor, ProductSize, ProductAttr, ProductAttrItem


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


_TAG_SEP_RE = re.compile(r'[,;\n\r\t|]+')


class TagsAutoCreateWidget(forms.TextInput):
    """Text input với <datalist> suggestion từ Tag table + paste handler chuẩn
    hoá nhiều separator (comma/semicolon/newline/tab/pipe) → ', '. Tag chưa
    tồn tại tự create lúc form save. Live chip preview hiển thị tag được parse
    với badge '(new)' cho tag chưa có."""

    template_name = 'admin/widgets/tags_text.html'

    def __init__(self, attrs=None):
        defaults = {
            'list': 'product-tag-suggestions',
            'placeholder': 'Type or paste: tag1, tag2, tag3 — Enter or comma to separate',
            'style': 'width: 60em',
            'autocomplete': 'off',
            'class': 'vTextField',
        }
        if attrs:
            defaults.update(attrs)
        super().__init__(defaults)

    def get_context(self, name, value, attrs):
        ctx = super().get_context(name, value, attrs)
        suggestions = list(
            Tag.objects.order_by('name').values_list('name', flat=True)
        )
        ctx['widget']['suggestions'] = suggestions
        ctx['widget']['suggestions_json'] = json.dumps(suggestions)
        return ctx


class ProductAdminForm(forms.ModelForm):
    """
    Form quản lý sản phẩm — tags dùng input text (auto-create) thay vì
    filter_horizontal M2M widget mặc định.
    """
    tags_input = forms.CharField(
        required=False,
        label='Tags',
        widget=TagsAutoCreateWidget(),
        help_text='Cách nhau bằng dấu phẩy hoặc Enter. Tag chưa có sẽ tự tạo khi Save.',
    )

    class Meta:
        model = Product
        exclude = ('tags',)
        widgets = {
            'desc': CKEditorWidget(config_name='full'),
            'desc_short': AceWidget(
                mode="markdown",
                theme="monokai",
                wordwrap=True,
                width="100%",
                height="200px",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(
                self.instance.tags.order_by('name').values_list('name', flat=True)
            )

    def _save_m2m(self):
        # Parent save_m2m sets all M2M except tags (excluded). Apply our tags
        # parser here so it runs inside the same save() transaction as the
        # standard M2M handling — admin's save_related calls form.save_m2m().
        super()._save_m2m()
        raw = self.cleaned_data.get('tags_input') or ''
        names = [n.strip() for n in _TAG_SEP_RE.split(raw) if n.strip()]
        # Dedup case-insensitively, preserve first-seen casing
        seen = set()
        uniq = []
        for n in names:
            k = n.lower()
            if k in seen:
                continue
            seen.add(k)
            uniq.append(n)
        objs = []
        for name in uniq:
            # case-insensitive match so "Hiking" doesn't duplicate "hiking"
            existing = Tag.objects.filter(name__iexact=name).first()
            objs.append(existing or Tag.objects.create(name=name))
        self.instance.tags.set(objs)


class ProductBrandAdminForm(forms.ModelForm):
    """
    Form quản lý thương hiệu sản phẩm
    """
    class Meta:
        model = Brand
        fields = '__all__'
        widgets = build_widgets(
            ['desc']
        )


class ProductCategoryAdminForm(forms.ModelForm):
    """
    Form quản lý danh mục sản phẩm
    """
    class Meta:
        model = Category
        fields = '__all__'
        widgets = build_widgets(
            ['desc']
        )


class ProductTagAdminForm(forms.ModelForm):
    """
    Form quản lý tag sản phẩm
    """
    class Meta:
        model = Tag
        fields = '__all__'
        widgets = build_widgets(
            ['desc']
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

    class ProductVariantForm(forms.ModelForm):
        class Meta:
            model = ProductVariant
            fields = ['product', 'attr_items', 'price_origin', 'price_promo']  # Loại bỏ 'code'
            widgets = {
                'attr_items': forms.SelectMultiple,
            }
