from ckeditor.widgets import CKEditorWidget
from django import forms
from django_ace import AceWidget

from articles.models import ArticleCategory, ArticleTag, Article, ArticleComment


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


class ArticleCategoryAdminForm(forms.ModelForm):
    """
    Form quản lý danh mục bài viết
    """
    class Meta:
        model = ArticleCategory
        fields = '__all__'
        widgets = build_widgets(['desc', 'desc_safe'])


class ArticleTagAdminForm(forms.ModelForm):
    """
    Form quản lý tag bài viết
    """
    class Meta:
        model = ArticleTag
        fields = '__all__'
        widgets = build_widgets(['desc', 'desc_safe'])


class ArticleAdminForm(forms.ModelForm):
    """
    Form quản lý bài viết
    """
    class Meta:
        model = Article
        fields = '__all__'
        widgets = {
            **build_widgets(['excerpt', 'excerpt_safe', 'content_safe']),
            'content': CKEditorWidget(config_name='full'),
        }


class ArticleCommentAdminForm(forms.ModelForm):
    """
    Form quản lý bình luận bài viết
    """
    class Meta:
        model = ArticleComment
        fields = '__all__'
        widgets = build_widgets(['content', 'content_safe'])

