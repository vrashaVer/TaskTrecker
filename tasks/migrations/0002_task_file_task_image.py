# Generated by Django 5.1.1 on 2024-10-09 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='task_files/'),
        ),
        migrations.AddField(
            model_name='task',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='task_images/'),
        ),
    ]
