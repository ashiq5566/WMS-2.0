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
    name = models.CharField(max_length=100, null=True)
    company_name = models.CharField(max_length=150, null=True, blank=True)
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    shipping_address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True, default='India')
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    alternate_phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    website = models.CharField(max_length=150, null=True, blank=True)
    type = models.CharField(choices=STAKEHOLDER_TYPES, max_length=128, null=True, blank=True)
    tax_id = models.CharField(max_length=50, null=True, blank=True) # GSTIN / Tax ID
    pan_number = models.CharField(max_length=50, null=True, blank=True)
    payment_terms = models.CharField(max_length=100, null=True, blank=True, default='Net 30')
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)
    opening_balance = models.IntegerField(null=True, blank=True, default=0)
    notes = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Synchronize is_active and is_deleted
        if self.is_deleted and self.is_active:
            self.is_active = False
        elif not self.is_deleted and not self.is_active:
            self.is_deleted = True

        # Auto-generate stakeholder_id if not present
        if not self.stakeholder_id:
            prefix = 'CUST' if self.type == 'Customer' else ('SUPP' if self.type == 'Supplier' else 'STK')
            last_obj = Stakeholder.objects.filter(type=self.type).exclude(stakeholder_id__isnull=True).order_by('-id').first()
            next_num = 1
            if last_obj and last_obj.stakeholder_id and '-' in last_obj.stakeholder_id:
                try:
                    parts = last_obj.stakeholder_id.split('-')
                    next_num = int(parts[-1]) + 1
                except (ValueError, IndexError):
                    next_num = (last_obj.id or 0) + 1
            elif last_obj and last_obj.id:
                next_num = last_obj.id + 1
            self.stakeholder_id = f"{prefix}-{next_num:04d}"

        super().save(*args, **kwargs)

    @property
    def total_pending_amount(self):
        pending = self.order_set.filter(pending_amount__gt=0).aggregate(total=models.Sum('pending_amount'))['total'] or 0
        return pending + (self.opening_balance or 0)

    @property
    def total_setteled_amount(self):
        return self.payment_set.aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def total_orders_count(self):
        return self.order_set.count()

    @property
    def total_sales_amount(self):
        return self.order_set.aggregate(total=models.Sum('total_amount'))['total'] or 0

    @property
    def total_returns_count(self):
        # Return records linked through original_order
        try:
            from inventory.models import Return
            return Return.objects.filter(original_order__stakeholder=self).count()
        except Exception:
            return 0

    @property
    def next_bill_to_clear(self):
        bill = self.order_set.filter(pending_amount__gt=0).order_by('date_added').first()
        if bill:
            return {'pending_amount': bill.pending_amount, 'order_number': bill.order_number}
        return {'pending_amount': 0, 'order_number': None}

    def __str__(self):
        return f'{self.name or self.stakeholder_id or self.id}'


# class Supplier(WebBaseModel):
#     supplier_id = models.CharField(max_length=100, null=True, unique=True)
#     supplier_name = models.CharField(max_length=100, null=True)
#     supplier_address = models.CharField(max_length=200, null=True)
#     supplier_mobile = models.CharField(max_length=15,null=True)
    
#     def __str__(self):
#             return self.supplier_name