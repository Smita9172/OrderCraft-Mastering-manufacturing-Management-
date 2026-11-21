-- =============================================================================
-- ORDERCRAFT: MASTERING MANUFACTURING MANAGEMENT
-- Comprehensive Supabase PostgreSQL Database Schema
-- Modules: Order Booking, BOM, Purchase Orders, Invoices, Payments, Analytics, RBAC
-- =============================================================================

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- 1. USERS & ACCESS CONTROL (Module 7: RBAC)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS accounts_customuser (
    id BIGSERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMPTZ,
    is_superuser BOOLEAN DEFAULT FALSE,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) DEFAULT '',
    last_name VARCHAR(150) DEFAULT '',
    email VARCHAR(254) DEFAULT '',
    is_staff BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    date_joined TIMESTAMPTZ DEFAULT NOW(),
    role VARCHAR(20) DEFAULT 'ADMIN' CHECK (role IN ('ADMIN', 'SALES', 'PRODUCTION', 'PROCUREMENT', 'FINANCE')),
    phone VARCHAR(20),
    department VARCHAR(100) DEFAULT 'Manufacturing Operations',
    designation VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts_auditlog (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES accounts_customuser(id) ON DELETE SET NULL,
    user_name VARCHAR(150),
    action VARCHAR(20) NOT NULL,
    module VARCHAR(20) NOT NULL,
    record_id VARCHAR(100),
    description TEXT NOT NULL,
    ip_address INET,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 2. BILL OF MATERIALS (BOM) & PRODUCTS (Module 2)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bom_rawmaterial (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(30) DEFAULT 'METALS' CHECK (category IN ('METALS', 'ELECTRICAL', 'FASTENERS', 'POLYMERS', 'CHEMICALS', 'PACKAGING')),
    unit_of_measure VARCHAR(10) DEFAULT 'KG' CHECK (unit_of_measure IN ('KG', 'MTR', 'PCS', 'LTR', 'SQM', 'SET')),
    standard_cost NUMERIC(12, 2) DEFAULT 0.00,
    current_stock NUMERIC(12, 2) DEFAULT 0.00,
    reorder_level NUMERIC(12, 2) DEFAULT 50.00,
    safety_stock NUMERIC(12, 2) DEFAULT 20.00,
    warehouse_location VARCHAR(100) DEFAULT 'Warehouse Rack A-01',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bom_product (
    id BIGSERIAL PRIMARY KEY,
    product_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100) DEFAULT 'Industrial Motors & Pumps',
    description TEXT,
    unit_of_measure VARCHAR(10) DEFAULT 'PCS',
    selling_price NUMERIC(12, 2) DEFAULT 0.00,
    lead_time_days INTEGER DEFAULT 5,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bom_billofmaterial (
    id BIGSERIAL PRIMARY KEY,
    bom_number VARCHAR(50) UNIQUE NOT NULL,
    product_id BIGINT UNIQUE NOT NULL REFERENCES bom_product(id) ON DELETE CASCADE,
    version VARCHAR(20) DEFAULT 'v1.0',
    is_active BOOLEAN DEFAULT TRUE,
    is_approved BOOLEAN DEFAULT TRUE,
    approved_by_id BIGINT REFERENCES accounts_customuser(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bom_bomitem (
    id BIGSERIAL PRIMARY KEY,
    bom_id BIGINT NOT NULL REFERENCES bom_billofmaterial(id) ON DELETE CASCADE,
    raw_material_id BIGINT NOT NULL REFERENCES bom_rawmaterial(id) ON DELETE CASCADE,
    quantity_required NUMERIC(10, 3) NOT NULL,
    wastage_percentage NUMERIC(5, 2) DEFAULT 2.00,
    notes VARCHAR(255),
    CONSTRAINT unique_bom_rawmaterial UNIQUE (bom_id, raw_material_id)
);

-- -----------------------------------------------------------------------------
-- 3. CUSTOMERS & ORDER BOOKING (Module 1)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders_customer (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    gst_number VARCHAR(25),
    billing_address TEXT NOT NULL,
    shipping_address TEXT,
    city VARCHAR(100) DEFAULT 'Mumbai',
    state VARCHAR(100) DEFAULT 'Maharashtra',
    pincode VARCHAR(10) DEFAULT '400001',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders_salesorder (
    id BIGSERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id BIGINT NOT NULL REFERENCES orders_customer(id) ON DELETE RESTRICT,
    order_date DATE NOT NULL,
    delivery_due_date DATE NOT NULL,
    priority VARCHAR(20) DEFAULT 'MEDIUM' CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')),
    status VARCHAR(30) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'CONFIRMED', 'IN_PRODUCTION', 'READY_FOR_DISPATCH', 'DISPATCHED', 'DELIVERED', 'CANCELLED')),
    subtotal NUMERIC(14, 2) DEFAULT 0.00,
    tax_rate NUMERIC(5, 2) DEFAULT 18.00,
    tax_amount NUMERIC(14, 2) DEFAULT 0.00,
    discount_amount NUMERIC(14, 2) DEFAULT 0.00,
    grand_total NUMERIC(14, 2) DEFAULT 0.00,
    payment_terms VARCHAR(100) DEFAULT 'Net 30 Days',
    special_instructions TEXT,
    created_by_id BIGINT REFERENCES accounts_customuser(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders_salesorderitem (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders_salesorder(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES bom_product(id) ON DELETE RESTRICT,
    quantity INTEGER DEFAULT 1,
    unit_price NUMERIC(12, 2) NOT NULL,
    discount_percentage NUMERIC(5, 2) DEFAULT 0.00,
    line_total NUMERIC(14, 2) DEFAULT 0.00,
    specifications TEXT
);

-- -----------------------------------------------------------------------------
-- 4. VENDORS & PROCUREMENT / PURCHASE ORDERS (Module 3)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS procurement_vendor (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    gst_number VARCHAR(25),
    address TEXT NOT NULL,
    city VARCHAR(100) DEFAULT 'Pune',
    state VARCHAR(100) DEFAULT 'Maharashtra',
    pincode VARCHAR(10) DEFAULT '411001',
    payment_terms VARCHAR(100) DEFAULT 'Net 30 Days',
    rating NUMERIC(3, 1) DEFAULT 4.5,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS procurement_purchaseorder (
    id BIGSERIAL PRIMARY KEY,
    po_number VARCHAR(50) UNIQUE NOT NULL,
    vendor_id BIGINT NOT NULL REFERENCES procurement_vendor(id) ON DELETE RESTRICT,
    linked_sales_order_id BIGINT REFERENCES orders_salesorder(id) ON DELETE SET NULL,
    order_date DATE NOT NULL,
    expected_delivery_date DATE NOT NULL,
    status VARCHAR(30) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'ISSUED', 'ACKNOWLEDGED', 'PARTIALLY_RECEIVED', 'COMPLETED', 'CANCELLED')),
    subtotal NUMERIC(14, 2) DEFAULT 0.00,
    tax_amount NUMERIC(14, 2) DEFAULT 0.00,
    total_amount NUMERIC(14, 2) DEFAULT 0.00,
    terms_and_conditions TEXT,
    notes TEXT,
    created_by_id BIGINT REFERENCES accounts_customuser(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS procurement_purchaseorderitem (
    id BIGSERIAL PRIMARY KEY,
    purchase_order_id BIGINT NOT NULL REFERENCES procurement_purchaseorder(id) ON DELETE CASCADE,
    raw_material_id BIGINT NOT NULL REFERENCES bom_rawmaterial(id) ON DELETE RESTRICT,
    quantity_ordered NUMERIC(12, 2) NOT NULL,
    quantity_received NUMERIC(12, 2) DEFAULT 0.00,
    unit_price NUMERIC(12, 2) NOT NULL,
    tax_rate NUMERIC(5, 2) DEFAULT 18.00,
    line_total NUMERIC(14, 2) DEFAULT 0.00
);

CREATE TABLE IF NOT EXISTS procurement_goodsreceiptnote (
    id BIGSERIAL PRIMARY KEY,
    grn_number VARCHAR(50) UNIQUE NOT NULL,
    purchase_order_id BIGINT NOT NULL REFERENCES procurement_purchaseorder(id) ON DELETE CASCADE,
    receipt_date DATE NOT NULL,
    challan_number VARCHAR(100),
    remarks TEXT,
    received_by_id BIGINT REFERENCES accounts_customuser(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS procurement_vendorcommunication (
    id BIGSERIAL PRIMARY KEY,
    vendor_id BIGINT NOT NULL REFERENCES procurement_vendor(id) ON DELETE CASCADE,
    purchase_order_id BIGINT REFERENCES procurement_purchaseorder(id) ON DELETE SET NULL,
    channel VARCHAR(20) DEFAULT 'EMAIL' CHECK (channel IN ('EMAIL', 'PHONE', 'WHATSAPP', 'MEETING')),
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    date_logged TIMESTAMPTZ DEFAULT NOW(),
    logged_by_id BIGINT REFERENCES accounts_customuser(id) ON DELETE SET NULL
);

-- -----------------------------------------------------------------------------
-- 5. INVOICES & TAXATION (Module 4)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoices_invoice (
    id BIGSERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    sales_order_id BIGINT NOT NULL REFERENCES orders_salesorder(id) ON DELETE CASCADE,
    customer_id BIGINT NOT NULL REFERENCES orders_customer(id) ON DELETE RESTRICT,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    payment_terms VARCHAR(100) DEFAULT 'Net 30 Days',
    status VARCHAR(25) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'ISSUED', 'PARTIALLY_PAID', 'PAID', 'OVERDUE', 'CANCELLED')),
    subtotal NUMERIC(14, 2) DEFAULT 0.00,
    cgst_rate NUMERIC(5, 2) DEFAULT 9.00,
    cgst_amount NUMERIC(14, 2) DEFAULT 0.00,
    sgst_rate NUMERIC(5, 2) DEFAULT 9.00,
    sgst_amount NUMERIC(14, 2) DEFAULT 0.00,
    igst_rate NUMERIC(5, 2) DEFAULT 0.00,
    igst_amount NUMERIC(14, 2) DEFAULT 0.00,
    discount_amount NUMERIC(14, 2) DEFAULT 0.00,
    grand_total NUMERIC(14, 2) DEFAULT 0.00,
    amount_paid NUMERIC(14, 2) DEFAULT 0.00,
    amount_due NUMERIC(14, 2) DEFAULT 0.00,
    bank_details TEXT,
    notes TEXT,
    created_by_id BIGINT REFERENCES accounts_customuser(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS invoices_invoiceitem (
    id BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT NOT NULL REFERENCES invoices_invoice(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES bom_product(id) ON DELETE SET NULL,
    description VARCHAR(255) NOT NULL,
    hsn_sac_code VARCHAR(20) DEFAULT '8501',
    quantity INTEGER DEFAULT 1,
    unit_price NUMERIC(12, 2) NOT NULL,
    tax_rate NUMERIC(5, 2) DEFAULT 18.00,
    line_total NUMERIC(14, 2) DEFAULT 0.00
);

-- -----------------------------------------------------------------------------
-- 6. PAYMENTS & RECONCILIATION (Module 5)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments_payment (
    id BIGSERIAL PRIMARY KEY,
    payment_number VARCHAR(50) UNIQUE NOT NULL,
    payment_type VARCHAR(25) DEFAULT 'CUSTOMER_RECEIPT' CHECK (payment_type IN ('CUSTOMER_RECEIPT', 'VENDOR_PAYMENT')),
    invoice_id BIGINT REFERENCES invoices_invoice(id) ON DELETE SET NULL,
    purchase_order_id BIGINT REFERENCES procurement_purchaseorder(id) ON DELETE SET NULL,
    customer_id BIGINT REFERENCES orders_customer(id) ON DELETE SET NULL,
    vendor_id BIGINT REFERENCES procurement_vendor(id) ON DELETE SET NULL,
    amount NUMERIC(14, 2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_method VARCHAR(25) DEFAULT 'BANK_TRANSFER' CHECK (payment_method IN ('BANK_TRANSFER', 'UPI', 'CHEQUE', 'CREDIT_CARD', 'CASH', 'DEMAND_DRAFT')),
    reference_number VARCHAR(100),
    status VARCHAR(20) DEFAULT 'COMPLETED' CHECK (status IN ('PENDING', 'COMPLETED', 'FAILED', 'CANCELLED')),
    is_reconciled BOOLEAN DEFAULT TRUE,
    notes TEXT,
    recorded_by_id BIGINT REFERENCES accounts_customuser(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- INDEXES FOR HIGH QUERY PERFORMANCE (Module 6: Analytics)
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders_salesorder(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders_salesorder(status);
CREATE INDEX IF NOT EXISTS idx_po_vendor ON procurement_purchaseorder(vendor_id);
CREATE INDEX IF NOT EXISTS idx_po_status ON procurement_purchaseorder(status);
CREATE INDEX IF NOT EXISTS idx_invoice_status ON invoices_invoice(status);
CREATE INDEX IF NOT EXISTS idx_payments_type ON payments_payment(payment_type);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON accounts_auditlog(timestamp DESC);
