from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from articles.models import ArticleCategory, ArticleTag, Article, ArticleComment
from utils.common import get_random_code2
from utils.content_processors import clean_content

# Dict ánh xạ các model cần xử lý trước khi lưu với các trường tương ứng
PRE_SAVE_MODELS = {
    ArticleCategory: ['desc'],
    ArticleTag: ['desc'],
    Article: ['excerpt', 'content'],
    ArticleComment: ['content'],
}

# Danh sách các model cần xử lý sau khi lưu
POST_SAVE_MODELS = [Article, ArticleComment]


@receiver(pre_save)
def handle_pre_save(sender, instance, **kwargs):
    """
    Xử lý trước khi lưu dữ liệu
    """
    if sender in PRE_SAVE_MODELS:
        for field in PRE_SAVE_MODELS[sender]:
            safe_field = f"{field}_safe"
            setattr(instance, safe_field, clean_content(getattr(instance, field)))


@receiver(post_save)
def handle_post_save(sender, instance, created, **kwargs):
    """
    Xử lý sau khi lưu dữ liệu
    """
    if sender in POST_SAVE_MODELS and not instance.code:
        code = get_random_code2(13, "n")
        instance.code = code
        sender.objects.filter(id=instance.id).update(code=code)

