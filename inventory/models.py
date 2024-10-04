from django.db import models

from general.models import WebBaseModel
from accounts.models import Stakeholder

class Product(WebBaseModel):
    product_id = models.CharField(max_length=10,null=True)
    name = models.CharField(max_length=100, null=True, blank=False,unique=True)
    unit_price = models.PositiveBigIntegerField(null=True,blank=True)
    qty_available = models.PositiveIntegerField(null=True, default=0)
    qty_sold = models.PositiveIntegerField(null=True, default=0)
    qty_purchased = models.PositiveIntegerField(null=True, default=0)
    status = models.BooleanField(default=False)
    
    def __str__(self):
        return  self.name
    
class PurchaseOrder(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    po_no = models.IntegerField(null=True)
    po_number = models.CharField(max_length=100, null=True, unique=True)
    stakeholder = models.ForeignKey(Stakeholder, on_delete=models.CASCADE,null=True)
    gross_amount = models.PositiveIntegerField(null=True)
    discount = models.PositiveIntegerField(null=True)
    net_amount = models.PositiveIntegerField(null=True)
    net_pending = models.PositiveIntegerField(null=True,default=0)
    status = models.BooleanField(default=False,null=True)
    
    def __str__(self):
            return self.po_number