from django.db import models

from general.models import WebBaseModel

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