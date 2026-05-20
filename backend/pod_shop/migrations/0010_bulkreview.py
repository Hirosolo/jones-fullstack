# Generated manually to create BulkReview model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pod_shop', '0009_add_reviewer_name_to_review'),
    ]

    operations = [
        migrations.CreateModel(
            name='BulkReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveIntegerField(choices=[(1, '1 sao'), (2, '2 sao'), (3, '3 sao'), (4, '4 sao'), (5, '5 sao')], help_text='Điểm đánh giá (1-5 sao) cho tất cả các review trong lô này.')),
                ('quantity', models.PositiveIntegerField(default=1, help_text='Số lượng review ẩn danh với rating này.')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Thời gian tạo bulk review.')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Thời gian cập nhật bulk review.')),
                ('admin_notes', models.TextField(blank=True, help_text='Ghi chú của quản trị viên.')),
                ('product', models.ForeignKey(help_text='Sản phẩm được đánh giá hàng loạt.', on_delete=django.db.models.deletion.CASCADE, related_name='product_bulk_review_set', to='pod_shop.product')),
            ],
            options={
                'verbose_name': 'Bulk Review (Review Hàng Loạt)',
                'verbose_name_plural': 'Bulk Reviews (Review Hàng Loạt)',
            },
        ),
    ]
