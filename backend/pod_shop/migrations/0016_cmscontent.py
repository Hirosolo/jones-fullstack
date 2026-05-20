from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pod_shop', '0015_review_wp_review_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='CMSContent',
            fields=[
                (
                    'id',
                    models.PositiveSmallIntegerField(
                        default=1, primary_key=True, serialize=False
                    ),
                ),
                (
                    'payload',
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text='Toàn bộ CMS content (home/footer/seo/menu) dạng JSON.',
                    ),
                ),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'CMS Content',
                'verbose_name_plural': 'CMS Content',
            },
        ),
    ]
