import random
from datetime import timezone

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from faker import Faker

from articles.models import Article, ArticleCategory, ArticleTag, ArticleComment

fake = Faker('en_US')
User = get_user_model()

image_links = [
    "https://placehold.co/640x480",
    "https://placehold.co/1640x480",
    "https://placehold.co/3640x480",
    "https://placehold.co/640x1800",
    "https://placehold.co/1400x1800",
]

def generate_code(prefix='ART', length=10):
    return prefix + fake.bothify(text='##########')[:length]

def generate_html_content():
    return (
        f"<p>{fake.text(max_nb_chars=1000)}</p>\n"
        f"<img src='{random.choice(image_links)}' alt='Ảnh minh họa' width='100%'/>\n"
        f"<p>{fake.text(max_nb_chars=2000)}</p>"
    )

def generate_multi_word_name(min_words=2, max_words=3):
    return ' '.join(fake.words(nb=random.randint(min_words, max_words))).capitalize()

class Command(BaseCommand):
    help = 'Tạo dữ liệu mẫu cho bài viết, danh mục, thẻ và bình luận'

    def add_arguments(self, parser):
        parser.add_argument('--num_articles', type=int, default=10, help='Số lượng bài viết')
        parser.add_argument('--num_comments', type=int, default=3, help='Số lượng bình luận mỗi bài')

    def handle(self, *args, **options):
        num_articles = options['num_articles']
        num_comments = options['num_comments']

        users = list(User.objects.all())

        # Tạo danh mục nếu chưa có
        categories = list(ArticleCategory.objects.all())
        if not categories:
            self.stdout.write("🔧 Đang tạo danh mục mẫu...")
            for i in range(5):
                name = generate_multi_word_name()
                category = ArticleCategory.objects.create(
                    name=name,
                    desc=fake.text(max_nb_chars=200),
                    desc_safe=fake.text(max_nb_chars=200),
                    slug=fake.slug(),
                    order=i,
                    admin_note=fake.sentence(),
                    meta_title=f"{name} - Danh mục"[:60],
                    meta_desc=fake.text(max_nb_chars=145)
                )
                categories.append(category)

        # Tạo thẻ nếu chưa có
        tags = list(ArticleTag.objects.all())
        if not tags:
            self.stdout.write("🔧 Đang tạo thẻ mẫu...")
            for i in range(10):
                name = generate_multi_word_name()
                tag = ArticleTag.objects.create(
                    name=name,
                    desc=fake.text(max_nb_chars=200),
                    desc_safe=fake.text(max_nb_chars=200),
                    slug=fake.slug(),
                    order=i,
                    admin_note=fake.sentence(),
                    meta_title=f"{name} - Thẻ bài viết"[:60],
                    meta_desc=fake.text(max_nb_chars=145)
                )
                tags.append(tag)

        if not users:
            self.stdout.write(self.style.ERROR("❌ Không có người dùng nào trong hệ thống."))
            return

        for _ in range(num_articles):
            user = random.choice(users)
            category = random.choice(categories)
            title = fake.sentence(nb_words=8)
            content = generate_html_content()
            code = generate_code()

            article = Article.objects.create(
                title=title,
                code=code,
                excerpt=fake.text(max_nb_chars=200),
                excerpt_safe=fake.text(max_nb_chars=200),
                content=content,
                content_safe=content,
                slug=None,
                author=user,
                author_name=user.username,
                published_at=fake.date_time_this_year(tzinfo=timezone.utc),
                num_views=random.randint(0, 1000),
                featured=random.choice([True, False]),
                status="published",
                meta_title=title[:60],
                meta_desc=fake.text(max_nb_chars=145),
                category=category,
            )

            # Gán ngẫu nhiên thẻ
            article.tags.set(random.sample(tags, k=min(3, len(tags))))

            for _ in range(num_comments):
                ArticleComment.objects.create(
                    code=generate_code('CMT'),
                    article=article,
                    author=random.choice(users),
                    content=fake.text(max_nb_chars=200),
                    content_safe=fake.text(max_nb_chars=200),
                    created_at=fake.date_time_this_year(tzinfo=timezone.utc),
                    updated_at=fake.date_time_this_year(tzinfo=timezone.utc),
                )

        self.stdout.write(self.style.SUCCESS(f"✅ Đã tạo {num_articles} bài viết, mỗi bài có {num_comments} bình luận."))
