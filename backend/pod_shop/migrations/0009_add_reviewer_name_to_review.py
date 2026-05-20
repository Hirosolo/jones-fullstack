# Generated manually to add reviewer_name field to Review model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pod_shop', '0007_remove_cartitem_session_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='reviewer_name',
            field=models.CharField(blank=True, help_text='Reviewer name (required if not logged in)', max_length=255),
        ),
    ]
