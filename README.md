# Warehouse Management System Backend

This repository contains the Django backend for a warehouse management system. It exposes REST APIs for authentication, stakeholders, products, orders, returns, payments, and cart management, and it can also serve a built frontend from the same project.

## Stack

- Python 3
- Django 5
- Django REST Framework
- SQLite by default
- JWT authentication with Simple JWT
- WhiteNoise for static assets

## Project Structure

- `accounts/`: custom user model and stakeholder records
- `inventory/`: products, orders, returns, payments, carts
- `api/v1/`: versioned REST API views, serializers, and routes
- `general/`: shared abstract base model
- `frontmatter/`: template entrypoint for the root page
- `wms/`: Django settings and root URL configuration
- `wms-frontend/`: frontend app currently referenced by Django templates/static settings
- `website/`: separate frontend site folder

## Core Features

- Custom user model (`accounts.User`)
- JWT login and refresh endpoints
- Stakeholder management for customers and suppliers
- Product catalog with optional size-based pricing and stock
- Purchase orders and sales orders
- Returns and return items
- Payment tracking against orders or stakeholder balances
- Cart and cart item APIs

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
pip install djangorestframework-simplejwt
```

3. Apply migrations:

```bash
python3 manage.py migrate
```

4. Start the development server:

```bash
python3 manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

## Default Configuration

- Database: SQLite (`db.sqlite3`)
- Auth user model: `accounts.User`
- CORS: open to all origins
- Media files: served from `/media/`
- Static files: collected into `var/static_root/`
- Root URL: serves `frontmatter/index.html`

## Authentication

JWT endpoints:

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`

There is also a session-based login endpoint:

- `POST /api/accounts/login/`

For protected endpoints, send:

```http
Authorization: Bearer <access_token>
```

## Main API Endpoints

### Accounts

- `GET|POST /api/accounts/stakeholders/`
- `GET|PATCH|PUT|DELETE /api/accounts/stakeholders/<id>/`

### Inventory

- `GET|POST /api/inventory/products/`
- `GET|PATCH|PUT|DELETE /api/inventory/products/<id>/`
- `GET|POST /api/inventory/orders/`
- `GET|PATCH|PUT|DELETE /api/inventory/orders/<id>/`
- `GET /api/inventory/orders/get_total_by_stakeholders/`
- `GET|POST /api/inventory/order-items/`
- `GET|POST /api/inventory/returns/`
- `GET|POST /api/inventory/return-items/`
- `GET|POST /api/inventory/payments/`
- `GET|POST /api/inventory/cart/`
- `GET|POST /api/inventory/cart-items/`

## Request Notes

- Order creation expects a payload with `order` and `items`.
- Return creation expects a payload with `return` and `items`.
- Product creation uses `ProductCreateSerializer`, where `sizes` is sent as a JSON string.
- Product listing uses a richer serializer and includes nested size data.

## Filtering and Search

The API supports filtering/searching on several endpoints through Django REST Framework and `django-filter`.

Examples:

- Orders can be filtered by `order_type`, `order_status`, `order_date`, and stakeholder.
- Payments can be filtered by order, stakeholder, order type, and `payment_date`.
- Stakeholders support search by name, type, address, mobile, and email.

## Frontend Integration

The Django template configuration points to the built assets from `wms-frontend/dist`. If you want Django to serve the frontend directly, build that app first so the `dist` directory exists.

This repository also contains a separate `website/` folder, which appears to be another frontend codebase and is not wired into the backend settings by default.

## Seed / Sample Data

The repository includes JSON files that can be used as sample reference data:

- `products.json`
- `orders.json`
- `order-items.json`
- `payments.json`
- `stakeholders.json`

## Development Notes

- `DEBUG` is enabled in the current settings.
- `ALLOWED_HOSTS` is set to `["*"]`.
- The current settings file contains a hardcoded secret key, which should be replaced for production use.
- `psycopg2-binary` is listed in dependencies, but PostgreSQL is not configured in `wms/settings.py`.

## Useful Commands

```bash
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py collectstatic
python3 manage.py test
```
