from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pod_shop', '0012_productimage_image_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='brand',
            name='logo_url',
            field=models.URLField(blank=True, max_length=1000),
        ),
        migrations.AddField(
            model_name='brand',
            name='league',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
