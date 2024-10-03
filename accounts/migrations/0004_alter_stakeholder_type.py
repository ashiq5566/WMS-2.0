# Generated by Django 5.0.6 on 2024-10-03 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_remove_stakeholder_stakeholder_address_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stakeholder',
            name='type',
            field=models.CharField(blank=True, choices=[('Customer', 'Customer'), ('Customer', 'Supplier')], max_length=128, null=True),
        ),
    ]
