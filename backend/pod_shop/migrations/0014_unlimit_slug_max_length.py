from django.db import migrations
import autoslug.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pod_shop', '0013_brand_logo_url_league'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='slug',
            field=autoslug.fields.AutoSlugField(
                blank=True, editable=True, max_length=500,
                populate_from='name', unique=True,
            ),
        ),
        migrations.AlterField(
            model_name='brand',
            name='slug',
            field=autoslug.fields.AutoSlugField(
                blank=True, editable=True, max_length=500,
                populate_from='name', unique=True,
            ),
        ),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=autoslug.fields.AutoSlugField(
                blank=True, editable=True, max_length=500,
                populate_from='name', unique=True,
            ),
        ),
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=autoslug.fields.AutoSlugField(
                blank=True, editable=True, max_length=500,
                populate_from='name', unique=True,
            ),
        ),
    ]
