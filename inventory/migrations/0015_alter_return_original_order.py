# Generated by Django 5.0.6 on 2024-10-24 18:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0014_returnitem_total'),
    ]

    operations = [
        migrations.AlterField(
            model_name='return',
            name='original_order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.order'),
        ),
    ]