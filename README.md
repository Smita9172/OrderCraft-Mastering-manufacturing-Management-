# OrderCraft

OrderCraft is a manufacturing operations and ERP-style web application. It manages customer orders, bills of materials, inventory, procurement, invoices, payments, analytics, users, and audit logs.

This document describes the technologies and behavior implemented in the project source code.

## Technology stack

| Area | Technology actually used | Project role |
|---|---|---|
| Backend language | Python | Implements the server, models, business rules, API views, migrations, and seed command. |
| Backend framework | Django 6.1.3 | Provides URL routing, templates, ORM, sessions, authentication, admin, migrations, WSGI, and ASGI support. |
| API framework | Django REST Framework 3.18.3 | Provides JSON APIs, serializers, viewsets, routers, custom actions, and API responses. |
| Frontend | HTML5, CSS3, and vanilla JavaScript | Provides the landing page, authentication pages, ERP dashboard, forms, tables, modals, and client-side behavior. |
| HTTP client | Browser Fetch API | Sends JSON requests from the frontend to `/api/...` endpoints. |
| Charts | Chart.js from jsDelivr CDN | Displays revenue, order-status, inventory, and product analytics charts. |
| Icons | Font Awesome 6.4.0 from cdnjs | Provides interface and dashboard icons. |
| Font | Google Fonts Inter | Provides the main user-interface font. |
| Database ORM | Django ORM | Maps application models to relational database tables and performs queries, relationships, aggregation, and transactions. |
| Cloud database option | PostgreSQL hosted by Supabase | Optional production database configured through Supabase connection settings. |
| PostgreSQL driver | psycopg 3 | Allows Django to connect to PostgreSQL. |
| Local database option | SQLite | Automatic local fallback when PostgreSQL is not configured or is unavailable. |
| Environment configuration | python-dotenv | Loads `.env` values such as database credentials, `SECRET_KEY`, `DEBUG`, and SQLite override settings. |
| Database URL parsing | dj-database-url | Parses `DATABASE_URL` when PostgreSQL is configured through a connection URL. |
| CORS | django-cors-headers | Adds CORS middleware for API requests. |
| Authentication | Django authentication and sessions | Handles password hashing, login, logout, session cookies, password validation, and current-user lookup. |
| Security | Django CSRF middleware | Protects state-changing requests; the frontend sends the CSRF cookie value in `X-CSRFToken`. |
| Administration | Django Admin | Provides the `/admin/` management interface for registered models. |

There is no React, Vue, Angular, TypeScript, Node.js package setup, npm build system, Bootstrap, Tailwind CSS, Axios, JWT, OAuth, GraphQL, Celery, Redis, Docker, or Supabase SDK in the source tree.

## Project structure

```text
ordercraft/
├── backend/
│   ├── apps/
│   │   ├── accounts/       Users, authentication, roles, and audit logs
│   │   ├── analytics/      Dashboard metrics, charts, and CSV exports
│   │   ├── bom/            Products, raw materials, BOMs, and stock logic
│   │   ├── invoices/       Invoices, invoice items, and payment actions
│   │   ├── orders/         Customers, sales orders, and order items
│   │   ├── payments/       Customer/vendor payments and summaries
│   │   └── procurement/    Vendors, purchase orders, GRNs, and communications
│   ├── ordercraft_core/    Django settings, URLs, WSGI, and ASGI
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── *.html              Django-rendered HTML pages
│   ├── css/                Landing, login, and dashboard styles
│   └── js/                 API service layer and dashboard controller
├── supabase_schema.sql     Optional PostgreSQL schema script
└── .env.example            Environment variable template
```

## Application modules

| Module | Main responsibility |
|---|---|
| Accounts | Custom users, registration, login, logout, roles, and audit logs |
| Orders | Customers, sales orders, order items, status updates, material checks, and invoice creation |
| BOM and inventory | Products, raw materials, BOMs, stock adjustments, material costs, and shortage detection |
| Procurement | Vendors, purchase orders, goods receipt notes, inventory receiving, and vendor communications |
| Invoices | Invoices, invoice items, tax totals, payment status, amount paid, and amount due |
| Payments | Customer/vendor payments, payment summaries, and reconciliation workflows |
| Analytics | Dashboard metrics, chart data, top products, inventory summaries, and CSV exports |

## API structure

| Prefix | Purpose |
|---|---|
| `/api/accounts/` | Authentication, users, and audit logs |
| `/api/orders/` | Customers and sales orders |
| `/api/bom/` | Products, raw materials, BOMs, and BOM explosion |
| `/api/procurement/` | Vendors, purchase orders, GRNs, and communications |
| `/api/invoices/` | Invoices and invoice actions |
| `/api/payments/` | Payments and payment summaries |
| `/api/analytics/` | Dashboard metrics, charts, and CSV exports |

The frontend uses JSON requests through the shared API service in `frontend/js/api.js`.

## Authentication and permissions

- Django session authentication is used for normal login sessions.
- DRF also has `BasicAuthentication` configured.
- CSRF protection is enabled for browser requests.
- The `/app/` and `/dashboard/` pages require a logged-in Django user.
- The current REST API default permission is `AllowAny`; strict role-based endpoint authorization is therefore not currently enforced by the API.
- User roles are stored and displayed, but role values should not be described as complete backend RBAC enforcement.
- CORS is configured with `CORS_ALLOW_ALL_ORIGINS = True` and `CORS_ALLOW_CREDENTIALS = True`, which is suitable for development but should be restricted before production deployment.

## Database configuration

The backend supports two database paths:

1. PostgreSQL through Supabase, using either individual `SUPABASE_DB_*` variables or `DATABASE_URL`.
2. Local SQLite fallback at `backend/db.sqlite3` when PostgreSQL is not active.

The database choice is made in `backend/ordercraft_core/settings.py`. The included `supabase_schema.sql` is a PostgreSQL schema script for optional direct deployment through a Supabase SQL editor. The application itself connects through Django's database layer, not through a Supabase SDK.

## Setup and run

From the project directory:

```bash
cd backend
python -m venv .venv
```

Activate the environment according to your operating system, then install dependencies:

```bash
pip install -r requirements.txt
```

For local development, leave PostgreSQL variables unset and Django will use SQLite. For Supabase PostgreSQL, copy `.env.example` to `.env` and provide either `DATABASE_URL` or the individual `SUPABASE_DB_*` variables.

Apply migrations:

```bash
python manage.py migrate
```

Optionally seed demonstration data:

```bash
python manage.py seed_data
```

Start the development server:

```bash
python manage.py runserver
```

Available pages:

- `/` — landing page
- `/login/` — login page
- `/register/` — registration page
- `/app/` — authenticated ERP dashboard
- `/admin/` — Django administration

## Static assets

Django serves the frontend files from the `frontend/` directory through Django static-file configuration. The dashboard loads Chart.js, Font Awesome, and Inter from external CDNs, while project-specific CSS and JavaScript are served locally.

## Important implementation notes

- The project is a Django monolith that serves the frontend templates and the REST API.
- The frontend is not a separately compiled SPA.
- There is no `package.json`; frontend dependencies are loaded through CDN links.
- PostgreSQL/Supabase support is implemented through Django database configuration and `psycopg`, not through a Supabase client library.
- SQLite is a fallback database configuration, not a separate application API.
- The project includes Django migrations and a custom `seed_data` management command.
