from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0004_add_tags_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='knowledgearticle',
            name='is_published',
            field=models.BooleanField(db_index=True, default=False, verbose_name='Đã xuất bản'),
        ),
        migrations.AlterField(
            model_name='knowledgearticle',
            name='published_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
