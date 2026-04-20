# PanAfric Store - Backend

Pan-African e-commerce backend with multi-currency rate locking and settlement.

**Tech Stack**: Django + DRF + PostgreSQL (Neon) + JWT

## Why Django?
I chose Django because it provides a mature ORM, built-in admin, excellent security defaults, and first-class support for background tasks — perfect for strict rate-locking and settlement logic required by the brief.

## Features Implemented
- Full auth with role-based JWT expiry (24h customer / 7d merchant)
- Exchange rate engine (Frankfurter API + 30-min cache + stale fallback)
- Product CRUD with live currency conversion
- Cart (price calculated at read time only)
- Checkout with **rate locking**, settlement calculation, and payout notifications
- Role-based access control + 403 on unauthorized access
- Rate limiting (5/min checkout, 10/min login)
- 12+ meaningful tests covering all critical business rules
- Soft delete on products

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py runserver