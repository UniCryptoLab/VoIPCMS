# Generated by Django 4.0.4 on 2023-02-01 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voip', '0035_alter_errorfile_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='errorfile',
            name='is_del',
            field=models.BooleanField(default=False, verbose_name='Delete'),
        ),
    ]
