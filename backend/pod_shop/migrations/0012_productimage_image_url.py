from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pod_shop', '0011_productcolor_productsize_product_available_attrs_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productimage',
            name='image_url',
            field=models.URLField(blank=True, max_length=1000),
        ),
    ]
