# Generated by Django 5.0.6 on 2024-11-13 16:24

from django.db import migrations, models

def populate_order_date(apps, schema_editor):
    Order = apps.get_model('inventory', 'Order')
    for order in Order.objects.all():
        order.order_date = order.date_added  # assuming created_at exists in Order model
        order.save()
        
class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0017_alter_payment_payment_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='order_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(populate_order_date),
    ]
