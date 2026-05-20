from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pod_shop', '0016_cmscontent'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductSlugAlias',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'old_slug',
                    models.CharField(db_index=True, max_length=500, unique=True),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'product',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='slug_aliases',
                        to='pod_shop.product',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Product slug alias',
                'verbose_name_plural': 'Product slug aliases',
                'ordering': ['-created_at'],
            },
        ),
    ]
