from django.db import models
from django.db import transaction
from django.db.models import F

from general.models import WebBaseModel
from accounts.models import Stakeholder, User

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
    status = models.BooleanField(default=False)
    unit = models.CharField(choices=UNIT_CHOICES, null=True, blank=True, max_length=100)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.product_id:
            self.product_id = f"PR{self.pk}"
            type(self).objects.filter(pk=self.pk).update(product_id=self.product_id)
    
    @property
    def qty_available(self):
        """Calculate available stock from all product sizes"""
        return sum(size.stock for size in self.sizes.all())
    
    def __str__(self):
        return  self.name
    
class ProductSize(models.Model):
    product = models.ForeignKey(
        Product,
        related_name="sizes",
        on_delete=models.CASCADE
    )
    size = models.PositiveIntegerField()  # 1,2,3...25
    price = models.PositiveBigIntegerField()
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.name} - {self.size}"

    
class StockMovement(models.Model):
    """
    Tracks all inventory movements for audit trail.
    Similar to SAP/Odoo stock movements.
    """
    MOVEMENT_TYPE_CHOICES = [
        ('PURCHASE', 'Purchase Order Receipt'),
        ('SALE', 'Sales Order Shipment'),
        ('RETURN_SALE', 'Sales Return'),
        ('RETURN_PURCHASE', 'Purchase Return'),
        ('ADJUSTMENT', 'Stock Adjustment'),
        ('TRANSFER', 'Internal Transfer'),
    ]
    
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, related_name='movements')
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.IntegerField()  # Positive for inbound, negative for outbound
    reference = models.CharField(max_length=100, null=True, blank=True)  # Order number, reference
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.product_size} - {self.movement_type} - {self.quantity}"
    
    class Meta:
        ordering = ['-created_at']


    
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
    
    @property
    def total_sales_orders(self):
        return Order.objects.filter(order_type='SO', is_deleted=False).count()
    
    @property
    def total_purchase_orders(self):
        return Order.objects.filter(order_type='PO', is_deleted=False).count()
    
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
    product_size = models.ForeignKey(ProductSize, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price_at_time_of_order = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} of {self.product.name} (Size: {self.product_size.size if self.product_size else 'N/A'}) for {self.order}"
    
    def save(self, *args, **kwargs):
        """
        Update ProductSize stock when order is created/saved.
        This follows ERP patterns like SAP/Odoo.
        """
        is_new = self.pk is None
        
        if is_new and self.order and self.product_size:
            if self.order.order_type == 'PO':
                # Purchase Order: increase stock
                self.product_size.stock += self.quantity
                movement_type = 'PURCHASE'
            elif self.order.order_type == 'SO':
                # Sales Order: decrease stock
                self.product_size.stock -= self.quantity
                movement_type = 'SALE'
            
            self.product_size.save()
            
            # Create stock movement record for audit trail
            StockMovement.objects.create(
                product_size=self.product_size,
                order=self.order,
                movement_type=movement_type,
                quantity=self.quantity if self.order.order_type == 'PO' else -self.quantity,
                reference=self.order.order_number,
            )
            
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
    product_size = models.ForeignKey(ProductSize, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price_at_return = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    def __str__(self):
        return f"Return of {self.quantity} of {self.product.name} for Return {self.return_order.id}"
    
    def save(self, *args, **kwargs):
        """
        Handle stock adjustments for returns using StockMovement
        """
        is_new = self.pk is None
        
        if is_new and self.return_order and self.product_size:
            if self.return_order.return_type == 'SR':
                # Sales Return: increase stock
                self.product_size.stock += self.quantity
                movement_type = 'RETURN_SALE'
            elif self.return_order.return_type == 'PR':
                # Purchase Return: decrease stock
                self.product_size.stock -= self.quantity
                movement_type = 'RETURN_PURCHASE'
            
            self.product_size.save()
            
            # Create stock movement record for audit trail
            StockMovement.objects.create(
                product_size=self.product_size,
                order=self.return_order.original_order,
                movement_type=movement_type,
                quantity=self.quantity if self.return_order.return_type == 'SR' else -self.quantity,
                reference=self.return_order.original_order.order_number,
                notes=f"Return for {self.return_order.return_type}"
            )
        
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
    payment_date = models.DateTimeField()
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='CASH')
    
    def __str__(self):
        return f"Payment of {self.amount} for Order {self.company.name} on {self.payment_date}"
    
    
    #when a payment instance is created with a amount minus the amount from order model field pending amount
    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.order is not None:
                order_instance = Order.objects.get(pk=self.order.pk)
                order_instance.pending_amount=self.order.pending_amount - self.amount
                order_instance.save()
            elif self.order is None:
                if self.company is not None:
                    if self.company.opening_balance > 0:
                        self.company.opening_balance -= self.amount
                        self.company.save()
                    else:
                        order_instance = Order.objects.filter(stakeholder=self.company, order_status='Issued').order_by('date_added').first()
                        order_instance.pending_amount=order_instance.pending_amount - self.amount
                        self.order = order_instance
                        order_instance.save()
                    
                        order_instance.refresh_from_db()
                        if order_instance.pending_amount == 0:
                            order_instance.order_status='Closed'
                            order_instance.save()
            super().save(*args, **kwargs)
    
    
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart ({self.user.username})"


class CartItem(models.Model):
    cart = models.ForeignKey('Cart', related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

    @property
    def total_price(self):
        return self.product.selling_price * self.quantity
