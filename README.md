# OrderCraft: Mastering Manufacturing Management ERP
> **A Comprehensive Enterprise Manufacturing & Operations Management System**  
> *Developed for Major College Academic Evaluation*

---

## 🏭 Project Overview
**OrderCraft** is an enterprise-grade Manufacturing Resource Planning (MRP II) and Enterprise Resource Planning (ERP) suite tailored for modern discrete manufacturing plants (such as precision machinery, electric motors, pumps, and engineered assemblies).

The system seamlessly unifies the end-to-end manufacturing lifecycle: from customer sales order booking, multi-level Bill of Materials (BOM) explosion, inventory management, supplier procurement, goods receipt (GRN), GST-compliant commercial tax invoicing, and dual-entry payment reconciliation, to real-time executive analytics and Role-Based Access Control (RBAC) with an immutable audit log.

---

## 🛠️ Technology Stack
| Layer | Technology | Description |
|---|---|---|
| **Frontend** | HTML5, Modern CSS3, Vanilla JavaScript (ES6+) | Fully responsive single-page manufacturing portal with custom CSS variables, modal dialogs, real-time search/filtering, and print-ready tax invoice sheets. |
| **Data Visualization** | Chart.js 4 | Interactive charts for monthly revenue trends, order status distribution, and inventory category valuation. |
| **Backend** | Python 3.13, Django 6.1 | Modular architecture with 7 distinct Django applications, robust relational ORM, and automated reconciliation hooks. |
| **API** | Django REST Framework (DRF) | RESTful API endpoints with standard CRUD, custom action routes, and JSON payloads. |
| **Database** | **Supabase PostgreSQL** *(with SQLite Fallback)* | High-performance PostgreSQL database hosted on Supabase, featuring full relational integrity, foreign keys, and indexed queries. |

---

## 🧩 The 7 Core Manufacturing Modules

### 1. Order Booking Module (`apps.orders`)
- **Customer Master**: Centralized registry of industrial clients with GSTIN, billing, and plant shipping addresses.
- **Sales Orders (SO)**: Auto-generating order numbers (`SO-2026-0001`), priorities (`URGENT`, `HIGH`, `MEDIUM`, `LOW`), order/due dates, and custom engineering specifications.
- **Dynamic Line Items**: Multi-item order configuration with automated subtotal, GST (18%), discount deductions, and grand total calculations.
- **Production Pipeline**: Lifecycle status progression (`DRAFT` → `CONFIRMED` → `IN_PRODUCTION` → `READY_FOR_DISPATCH` → `DISPATCHED` → `DELIVERED`).
- **1-Click Invoice Generation**: Direct conversion of confirmed sales orders into formal tax invoices.

### 2. Bill of Material (BOM) Module (`apps.bom`)
- **Raw Materials Catalog**: Real-time warehouse inventory tracking units of measurement (`KG`, `MTR`, `PCS`, `LTR`, `SQM`, `SET`), standard purchase costs, current physical stock, reorder levels, and warehouse bay/rack locations.
- **Finished Goods (FG) Master**: Engineered products catalog with selling prices, lead times, and calculated profit margins.
- **Multi-Component Recipes**: Detailed BOM headers and items with standard quantities, scrap/wastage allowance percentages, and calculated manufacturing cost.
- **Interactive BOM Explosion Simulator**: Select any finished product and production batch quantity to dynamically calculate gross material requirements, compare against real-time physical stock, flag critical shortages, and 1-click generate PO requisitions!

### 3. Purchase Order (PO) Module (`apps.procurement`)
- **Approved Vendor Directory**: Supplier master with credit payment terms, tax information, contact persons, and vendor performance ratings (1-5 stars).
- **Purchase Orders**: Formal procurement documents linked to Sales Order shortages or general warehouse restocking.
- **Goods Receipt Note (GRN) Workflow**: When consignments arrive at the warehouse gate, the GRN inspector verifies delivery challans, records received quantities, and **automatically increments physical inventory stock levels in real time**.
- **Vendor Communications Log**: Activity history recording phone calls, emails, and meetings with material suppliers.

### 4. Invoice Generation Module (`apps.invoices`)
- **GST-Compliant Tax Invoices**: Automated invoice creation with auto-generated sequential numbers (`INV-2026-0001`).
- **Tax Breakdown**: Dual CGST (9%) + SGST (9%) and IGST support, HSN/SAC classification codes (e.g. `8501`), discount handling, and payment terms (e.g., `Net 30 Days`).
- **Printable Tax Invoice Template**: Professional letterhead format with corporate details, bank remittance accounts (IFSC, Account Number), signature blocks, and print-to-PDF CSS.
- **Tracking**: Real-time tracking of `Amount Paid`, `Balance Due`, and status (`DRAFT`, `ISSUED`, `PARTIALLY_PAID`, `PAID`, `OVERDUE`).

### 5. Payment & Reconciliation Module (`apps.payments`)
- **Dual Cashflow Tracking**:
  - **Inflow (Customer Receipts)**: Payments received against client invoices.
  - **Outflow (Vendor Payments)**: Payments disbursed to suppliers against purchase orders.
- **Multi-Method Support**: Bank Transfer (NEFT/RTGS/IMPS), UPI, Corporate Cheque, Credit Card, and Cash with UTR / Transaction Reference tracking.
- **Automated Real-Time Reconciliation**: Recording a customer payment immediately updates the associated invoice's `amount_paid`, reduces `amount_due`, and dynamically shifts invoice status to `PAID` or `PARTIALLY_PAID`.

