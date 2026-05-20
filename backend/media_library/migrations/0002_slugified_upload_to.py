from django.db import migrations, models
import media_library.models


class Migration(migrations.Migration):

    dependencies = [
        ('media_library', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mediaasset',
            name='image',
            field=models.ImageField(upload_to=media_library.models.slugified_upload_to),
        ),
    ]
