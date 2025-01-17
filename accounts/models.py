from django.db import models
from django.contrib.auth.models import AbstractUser, Group

from general.models import WebBaseModel

class User(AbstractUser):
    phone = models.CharField(max_length=45, null=True, blank=True)
    email = models.EmailField(max_length=45, null=True,blank=True)
    user_type = models.CharField(max_length=45, blank=True, null=True)
    
    def __str__(self):
            return f"{str(self.first_name)} - {self.user_type}" 
        
        
class Stakeholder(WebBaseModel):
    STAKEHOLDER_TYPES = [
        ('Customer', 'Customer'),
        ('Supplier', 'Supplier'),
    ]
    stakeholder_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    name = models.CharField(max_length=100,null=True)
    address = models.CharField(max_length=200,null=True)
    mobile = models.CharField(max_length=15,null=True)
    email = models.EmailField(null=True, blank=True)
    type = models.CharField(choices=STAKEHOLDER_TYPES, max_length=128, null=True, blank=True)
    opening_balance = models.IntegerField(null=True, blank=True, default=0)
    
    @property
    def total_pending_amount(self):
        pending = self.order_set.filter(pending_amount__gt=0).aggregate(total=models.Sum('pending_amount'))['total'] or 0
        return pending + self.opening_balance
    
    @property
    def total_setteled_amount(self):
        return self.payment_set.aggregate(total=models.Sum('amount'))['total'] or 0
    
    @property
    def next_bill_to_clear(self):
        bill = self.order_set.filter(pending_amount__gt=0).order_by('date_added').first()
        pending_amount = bill.pending_amount
        order_number = bill.order_number
        
        return {'pending_amount': pending_amount, 'order_number': order_number}
    def __str__(self):
            return f'{self.id}'


# class Supplier(WebBaseModel):
#     supplier_id = models.CharField(max_length=100, null=True, unique=True)
#     supplier_name = models.CharField(max_length=100, null=True)
#     supplier_address = models.CharField(max_length=200, null=True)
#     supplier_mobile = models.CharField(max_length=15,null=True)
    
#     def __str__(self):
#             return self.supplier_name