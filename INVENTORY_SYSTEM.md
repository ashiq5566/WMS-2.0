# Warehouse Management System - Inventory Model (ERP-style)

## Overview

The inventory system has been redesigned to follow industry-standard ERP practices (similar to SAP, Oracle, Odoo) with a focus on single source of truth and complete audit trail.

## Core Concepts

### 1. **ProductSize Model** - Single Source of Truth

- **Field**: `stock` (integer)
- Tracks the actual inventory level for each product size
- Updated with every purchase/sales order
- No redundant fields

```python
class ProductSize:
    product: ForeignKey(Product)
    size: Integer
    price: BigInteger (cost price)
    stock: Integer (real-time quantity)
    is_available: Boolean
```

### 2. **Product Model** - Simplified

- **Removed**: `qty_purchased`, `qty_sold` (redundant)
- **Kept**: Basic product info, pricing, unit of measurement
- **Added Property**: `qty_available` (calculated from ProductSize.stock)

```python
@property
def qty_available(self):
    """Calculated from all product sizes"""
    return sum(size.stock for size in self.sizes.all())
```

### 3. **StockMovement Model** - Complete Audit Trail (NEW)

Tracks all inventory changes for compliance and reporting, similar to SAP MM (Materials Management).

```python
class StockMovement:
    product_size: ForeignKey(ProductSize)
    order: ForeignKey(Order)  # Reference to original transaction
    movement_type: Choice [
        'PURCHASE' - Purchase Order Receipt
        'SALE' - Sales Order Shipment
        'RETURN_SALE' - Sales Return
        'RETURN_PURCHASE' - Purchase Return
        'ADJUSTMENT' - Manual Stock Adjustment
        'TRANSFER' - Internal Transfer
    ]
    quantity: Integer (positive for inbound, negative for outbound)
    reference: CharField (Order number)
    notes: TextField
    created_at: DateTime (automatic)
    created_by: ForeignKey(User)
```

### 4. **OrderItem Model** - Updated

Now includes ProductSize for size-based ordering.

```python
class OrderItem:
    order: ForeignKey(Order)
    product: ForeignKey(Product)
    product_size: ForeignKey(ProductSize)  # NEW - tracks size
    quantity: Integer
    price_at_time_of_order: Decimal
    total: Decimal
```

## Inventory Flows

### A. Purchase Order (PO) Flow

```
1. Create Order (type='PO', order_type='Purchase Order')
2. Add OrderItems with ProductSize
3. On OrderItem.save():
   - ProductSize.stock += quantity
   - Create StockMovement(type='PURCHASE', quantity=+qty)
   - Update qty_available property
```

### B. Sales Order (SO) Flow

```
1. Create Order (type='SO', order_type='Sales Order')
2. Add OrderItems with ProductSize
3. On OrderItem.save():
   - ProductSize.stock -= quantity
   - Create StockMovement(type='SALE', quantity=-qty)
   - Update qty_available property
```

### C. Sales Return Flow

```
1. Create Return(type='SR')
2. On Return.save():
   - ProductSize.stock += returned_quantity
   - Create StockMovement(type='RETURN_SALE', quantity=+qty)
   - Adjust order pending_amount
```

### D. Purchase Return Flow

```
1. Create Return(type='PR')
2. On Return.save():
   - ProductSize.stock -= returned_quantity
   - Create StockMovement(type='RETURN_PURCHASE', quantity=-qty)
   - Adjust order pending_amount
```

## Database Schema

### Product Table (Simplified)

```
id, created_at, updated_at, is_deleted
product_id, name, selling_price, price_at_time_of_purchase
status, unit, image, description
```

### ProductSize Table (Real-time Stock)

```
id, product_id, size, price, stock, is_available
```

### StockMovement Table (Audit Trail)

```
id, product_size_id, order_id, movement_type, quantity
reference, notes, created_at, created_by_id
```

### OrderItem Table (Transaction Detail)

```
id, order_id, product_id, product_size_id
quantity, price_at_time_of_order, total
```

## API Response Example

### Get Product with Stock

```json
{
  "id": 1,
  "product_id": "PR1",
  "name": "T-Shirt",
  "unit": "Pieces",
  "selling_price": 500,
  "qty_available": 145,
  "sizes": [
    {
      "id": 1,
      "size": "S",
      "price": 300,
      "stock": 50,
      "is_available": true
    },
    {
      "id": 2,
      "size": "M",
      "price": 350,
      "stock": 45,
      "is_available": true
    },
    {
      "id": 3,
      "size": "L",
      "price": 400,
      "stock": 50,
      "is_available": true
    }
  ]
}
```

### Get Stock Movement Audit Trail

```json
{
  "id": 1,
  "product_name": "T-Shirt - Size M",
  "order": 101,
  "movement_type": "PURCHASE",
  "quantity": 100,
  "reference": "PO-001",
  "created_at": "2024-01-15T10:30:00Z",
  "created_by": "admin"
}
```

## Benefits of This Design

1. **Single Source of Truth**: Stock only stored in ProductSize
2. **Audit Trail**: Every change tracked in StockMovement
3. **No Discrepancy**: qty_available calculated from actual stock
4. **Scalability**: Supports unlimited stock movements
5. **Compliance**: Complete transaction history
6. **Performance**: Direct stock queries without aggregation
7. **Size-Based**: Each size tracked independently
8. **ERP Standard**: Follows SAP/Odoo/Oracle patterns

## Comparison with Old System

### Old Approach (Removed)

- Product.qty_available (denormalized)
- Product.qty_sold (redundant)
- Product.qty_purchased (redundant)
- No audit trail
- Prone to discrepancy
- Hard to debug

### New Approach (Current)

- ProductSize.stock (source of truth)
- Product.qty_available (computed property)
- StockMovement (complete audit)
- Always accurate
- Compliant
- Easy to debug

## Migration Notes

- Removed fields: qty_purchased, qty_sold from Product
- New relationship: OrderItem → ProductSize
- New model: StockMovement for audit trail
- Database migration: 0028_simplify_inventory_model
- Zero data loss: Historical orders preserved
