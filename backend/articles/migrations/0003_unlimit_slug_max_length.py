from django.db import migrations
import autoslug.fields


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0002_article_featured_image_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articlecategory',
            name='slug',
            field=autoslug.fields.AutoSlugField(
                blank=True, editable=True, help_text='Đường dẫn thân thiện',
                max_length=500, populate_from='name', unique=True,
            ),
        ),
        migrations.AlterField(
            model_name='articletag',
            name='slug',
            field=autoslug.fields.AutoSlugField(
                blank=True, editable=True, help_text='Đường dẫn thân thiện',
                max_length=500, populate_from='name', unique=True,
            ),
        ),
        migrations.AlterField(
            model_name='article',
            name='slug',
            field=autoslug.fields.AutoSlugField(
                blank=True, editable=True, help_text='Đường dẫn thân thiện',
                max_length=500, populate_from='title', unique=True,
            ),
        ),
    ]
