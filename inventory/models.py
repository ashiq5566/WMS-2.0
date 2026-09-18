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
    price_at_time_of_purchase = models.PositiveBigIntegerField(null=True, blank=True)
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
      if not self.order_number:
        import uuid
        prefix = self.order_type if self.order_type else 'ORD'
        self.order_number = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
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
    RETURN_STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending Approval', 'Pending Approval'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Processed', 'Processed'),
        ('Completed', 'Completed'),
    ]

    return_type = models.CharField(max_length=2, choices=RETURN_TYPE_CHOICES)
    return_status = models.CharField(max_length=20, choices=RETURN_STATUS_CHOICES, default='Completed')
    original_order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='returns')
    date = models.DateField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    stock_adjusted = models.BooleanField(default=False)

    def __str__(self):
        return f"Return for Order {self.original_order.id} ({self.return_status}) on {self.date}"

    def save(self, *args, **kwargs):
        # Start an atomic transaction
        with transaction.atomic():
            # Check if status warrants inventory/financial adjustments and has not yet been applied
            is_approved = self.return_status in ['Approved', 'Processed', 'Completed']
            if is_approved and not self.stock_adjusted:
                order = Order.objects.select_for_update().get(pk=self.original_order.pk)
                ret_amount = int(self.total_amount or 0)
                new_total = max(0, (order.total_amount or 0) - ret_amount)
                new_pending = max(0, (order.pending_amount or 0) - ret_amount)
                Order.objects.filter(pk=order.pk).update(
                    total_amount=new_total,
                    pending_amount=new_pending
                )
                self.stock_adjusted = True

            super().save(*args, **kwargs)


class ReturnItem(models.Model):
    CONDITION_CHOICES = [
        ('Good', 'Good'),
        ('Damaged', 'Damaged'),
        ('Expired', 'Expired'),
        ('Defective', 'Defective'),
        ('Wrong Item', 'Wrong Item'),
    ]

    return_order = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_size = models.ForeignKey(ProductSize, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price_at_return = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='Good')
    reason = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Return of {self.quantity} of {self.product.name} ({self.condition}) for Return {self.return_order.id}"

    def save(self, *args, **kwargs):
        """
        Handle stock adjustments for returns using StockMovement and condition validation
        """
        is_new = self.pk is None
        if is_new and self.quantity and self.price_at_return and self.total is None:
            self.total = self.quantity * self.price_at_return

        is_approved = self.return_order and self.return_order.return_status in ['Approved', 'Processed', 'Completed']

        if is_new and is_approved and self.product_size:
            if self.return_order.return_type == 'SR':
                # Sales Return: only restock sellable goods (Good, Wrong Item)
                # Damaged, Expired, Defective goods go into quarantine without inflating sellable stock
                if self.condition in ['Good', 'Wrong Item']:
                    self.product_size.stock += self.quantity
                    self.product_size.save()
                    movement_type = 'RETURN_SALE'
                    qty_delta = self.quantity
                else:
                    movement_type = 'RETURN_SALE'
                    qty_delta = 0  # Quarantined / Written-off
            elif self.return_order.return_type == 'PR':
                # Purchase Return: decrease stock from warehouse
                self.product_size.stock -= self.quantity
                self.product_size.save()
                movement_type = 'RETURN_PURCHASE'
                qty_delta = -self.quantity

            # Create stock movement record for audit trail
            StockMovement.objects.create(
                product_size=self.product_size,
                order=self.return_order.original_order,
                movement_type=movement_type,
                quantity=qty_delta,
                reference=self.return_order.original_order.order_number,
                notes=f"Return {self.return_order.return_type} ({self.condition}) - {self.reason or 'Processed'}"
            )

        super().save(*args, **kwargs)
    
    
