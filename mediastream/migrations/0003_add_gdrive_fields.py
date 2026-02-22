"""
Add Google Drive storage support fields to StreamMedia
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mediastream', '0002_alter_streammedia_file_alter_streammedia_thumbnail'),
    ]

    operations = [
        # Storage type field
        migrations.AddField(
            model_name='streammedia',
            name='storage_type',
            field=models.CharField(
                choices=[('local', 'Local Storage'), ('gdrive', 'Google Drive')],
                default='local',
                help_text='local = file trên VPS, gdrive = stream từ Google Drive',
                max_length=10,
                verbose_name='Loại lưu trữ',
            ),
        ),
        # Google Drive file ID
        migrations.AddField(
            model_name='streammedia',
            name='gdrive_file_id',
            field=models.CharField(
                blank=True,
                default='',
                help_text='ID file trên Google Drive (lấy từ URL chia sẻ). Để trống nếu dùng local.',
                max_length=255,
                verbose_name='Google Drive File ID',
            ),
        ),
        # Google Drive URL
        migrations.AddField(
            model_name='streammedia',
            name='gdrive_url',
            field=models.URLField(
                blank=True,
                default='',
                help_text='URL chia sẻ Google Drive (tự động trích xuất File ID)',
                max_length=500,
                verbose_name='Google Drive URL',
            ),
        ),
        # Make file field optional (blank=True for gdrive entries)
        migrations.AlterField(
            model_name='streammedia',
            name='file',
            field=models.FileField(
                blank=True,
                upload_to='stream/%(media_type)s/',
                verbose_name='File media',
            ),
        ),
    ]
