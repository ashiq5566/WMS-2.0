# Generated by Django 5.0.6 on 2024-10-24 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0011_orderitem_total'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='unit',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
