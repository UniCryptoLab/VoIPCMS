# Generated by Django 4.0.4 on 2022-12-29 06:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voip', '0010_alter_recharge_expired_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='recharge',
            name='credit_mark',
            field=models.CharField(blank=True, default='', max_length=128, verbose_name='CreditMark'),
        ),
    ]
