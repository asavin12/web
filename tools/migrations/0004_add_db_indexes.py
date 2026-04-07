from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0003_tool_cover_image_srcset'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tool',
            name='is_published',
            field=models.BooleanField(db_index=True, default=True, verbose_name='Xuất bản'),
        ),
    ]
