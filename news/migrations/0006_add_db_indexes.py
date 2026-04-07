from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0005_fix_category_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='is_published',
            field=models.BooleanField(db_index=True, default=False, verbose_name='Đã xuất bản'),
        ),
        migrations.AlterField(
            model_name='article',
            name='published_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Ngày xuất bản'),
        ),
    ]
