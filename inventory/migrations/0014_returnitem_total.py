# Generated by Django 5.0.6 on 2024-10-24 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0013_alter_product_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnitem',
            name='total',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]