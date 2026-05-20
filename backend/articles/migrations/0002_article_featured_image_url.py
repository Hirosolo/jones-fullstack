from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='featured_image_url',
            field=models.URLField(blank=True, max_length=1000),
        ),
    ]
