# Generated by Django 4.0.4 on 2022-12-27 02:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voip', '0003_rename_sales_staff_rename_sales_customer_staff'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staff',
            name='skype_id',
            field=models.CharField(default='', max_length=200, verbose_name='SkypeId'),
        ),
    ]
