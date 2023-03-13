# Generated by Django 4.0.4 on 2023-03-05 04:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voip', '0041_outboundgateway_internal_ip'),
    ]

    operations = [
        migrations.AddField(
            model_name='outboundgateway',
            name='asterisk_current_calls',
            field=models.BigIntegerField(default=0, verbose_name='Current Calls'),
        ),
        migrations.AddField(
            model_name='outboundgateway',
            name='asterisk_status',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Gateway Status'),
        ),
    ]