### 6. Reporting and Analytics Module (`apps.analytics`)
- **Executive KPI Cards**: Real-time tally of Total Booked Revenue, Collected Revenue, Procurement Expenditure, Accounts Receivable, Accounts Payable, Net Operating Margin, and Low-Stock Alert counts.
- **Interactive Visualizations (Chart.js)**:
  - 6-Month Sales Revenue vs. Procurement Cashflow trend line.
  - Sales Order Pipeline status breakdown donut chart.
  - Raw Material capital allocation by category (Metals, Electrical, Polymers, Fasteners).
  - Top 5 manufactured products by units sold and revenue.
- **Data Export Suite**: 1-click export of Orders, Inventory, Invoices, and POs to standard CSV formats, plus browser-native executive printing.

### 7. User Management and Access Control (RBAC) (`apps.accounts`)
- **Custom User Model**: Extends Django's user architecture with departmental roles and designations.
- **Role-Based Access Control**:
  - `ADMIN`: Full operational authority, settings, and user provisioning.
  - `SALES`: Order booking, customer relations, and invoice views.
  - `PRODUCTION`: Bill of Materials, production scheduling, stock monitoring, and BOM explosion.
  - `PROCUREMENT`: Vendor master, purchase order issuance, and Goods Receipt (GRN).
  - `FINANCE`: Commercial invoicing, payment receipts, vendor settlements, and cashflow reconciliation.
- **Live Role Switcher**: Interactive selector on the dashboard header allowing immediate role simulation during academic viva demonstrations.
- **Audit Trail**: Immutable system activity log recording actor, action type (`CREATE`, `STATUS_CHANGE`, `EXPLODE_BOM`, `RECEIVE_GOODS`, `RECONCILE`), affected module, record ID, and timestamps.

---

## 🚀 Quick Setup & Run Guide

### Step 1: Open Terminal in Backend Directory
```bash
cd ordercraft/backend
```

### Step 2: Apply Database Migrations
```bash
python manage.py migrate
```

### Step 3: Seed Realistic Manufacturing Plant Data
```bash
python manage.py seed_data
```
*This populates realistic finished products, multi-component BOMs, raw materials, industrial clients, approved suppliers, active sales orders, purchase orders, invoices, payments, and audit logs.*

### Step 4: Start the Development Server
```bash
python manage.py runserver
```
Open your browser and navigate to:
- **Homepage (Product Landing Page)**: `http://127.0.0.1:8000/`
- **Dedicated Login Page**: `http://127.0.0.1:8000/login/`
- **Manufacturing ERP Operations Dashboard**: `http://127.0.0.1:8000/app/`
- **Django Admin Portal**: `http://127.0.0.1:8000/admin/`

---

## 🗄️ Supabase PostgreSQL Setup Guide

OrderCraft is built from the ground up to support **Supabase PostgreSQL**.

### Connecting to your Supabase Project:
1. Log in to [Supabase](https://supabase.com) and create or open your project.
2. Go to **Project Settings** → **Database** → **Connection String** (URI mode).
3. In `ordercraft/backend/.env` (or `ordercraft/.env`), set:
```env
DATABASE_URL=postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```
4. Run migrations:
```bash
python manage.py migrate
python manage.py seed_data
```

*(Note: If no Supabase credentials are configured or PostgreSQL drivers are not installed locally, OrderCraft automatically falls back to the high-performance local SQLite database `db.sqlite3` with zero configuration needed!)*

### Direct Supabase SQL Editor Deployment:
If you wish to view or run tables directly in the Supabase web dashboard, open the included file:
- [`ordercraft/supabase_schema.sql`](./supabase_schema.sql)
Copy and paste its content into **Supabase SQL Editor** and click **Run**.

---

## 🔐 Default Seeded Accounts for Evaluation
All accounts use the default password: `ordercraft123`

| Username | Role | Full Name | Department |
|---|---|---|---|
| `admin` | Plant Administrator / Head | Vikram Malhotra | Executive Management |
| `sales_officer` | Sales & Order Booking | Rohan Verma | Commercial Sales |
| `prod_manager` | Production & BOM Manager | Anil Deshmukh | Manufacturing & Quality |
| `proc_officer` | Procurement Officer | Pooja Nair | Supply Chain & Sourcing |
| `accountant` | Finance & Commercial Accounts | Suresh Iyer | Finance & Accounts |

*(Tip: You can also use the **Simulate Role** dropdown on the top-right header to switch roles instantly without logging out!)*

---

## 🎓 College Viva & Presentation Guide

### Key Architectural Concepts to Highlight:
1. **Separation of Concerns**: Clean decoupling between the REST API (Django REST Framework) and the frontend view layer.
2. **Normalized Data Modeling**: Foreign key relationships linking Sales Orders → Invoices → Payments, and BOM → Raw Materials → POs → Goods Receipts (GRN).
3. **Automated Business Logic**:
   - Stock auto-increments upon GRN creation (`GoodsReceiptNote`).
   - Invoice auto-reconciliation and status updates upon payment confirmation (`Payment.save()`).
   - Real-time gross requirement calculation including scrap/wastage allowances.
4. **BOM Explosion Algorithm**: Calculates total dependent components for batch sizes, queries live inventory, and flags material shortages before production launch.
5. **Security & Auditing**: Immutable `AuditLog` captures operational trails with IP addresses and user actor tags.
