from django.db import models
from django.db import transaction
from django.db.models import F

from general.models import WebBaseModel
from accounts.models import Stakeholder

class Product(WebBaseModel):
    UNIT_CHOICES = [
        ('Pieces', 'Pieces'),
        ('Kilograms', 'Kilograms'),
        ('Sets', 'Sets'),
    ]
    product_id = models.CharField(max_length=10,null=True)
    name = models.CharField(max_length=100, null=True, blank=False,unique=True)
    selling_price = models.PositiveBigIntegerField(null=True,blank=True)
    price_at_time_of_purchase = models.PositiveBigIntegerField(null=True,blank=True)
    qty_available = models.PositiveIntegerField(null=True, default=0)
    qty_sold = models.PositiveIntegerField(null=True, default=0)
    qty_purchased = models.PositiveIntegerField(null=True, default=0)
    status = models.BooleanField(default=False)
    unit = models.CharField(choices=UNIT_CHOICES, null=True, blank=True, max_length=100)
    
    def __str__(self):
        return  self.name
    
class Order(WebBaseModel):
    ORDER_TYPE_CHOICES = [
        ('PO', 'Purchase Order'),
        ('SO', 'Sales Order'),
    ]
    STATUS_CHOICES = [
        ('Delivered', 'Delivered'),
        ('Recieved', 'Recieved'),
        ('Cancelled', 'Cancelled'),
        ('Closed', 'Closed'),
        ('Issued', 'Issued'),
    ]
    order_type = models.CharField(max_length=2, choices=ORDER_TYPE_CHOICES)
    order_number = models.CharField(max_length=100, null=True, unique=True)
    stakeholder = models.ForeignKey(Stakeholder, on_delete=models.CASCADE,null=True)
    gross_amount = models.PositiveIntegerField(null=True)
    discount = models.PositiveIntegerField(null=True)
    net_amount = models.PositiveIntegerField(null=True)
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Issued')
    total_amount = models.PositiveIntegerField(null=True)
    pending_amount = models.PositiveIntegerField(null=True)
    order_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
            return f'{self.order_number}'
        
    # when a order is created update the total amount and pending amount with value of net amount
    def save(self, *args, **kwargs):
      if self.pk is None:
        self.total_amount = self.net_amount
        self.pending_amount = self.net_amount
      super().save(*args, **kwargs)
        
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_time_of_order = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} of {self.product.name} for {self.order}"
    
    def save(self, *args, **kwargs):
        # Update product quantity if the order type is 'PO' (Purchase Order)
        if self.order and self.order.order_type == 'PO':
            self.product.qty_purchased += self.quantity
            self.product.qty_available += self.quantity
        elif self.order and self.order.order_type == 'SO':
            self.product.qty_purchased -= self.quantity
            self.product.qty_available -= self.quantity
        self.product.save()
            
        super().save(*args, **kwargs)
    
class Return(WebBaseModel):
    RETURN_TYPE_CHOICES = [
        ('PR', 'Purchase Return'),
        ('SR', 'Sales Return'),
    ]

    return_type = models.CharField(max_length=2, choices=RETURN_TYPE_CHOICES)
    original_order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='returns')
    date = models.DateField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    def __str__(self):
        return f" return for Order {self.original_order.id} on {self.date}"
    
    def save(self, *args, **kwargs):
        # Start an atomic transaction
        with transaction.atomic():
            # Check if the instance is being created (pk is None means it’s new)
            if self.pk is None:
                # Update the Order instance by subtracting the return total_amount
                Order.objects.filter(pk=self.original_order.pk).update(
                    total_amount=F('total_amount') - self.total_amount,
                    pending_amount=F('pending_amount') - self.total_amount
                )

            # Save the Return instance
            super().save(*args, **kwargs)
    

class ReturnItem(models.Model):
    return_order = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_return = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    def __str__(self):
        return f"Return of {self.quantity} of {self.product.name} for Return {self.return_order.id}"
    
    def save(self, *args, **kwargs):
        # Update product quantity based on return order
        if self.return_order and self.return_order.return_type == 'PR':
            self.product.qty_purchased -= self.quantity
            self.product.qty_available -= self.quantity
        elif self.return_order and self.return_order.return_type == 'SR':
            self.product.qty_purchased += self.quantity
            self.product.qty_available += self.quantity
        self.product.save()
        
        super().save(*args, **kwargs)
    
    
class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('BANK', 'Bank Transfer'),
        ('OTHER', 'Other'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    company = models.ForeignKey(Stakeholder, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.PositiveIntegerField(null=True, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='CASH')
    
    def __str__(self):
        return f"Payment of {self.amount} for Order {self.order.id} on {self.payment_date}"
    
    
    #when a payment instance is created with a amount minus the amount from order model field pending amount
    def save(self, *args, **kwargs):
        with transaction.atomic():
         Order.objects.filter(pk=self.order.pk).update(
            pending_amount=self.order.pending_amount - self.amount
         )
         self.order.refresh_from_db()
         if self.order.pending_amount == 0:
             Order.objects.filter(pk=self.order.pk).update(
                order_status='Closed'
            )
         super().save(*args, **kwargs)
    