class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('BANK', 'Bank Transfer'),
        ('OTHER', 'Other'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('INBOUND', 'Customer Receipt'),
        ('OUTBOUND', 'Supplier Payment'),
        ('REFUND', 'Refund / Credit'),
    ]

    STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    ]

    payment_number = models.CharField(max_length=100, null=True, blank=True, unique=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='INBOUND')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Completed')
    reference = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    company = models.ForeignKey(Stakeholder, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.PositiveIntegerField(null=True, blank=True)
    payment_date = models.DateTimeField()
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='CASH')
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        partner = self.company.name if self.company else (self.order.stakeholder.name if self.order and self.order.stakeholder else "General")
        return f"{self.payment_number or 'Payment'} - ₹{self.amount} ({partner})"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            is_new = self.pk is None

            # Validate positive amount
            if self.amount is None or self.amount <= 0:
                raise ValueError("Payment amount must be greater than zero.")

            # Invert or infer payment type if not explicitly set
            if self.order:
                if self.order.order_type == 'PO':
                    self.payment_type = 'OUTBOUND'
                elif not self.payment_type or self.payment_type == 'OUTBOUND':
                    self.payment_type = 'INBOUND'
            elif self.company and not self.payment_type:
                if self.company.type == 'Supplier':
                    self.payment_type = 'OUTBOUND'
                else:
                    self.payment_type = 'INBOUND'

            # Auto-generate payment_number if empty
            if not self.payment_number:
                prefix = 'PAY-' if self.payment_type == 'OUTBOUND' else ('REF-' if self.payment_type == 'REFUND' else 'REC-')
                last_pay = Payment.objects.filter(payment_number__startswith=prefix).order_by('-id').first()
                next_seq = 1
                if last_pay and last_pay.payment_number and '-' in last_pay.payment_number:
                    try:
                        parts = last_pay.payment_number.split('-')
                        next_seq = int(parts[-1]) + 1
                    except (ValueError, IndexError):
                        next_seq = (last_pay.id or 0) + 1
                elif last_pay and last_pay.id:
                    next_seq = last_pay.id + 1
                else:
                    next_seq = Payment.objects.count() + 1
                self.payment_number = f"{prefix}{next_seq:05d}"

            # Ensure company is linked from order
            if not self.company and self.order and self.order.stakeholder:
                self.company = self.order.stakeholder

            # Only deduct balances on newly created payments
            if is_new and self.status == 'Completed':
                if self.order is not None:
                    order_instance = Order.objects.select_for_update().get(pk=self.order.pk)
                    if self.amount > order_instance.pending_amount:
                        raise ValueError(f"Payment amount (₹{self.amount}) exceeds outstanding order balance (₹{order_instance.pending_amount}).")
                    order_instance.pending_amount = max(0, order_instance.pending_amount - self.amount)
                    if order_instance.pending_amount == 0:
                        order_instance.order_status = 'Closed'
                    order_instance.save()
                elif self.company is not None:
                    if (self.company.opening_balance or 0) > 0:
                        deduct = min(self.company.opening_balance, self.amount)
                        self.company.opening_balance -= deduct
                        self.company.save()
                        rem = self.amount - deduct
                        if rem > 0:
                            order_instance = Order.objects.select_for_update().filter(stakeholder=self.company, pending_amount__gt=0).order_by('date_added').first()
                            if order_instance:
                                alloc = min(order_instance.pending_amount, rem)
                                order_instance.pending_amount = max(0, order_instance.pending_amount - alloc)
                                if order_instance.pending_amount == 0:
                                    order_instance.order_status = 'Closed'
                                order_instance.save()
                                self.order = order_instance
                    else:
                        order_instance = Order.objects.select_for_update().filter(stakeholder=self.company, pending_amount__gt=0).order_by('date_added').first()
                        if order_instance:
                            alloc = min(order_instance.pending_amount, self.amount)
                            order_instance.pending_amount = max(0, order_instance.pending_amount - alloc)
                            if order_instance.pending_amount == 0:
                                order_instance.order_status = 'Closed'
                            order_instance.save()
                            self.order = order_instance

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
