# Generated by Django 4.0.4 on 2022-12-30 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voip', '0013_recharge_pay_address_recharge_pay_network'),
    ]

    operations = [
        migrations.AddField(
            model_name='recharge',
            name='pay_currency',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='Pay Currency'),
        ),
        migrations.AlterField(
            model_name='recharge',
            name='pay_address',
            field=models.CharField(blank=True, default='', max_length=128, verbose_name='Address'),
        ),
    ]
