from django.contrib import admin
from .models import Order, Product, OrderItem, Return, ReturnItem, Payment, Invoice, InvoiceItem

admin.site.register(Order)
admin.site.register(Product)
admin.site.register(OrderItem)
admin.site.register(Return)
admin.site.register(ReturnItem)
admin.site.register(Payment)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)
