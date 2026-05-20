from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pod_shop', '0014_unlimit_slug_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='wp_review_id',
            field=models.BigIntegerField(
                blank=True,
                null=True,
                unique=True,
                help_text='ID của review tương ứng trên WP/.shop. Dùng để dedup khi import và để khóa cặp .com↔.shop.',
            ),
        ),
    ]
