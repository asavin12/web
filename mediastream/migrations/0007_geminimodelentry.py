from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mediastream', '0006_add_youtube_to_streammedia'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeminiModelEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model_id', models.CharField(db_index=True, help_text='VD: gemini-2.5-flash, gemini-2.5-pro', max_length=200, unique=True, verbose_name='Model ID')),
                ('display_name', models.CharField(max_length=300, verbose_name='Tên hiển thị')),
                ('description', models.CharField(blank=True, default='', max_length=500, verbose_name='Mô tả')),
                ('is_active', models.BooleanField(default=True, help_text='Bỏ chọn để ẩn model khỏi danh sách', verbose_name='Hoạt động')),
                ('sort_order', models.IntegerField(default=100, verbose_name='Thứ tự')),
                ('synced_at', models.DateTimeField(auto_now=True, verbose_name='Đồng bộ lần cuối')),
            ],
            options={
                'verbose_name': 'Gemini Model',
                'verbose_name_plural': 'Gemini Models',
                'ordering': ['sort_order', 'model_id'],
            },
        ),
    ]
