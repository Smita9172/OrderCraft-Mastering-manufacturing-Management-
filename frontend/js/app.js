/**
 * OrderCraft: Mastering Manufacturing Management ERP
 * Main Frontend Application Controller
 * Handles all 7 Core Manufacturing Modules, Modals, Dynamic Tables & Chart.js
 */

// Global Application State
let appState = {
    currentRole: 'ADMIN',
    dashboardData: null,
    orders: [],
    customers: [],
    products: [],
    rawMaterials: [],
    purchaseOrders: [],
    vendors: [],
    invoices: [],
    payments: [],
    users: [],
    auditLogs: [],
    charts: {}
};

// Initial document load
document.addEventListener('DOMContentLoaded', async () => {
    setupTabNavigation();
    setupDateDefaults();
    await loadInitialData();
});

// Setup sidebar tab switching
function setupTabNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const tabId = item.getAttribute('data-tab');
            showTab(tabId);
        });
    });
}

function showTab(tabId) {
    document.querySelectorAll('.nav-item').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
    });

    document.querySelectorAll('.tab-content').forEach(section => {
        section.classList.remove('active');
    });

    const targetSection = document.getElementById(tabId);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    updateHeaderTitles(tabId);
    loadTabData(tabId);
}

function updateHeaderTitles(tabId) {
    const titles = {
        'tab-dashboard': { title: 'Executive Manufacturing Dashboard', sub: 'Real-time oversight of manufacturing pipeline, BOM, purchase orders, and cashflow' },
        'tab-orders': { title: 'Module 1: Order Booking & Pipeline', sub: 'Create, schedule, and track customer sales orders and delivery commitments' },
        'tab-bom': { title: 'Module 2: Bill of Materials & Inventory', sub: 'Engineering product recipes, component breakdown, and shortage explosion simulator' },
        'tab-procurement': { title: 'Module 3: Procurement & Purchase Orders', sub: 'Vendor sourcing, PO issuance, and Goods Receipt Note (GRN) warehouse restocking' },
        'tab-invoices': { title: 'Module 4: Commercial Invoice Generation', sub: 'Tax invoices, GST compliance, discount handling, and print-ready formats' },
        'tab-payments': { title: 'Module 5: Payment Receipts & Reconciliation', sub: 'Inflow receipts, vendor disbursements, and automated invoice balance reconciliation' },
        'tab-analytics': { title: 'Module 6: Reporting & Analytics Intelligence', sub: 'Manufacturing KPIs, financial insights, stock turnover, and CSV exports' },
        'tab-users': { title: 'Module 7: User Management & Access Control', sub: 'Role-based access matrix, active operator accounts, and immutable audit trail' },
    };

    const header = titles[tabId] || titles['tab-dashboard'];
    document.getElementById('page-title').textContent = header.title;
    document.getElementById('page-subtitle').textContent = header.sub;
}

function setupDateDefaults() {
    const today = new Date().toISOString().split('T')[0];
    const nextMonth = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    ['order-date-input', 'po-date-input', 'payment-date'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = today;
    });

    ['order-due-date-input', 'po-due-date-input'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = nextMonth;
    });
}

// -----------------------------------------------------------------------------
// Data Loading & Refresh
// -----------------------------------------------------------------------------
async function loadInitialData() {
    try {
        await Promise.all([
            loadCurrentUser(),
            loadDashboard(),
            loadOrdersData(),
            loadBOMData(),
            loadProcurementData(),
            loadInvoicesData(),
            loadPaymentsData(),
            loadUsersData()
        ]);
        showToast("OrderCraft ERP loaded with live manufacturing data!", "success");
    } catch (err) {
        console.error("Initialization error:", err);
        showToast("Loaded system with demo fallback cache.", "warning");
    }
}

async function loadCurrentUser() {
    try {
        const user = await API.getCurrentUser();
        if (user && user.username) {
            const elName = document.getElementById('user-display-name');
            const elBadge = document.getElementById('user-role-badge');
            const elAvatar = document.getElementById('user-avatar');
            const selector = document.getElementById('role-selector');
            
            const fullName = user.full_name || user.username;
            if (elName) elName.textContent = fullName;
            if (elBadge) elBadge.textContent = user.role_display || user.role;
            if (elAvatar) elAvatar.textContent = (fullName[0] + (fullName.split(' ')[1]?.[0] || '')).toUpperCase();
            if (selector && user.role) selector.value = user.role;
        }
    } catch (e) {
        console.warn("Could not load current user session:", e);
    }
}

async function logoutUser() {
    try {
        await API.logout();
        showToast("Signed out successfully.", "info");
    } catch (e) {
        console.warn("Sign out request error:", e);
    }
    setTimeout(() => {
        window.location.href = '/login/';
    }, 350);
}

async function refreshCurrentTab() {
    const icon = document.getElementById('refresh-icon');
    if (icon) icon.classList.add('fa-spin');
    
    const activeNav = document.querySelector('.nav-item.active');
    const activeTab = activeNav ? activeNav.getAttribute('data-tab') : 'tab-dashboard';
    
    await loadInitialData();
    
    setTimeout(() => {
        if (icon) icon.classList.remove('fa-spin');
        showToast("Data refreshed successfully!", "success");
    }, 600);
}

function loadTabData(tabId) {
    if (tabId === 'tab-dashboard') loadDashboard();
    else if (tabId === 'tab-orders') renderOrdersTable();
    else if (tabId === 'tab-bom') renderBOMTables();
    else if (tabId === 'tab-procurement') renderProcurementTables();
    else if (tabId === 'tab-invoices') renderInvoicesTable();
    else if (tabId === 'tab-payments') renderPaymentsTable();
    else if (tabId === 'tab-analytics') renderAnalyticsCharts();
    else if (tabId === 'tab-users') renderUsersAndAudit();
}

// -----------------------------------------------------------------------------
// Role Simulation (Module 7: RBAC)
// -----------------------------------------------------------------------------
function switchRole(newRole) {
    appState.currentRole = newRole;
    const roleMap = {
        'ADMIN': { name: 'Vikram Malhotra', title: 'Plant Administrator / Head', initials: 'VM' },
        'SALES': { name: 'Rohan Verma', title: 'Sales & Order Officer', initials: 'RV' },
        'PRODUCTION': { name: 'Anil Deshmukh', title: 'Production & BOM Manager', initials: 'AD' },
        'PROCUREMENT': { name: 'Pooja Nair', title: 'Procurement Specialist', initials: 'PN' },
        'FINANCE': { name: 'Suresh Iyer', title: 'Chief Financial Controller', initials: 'SI' },
    };

    const info = roleMap[newRole] || roleMap['ADMIN'];
    document.getElementById('user-display-name').textContent = info.name;
    document.getElementById('user-role-badge').textContent = info.title;
    document.getElementById('user-avatar').textContent = info.initials;

    showToast(`Simulating Role: ${info.title}`, 'info');
}

// -----------------------------------------------------------------------------
// 1. Executive Dashboard (Module 6 & Overview)
// -----------------------------------------------------------------------------
async function loadDashboard() {
    try {
        const data = await API.getDashboardOverview();
        appState.dashboardData = data;
        const kpis = data.kpis;

        document.getElementById('kpi-total-rev').textContent = `₹${formatNumber(kpis.total_order_value)}`;
        document.getElementById('kpi-rev-collected').textContent = `₹${formatNumber(kpis.revenue_collected)}`;
        document.getElementById('kpi-receivable-sub').textContent = `Receivables: ₹${formatNumber(kpis.outstanding_receivables)}`;
        document.getElementById('kpi-procurement-spend').textContent = `₹${formatNumber(kpis.vendor_payments_made)}`;
        document.getElementById('kpi-payable-sub').textContent = `Payables: ₹${formatNumber(kpis.outstanding_payables)}`;
        document.getElementById('kpi-inventory-val').textContent = `₹${formatNumber(kpis.total_inventory_valuation)}`;
        document.getElementById('kpi-low-stock-sub').innerHTML = `<span style="color:#ef4444; font-weight:600;"><i class="fas fa-exclamation-triangle"></i> ${kpis.low_stock_count} Low Stock</span>`;

        // Render low stock alerts table
        const tbodyLowStock = document.querySelector('#table-low-stock-alerts tbody');
        if (tbodyLowStock) {
            tbodyLowStock.innerHTML = data.low_stock_alerts.map(item => `
                <tr>
                    <td><code>${item.code}</code></td>
                    <td><strong>${item.name}</strong></td>
                    <td style="color:var(--danger); font-weight:700;">${item.current_stock} ${item.unit}</td>
                    <td>${item.reorder_level} ${item.unit}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="openNewPOForMaterial(${item.id}, '${item.name}', ${item.reorder_level - item.current_stock})">
                            <i class="fas fa-cart-plus"></i> Reorder
                        </button>
                    </td>
                </tr>
            `).join('') || `<tr><td colspan="5" style="text-align:center; color:var(--gray-500); padding:20px;">All stock levels optimal</td></tr>`;
        }

        // Render recent orders on dashboard
        const tbodyRecent = document.querySelector('#table-recent-orders tbody');
        if (tbodyRecent && appState.orders.length) {
            tbodyRecent.innerHTML = appState.orders.slice(0, 4).map(o => `
                <tr>
                    <td><code>${o.order_number}</code></td>
                    <td>${o.customer_name}</td>
                    <td>${getStatusBadge(o.status)}</td>
                    <td><strong>₹${formatNumber(o.grand_total)}</strong></td>
                </tr>
            `).join('');
        }

        renderDashboardCharts();
    } catch (err) {
        console.error("Dashboard load failed:", err);
    }
}

async function renderDashboardCharts() {
    try {
        const chartData = await API.getChartsData();

        // 1. Revenue & Procurement Trend Chart
        const ctxTrend = document.getElementById('chart-trend')?.getContext('2d');
        if (ctxTrend) {
            if (appState.charts.trend) appState.charts.trend.destroy();
            appState.charts.trend = new Chart(ctxTrend, {
                type: 'line',
                data: {
                    labels: chartData.monthly_trend_chart.months,
                    datasets: [
                        {
                            label: 'Sales Revenue (₹)',
                            data: chartData.monthly_trend_chart.sales,
                            borderColor: '#0f766e',
                            backgroundColor: 'rgba(15, 118, 110, 0.1)',
                            fill: true,
                            tension: 0.35,
                            borderWidth: 2.5
                        },
                        {
                            label: 'Procurement Spend (₹)',
                            data: chartData.monthly_trend_chart.procurement,
                            borderColor: '#f59e0b',
                            backgroundColor: 'transparent',
                            borderDash: [5, 5],
                            tension: 0.35,
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'top' } },
                    scales: {
                        y: {
                            ticks: { callback: (val) => '₹' + (val / 1000) + 'k' }
                        }
                    }
                }
            });
        }

        // 2. Order Status Donut Chart
        const ctxStatus = document.getElementById('chart-order-status')?.getContext('2d');
        if (ctxStatus) {
            if (appState.charts.status) appState.charts.status.destroy();
            appState.charts.status = new Chart(ctxStatus, {
                type: 'doughnut',
                data: {
                    labels: chartData.order_status_chart.labels,
                    datasets: [{
                        data: chartData.order_status_chart.data,
                        backgroundColor: ['#94a3b8', '#3b82f6', '#f59e0b', '#0284c7', '#6366f1', '#10b981', '#ef4444']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'right' } },
                    cutout: '65%'
                }
            });
        }
    } catch (err) {
        console.error("Charts render failed:", err);
    }
}

// -----------------------------------------------------------------------------
// 2. Module 1: Order Booking & Customers
// -----------------------------------------------------------------------------
async function loadOrdersData() {
    appState.orders = await API.getOrders();
    appState.customers = await API.getCustomers();
    renderOrdersTable();
    renderCustomersTable();
    updateBadges();
}

function renderOrdersTable() {
    const tbody = document.querySelector('#table-sales-orders tbody');
    if (!tbody) return;

    if (!appState.orders.length) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px;">No sales orders booked yet.</td></tr>`;
        return;
    }

    tbody.innerHTML = appState.orders.map(order => `
        <tr>
            <td><strong><code>${order.order_number}</code></strong></td>
            <td>
                <div><strong>${order.customer_name}</strong></div>
                <small style="color:var(--gray-500);">${order.customer_city || ''}</small>
            </td>
            <td>${formatDate(order.order_date)}</td>
            <td>${formatDate(order.delivery_due_date)}</td>
            <td>${getPriorityBadge(order.priority)}</td>
            <td>${getStatusBadge(order.status)}</td>
            <td><strong>₹${formatNumber(order.grand_total)}</strong></td>
            <td>
                <div class="action-btn-group">
                    <button class="btn btn-sm btn-secondary" title="Progress Status" onclick="promptUpdateOrderStatus(${order.id}, '${order.status}')">
                        <i class="fas fa-step-forward"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-primary" title="Check Raw Materials" onclick="checkOrderMaterials(${order.id})">
                        <i class="fas fa-boxes"></i>
                    </button>
                    ${!order.has_invoice ? `
                        <button class="btn btn-sm btn-primary" title="1-Click Create Invoice" onclick="convertOrderToInvoice(${order.id})">
                            <i class="fas fa-file-invoice"></i>
                        </button>
                    ` : `
                        <button class="btn btn-sm btn-success" title="View Generated Invoice" onclick="viewInvoice(${order.invoice_id})">
                            <i class="fas fa-check"></i>
                        </button>
                    `}
                </div>
            </td>
        </tr>
    `).join('');
}

function renderCustomersTable() {
    const tbody = document.querySelector('#table-customers tbody');
    if (!tbody) return;

    tbody.innerHTML = appState.customers.map(c => `
        <tr>
            <td><code>${c.code}</code></td>
            <td><strong>${c.company_name}</strong></td>
            <td>${c.contact_person}</td>
            <td>${c.email}<br><small>${c.phone}</small></td>
            <td><code>${c.gst_number || 'N/A'}</code></td>
            <td>${c.city}, ${c.state}</td>
            <td><span class="badge badge-medium">${c.orders_count || 0} Orders</span></td>
        </tr>
    `).join('');
}

function filterOrdersTable() {
    const q = document.getElementById('search-orders').value.toLowerCase();
    const status = document.getElementById('filter-order-status').value;

    const rows = document.querySelectorAll('#table-sales-orders tbody tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const matchesQuery = text.includes(q);
        const matchesStatus = !status || text.includes(status.toLowerCase());
        row.style.display = matchesQuery && matchesStatus ? '' : 'none';
    });
}

async function promptUpdateOrderStatus(orderId, currentStatus) {
    const statuses = ['DRAFT', 'CONFIRMED', 'IN_PRODUCTION', 'READY_FOR_DISPATCH', 'DISPATCHED', 'DELIVERED', 'CANCELLED'];
    const choice = prompt(`Update Order Status:\nCurrent: ${currentStatus}\nEnter new status:\n(${statuses.join(', ')})`, currentStatus);
    if (!choice || choice === currentStatus) return;

    const formatted = choice.trim().toUpperCase();
    if (!statuses.includes(formatted)) {
        showToast("Invalid status entered", "danger");
        return;
    }

    try {
        await API.updateOrderStatus(orderId, formatted);
        showToast(`Order status updated to ${formatted}`, "success");
        await loadOrdersData();
        await loadDashboard();
    } catch (err) {
        showToast("Failed to update status: " + err.message, "danger");
    }
}

async function checkOrderMaterials(orderId) {
    try {
        const res = await API.checkOrderMaterials(orderId);
        let msg = `Material Feasibility for Order ${res.order_number}:\n\n`;
        res.materials.forEach(m => {
            msg += `• ${m.name}: Needed ${m.total_required} ${m.unit} | Stock: ${m.current_stock} ${m.unit} | Shortage: ${m.shortage_quantity} ${m.unit}\n`;
        });
        if (res.overall_shortage) {
            msg += `\n⚠️ MATERIAL SHORTAGE DETECTED! Purchase orders must be issued.`;
            alert(msg);
        } else {
            msg += `\n✅ ALL RAW MATERIALS IN STOCK! Production can commence immediately.`;
            alert(msg);
        }
    } catch (err) {
        showToast("Error checking materials: " + err.message, "danger");
    }
}

async function convertOrderToInvoice(orderId) {
    if (!confirm("Generate commercial tax invoice from this sales order?")) return;
    try {
        const res = await API.createInvoiceFromOrder(orderId);
        showToast(res.message, "success");
        await loadOrdersData();
        await loadInvoicesData();
        showTab('tab-invoices');
    } catch (err) {
        showToast("Failed to create invoice: " + err.message, "danger");
    }
}

// -----------------------------------------------------------------------------
// 3. Module 2: Bill of Materials (BOM) & Finished Goods
// -----------------------------------------------------------------------------
async function loadBOMData() {
    appState.products = await API.getProducts();
    appState.rawMaterials = await API.getRawMaterials();
    renderBOMTables();
}

function renderBOMTables() {
    // 1. Products & BOMs
    const tbodyProds = document.querySelector('#table-products-bom tbody');
    if (tbodyProds) {
        tbodyProds.innerHTML = appState.products.map(p => `
            <tr>
                <td><code>${p.product_code}</code></td>
                <td><strong>${p.name}</strong></td>
                <td>${p.category}</td>
                <td>${p.bom_details ? `<strong>${p.bom_details.bom_number}</strong> (${p.bom_details.version})` : 'No BOM'}</td>
                <td><span class="badge badge-medium">${p.bom_details ? p.bom_details.items_count + ' items' : '0'}</span></td>
                <td>₹${formatNumber(p.total_bom_cost)}</td>
                <td><strong>₹${formatNumber(p.selling_price)}</strong></td>
                <td><strong style="color:var(--success);">${p.profit_margin}%</strong></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="openBOMExplosionForProduct(${p.id})">
                        <i class="fas fa-calculator"></i> Explode
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // 2. Raw Materials
    const tbodyRMs = document.querySelector('#table-raw-materials tbody');
    if (tbodyRMs) {
        tbodyRMs.innerHTML = appState.rawMaterials.map(rm => `
            <tr>
                <td><code>${rm.code}</code></td>
                <td><strong>${rm.name}</strong></td>
                <td>${rm.category_display}</td>
                <td>${rm.unit_of_measure}</td>
                <td>₹${formatNumber(rm.standard_cost)}</td>
                <td><strong style="color:${rm.is_low_stock ? 'var(--danger)' : 'var(--navy-900)'};">${rm.current_stock}</strong></td>
                <td>${rm.reorder_level}</td>
                <td>${getStockBadge(rm.stock_status)}</td>
                <td><small>${rm.warehouse_location}</small></td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="promptAdjustStock(${rm.id}, '${rm.name}', ${rm.current_stock})">
                        <i class="fas fa-wrench"></i> Adjust
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // Populate Product select in Explosion modal
    const selectExp = document.getElementById('explosion-product-select');
    if (selectExp) {
        selectExp.innerHTML = appState.products.map(p => `<option value="${p.id}">${p.product_code} - ${p.name}</option>`).join('');
    }
}

function filterBOMTable() {
    const q = document.getElementById('search-bom').value.toLowerCase();
    document.querySelectorAll('#table-products-bom tbody tr, #table-raw-materials tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
}

async function promptAdjustStock(materialId, name, currentStock) {
    const qtyStr = prompt(`Adjust Stock for ${name}:\nCurrent Stock: ${currentStock}\nEnter quantity to add (use negative to reduce):`, "50");
    if (!qtyStr) return;
    const qty = parseFloat(qtyStr);
    if (isNaN(qty) || qty === 0) return;

    const reason = prompt("Enter adjustment reason:", "Physical count verification / Restock");
    try {
        await API.adjustStock(materialId, qty, reason);
        showToast(`Stock updated successfully!`, "success");
        await loadBOMData();
        await loadDashboard();
    } catch (err) {
        showToast("Error updating stock: " + err.message, "danger");
    }
}

function openBOMExplosionModal() {
    openModal('modal-bom-explosion');
}

function openBOMExplosionForProduct(productId) {
    const select = document.getElementById('explosion-product-select');
    if (select) select.value = productId;
    openModal('modal-bom-explosion');
    runBOMExplosion();
}

async function runBOMExplosion() {
    const prodId = document.getElementById('explosion-product-select').value;
    const qty = document.getElementById('explosion-qty-input').value;

    try {
        const res = await API.explodeBOM(prodId, qty);
        const box = document.getElementById('explosion-results-box');
        box.style.display = 'block';

        document.getElementById('explosion-summary-title').textContent = `Requirements for ${res.order_quantity} Units of ${res.product_name}`;
        
        const badge = document.getElementById('explosion-shortage-badge');
        if (res.has_shortage) {
            badge.className = 'badge badge-urgent';
            badge.textContent = 'Material Shortage Detected';
            document.getElementById('btn-quick-po').style.display = 'inline-flex';
        } else {
            badge.className = 'badge badge-delivered';
            badge.textContent = 'All Components Available in Stock';
            document.getElementById('btn-quick-po').style.display = 'none';
        }

        const tbody = document.querySelector('#table-explosion-details tbody');
        tbody.innerHTML = res.items.map(i => `
            <tr style="${i.is_shortage ? 'background:#fff1f2;' : ''}">
                <td><code>${i.material_code}</code></td>
                <td><strong>${i.material_name}</strong></td>
                <td>${i.qty_per_unit} ${i.unit}</td>
                <td><strong>${i.total_required} ${i.unit}</strong></td>
                <td>${i.current_stock} ${i.unit}</td>
                <td style="color:${i.is_shortage ? 'var(--danger)' : 'var(--success)'}; font-weight:700;">
                    ${i.is_shortage ? `-${i.shortage_quantity} ${i.unit}` : 'Sufficient'}
                </td>
                <td>₹${formatNumber(i.total_cost)}</td>
            </tr>
        `).join('');

        document.getElementById('explosion-total-cost').textContent = `₹${formatNumber(res.total_material_cost)}`;
        window._lastExplosionShortages = res.items.filter(i => i.is_shortage);
    } catch (err) {
        showToast("Error running BOM explosion: " + err.message, "danger");
    }
}

function quickCreatePOFromShortage() {
    if (!window._lastExplosionShortages || !window._lastExplosionShortages.length) return;
    closeModal('modal-bom-explosion');
    openNewPOModal();

    // Auto populate PO rows with shortages
    const tbody = document.getElementById('new-po-items-tbody');
    tbody.innerHTML = '';
    window._lastExplosionShortages.forEach(item => {
        addPOItemRow(item.material_id, Math.ceil(item.shortage_quantity * 1.1), item.unit_cost);
    });
    showToast("PO form prepopulated with shortage items!", "info");
}

// -----------------------------------------------------------------------------
// 4. Module 3: Purchase Orders & Vendors
// -----------------------------------------------------------------------------
async function loadProcurementData() {
    appState.purchaseOrders = await API.getPurchaseOrders();
    appState.vendors = await API.getVendors();
    renderProcurementTables();
    updateBadges();
}

function renderProcurementTables() {
    const tbody = document.querySelector('#table-purchase-orders tbody');
    if (tbody) {
        tbody.innerHTML = appState.purchaseOrders.map(po => `
            <tr>
                <td><strong><code>${po.po_number}</code></strong></td>
                <td><strong>${po.vendor_name}</strong></td>
                <td>${formatDate(po.order_date)}</td>
                <td>${formatDate(po.expected_delivery_date)}</td>
                <td>${getStatusBadge(po.status)}</td>
                <td><strong>₹${formatNumber(po.total_amount)}</strong></td>
                <td>
                    <div class="action-btn-group">
                        <button class="btn btn-sm btn-secondary" title="Change PO Status" onclick="promptUpdatePOStatus(${po.id}, '${po.status}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        ${po.status !== 'COMPLETED' ? `
                            <button class="btn btn-sm btn-primary" title="Receive Goods (GRN)" onclick="openReceiveGRNModal(${po.id})">
                                <i class="fas fa-truck-loading"></i> GRN
                            </button>
                        ` : `
                            <span class="badge badge-completed"><i class="fas fa-check"></i> Stocked</span>
                        `}
                    </div>
                </td>
            </tr>
        `).join('');
    }

    const tbodyVendors = document.querySelector('#table-vendors tbody');
    if (tbodyVendors) {
        tbodyVendors.innerHTML = appState.vendors.map(v => `
            <tr>
                <td><code>${v.code}</code></td>
                <td><strong>${v.company_name}</strong></td>
                <td>${v.contact_person}</td>
                <td>${v.email}<br><small>${v.phone}</small></td>
                <td>${v.city}, ${v.state}</td>
                <td><span class="badge badge-ready"><i class="fas fa-star" style="color:#f59e0b;"></i> ${v.rating} / 5</span></td>
                <td>${v.payment_terms}</td>
                <td><span class="badge badge-medium">${v.po_count || 0} POs</span></td>
            </tr>
        `).join('');
    }

    // Populate Vendor dropdown
    const select = document.getElementById('po-vendor-select');
    if (select) {
        select.innerHTML = appState.vendors.map(v => `<option value="${v.id}">${v.code} - ${v.company_name}</option>`).join('');
    }
}

function filterPOTable() {
    const q = document.getElementById('search-po').value.toLowerCase();
    document.querySelectorAll('#table-purchase-orders tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
}

async function promptUpdatePOStatus(poId, currentStatus) {
    const statuses = ['DRAFT', 'ISSUED', 'ACKNOWLEDGED', 'PARTIALLY_RECEIVED', 'COMPLETED', 'CANCELLED'];
    const choice = prompt(`Update PO Status:\nCurrent: ${currentStatus}\nEnter new status:\n(${statuses.join(', ')})`, currentStatus);
    if (!choice || choice === currentStatus) return;

    try {
        await API.updatePOStatus(poId, choice.trim().toUpperCase());
        showToast("PO status updated!", "success");
        await loadProcurementData();
    } catch (err) {
        showToast("Failed to update PO: " + err.message, "danger");
    }
}

function openReceiveGRNModal(poId) {
    const po = appState.purchaseOrders.find(p => p.id === poId);
    if (!po) return;

    document.getElementById('grn-po-id').value = po.id;
    document.getElementById('grn-po-number').value = po.po_number;
    document.getElementById('grn-challan').value = `CH-${Math.floor(10000 + Math.random() * 90000)}`;

    const tbody = document.getElementById('grn-items-tbody');
    tbody.innerHTML = po.items.map(item => `
        <tr>
            <td><strong>${item.material_name}</strong></td>
            <td>${item.quantity_ordered} ${item.unit_of_measure}</td>
            <td>${item.quantity_received} ${item.unit_of_measure}</td>
            <td>
                <input type="number" step="0.01" class="form-control grn-received-input" 
                       data-item-id="${item.id}" 
                       value="${item.remaining_quantity}" 
                       max="${item.remaining_quantity}" min="0">
            </td>
        </tr>
    `).join('');

    openModal('modal-receive-grn');
}

async function submitGRN(e) {
    e.preventDefault();
    const poId = document.getElementById('grn-po-id').value;
    const challan = document.getElementById('grn-challan').value;
    const remarks = document.getElementById('grn-remarks').value;

    const items = [];
    document.querySelectorAll('.grn-received-input').forEach(input => {
        items.push({
            item_id: parseInt(input.getAttribute('data-item-id')),
            quantity_received: parseFloat(input.value) || 0
        });
    });

    try {
        const res = await API.receiveGoodsGRN(poId, { items, challan_number: challan, remarks });
        showToast(res.message, "success");
        closeModal('modal-receive-grn');
        await loadProcurementData();
        await loadBOMData();
        await loadDashboard();
    } catch (err) {
        showToast("Failed to record GRN: " + err.message, "danger");
    }
}

// -----------------------------------------------------------------------------
// 5. Module 4: Invoices & Tax Engine
// -----------------------------------------------------------------------------
async function loadInvoicesData() {
    appState.invoices = await API.getInvoices();
    renderInvoicesTable();
}

function renderInvoicesTable() {
    const tbody = document.querySelector('#table-invoices tbody');
    if (!tbody) return;

    tbody.innerHTML = appState.invoices.map(inv => `
        <tr>
            <td><strong><code>${inv.invoice_number}</code></strong></td>
            <td><strong>${inv.customer_name}</strong></td>
            <td><code>${inv.sales_order_number || '-'}</code></td>
            <td>${formatDate(inv.invoice_date)}</td>
            <td>${formatDate(inv.due_date)}</td>
            <td>${getStatusBadge(inv.status)}</td>
            <td><strong>₹${formatNumber(inv.grand_total)}</strong></td>
            <td style="color:var(--success); font-weight:600;">₹${formatNumber(inv.amount_paid)}</td>
            <td style="color:${inv.amount_due > 0 ? 'var(--danger)' : 'var(--gray-500)'}; font-weight:700;">
                ₹${formatNumber(inv.amount_due)}
            </td>
            <td>
                <div class="action-btn-group">
                    <button class="btn btn-sm btn-secondary" title="View & Print Invoice" onclick="viewInvoice(${inv.id})">
                        <i class="fas fa-eye"></i> View
                    </button>
                    ${inv.amount_due > 0 ? `
                        <button class="btn btn-sm btn-primary" title="Record Payment" onclick="openRecordPaymentForInvoice(${inv.id})">
                            <i class="fas fa-money-bill-wave"></i> Pay
                        </button>
                    ` : ''}
                </div>
            </td>
        </tr>
    `).join('');
}

function filterInvoicesTable() {
    const q = document.getElementById('search-invoices').value.toLowerCase();
    const status = document.getElementById('filter-invoice-status').value;

    document.querySelectorAll('#table-invoices tbody tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        const matchesQuery = text.includes(q);
        const matchesStatus = !status || text.includes(status.toLowerCase());
        row.style.display = matchesQuery && matchesStatus ? '' : 'none';
    });
}

function viewInvoice(invId) {
    const inv = appState.invoices.find(i => i.id === invId);
    if (!inv) return;

    const content = document.getElementById('invoice-printable-content');
    content.innerHTML = `
        <div class="invoice-print-container">
            <div class="invoice-header-grid">
                <div class="invoice-company">
                    <h2>APEX PRECISION ENGINEERING PVT LTD</h2>
                    <p>Plant 01, Andheri East Industrial Estate, Mumbai, MH - 400093</p>
                    <p><strong>GSTIN:</strong> 27AABCA9918P1ZX | <strong>CIN:</strong> U29253MH2026PTC099121</p>
                    <p><strong>Email:</strong> accounts@apexprecision.com | <strong>Phone:</strong> +91 22 2831 9900</p>
                </div>
                <div class="invoice-meta">
                    <h1 style="color:var(--primary); font-size:26px; font-weight:800; margin-bottom:4px;">TAX INVOICE</h1>
                    <p><strong>Invoice #:</strong> ${inv.invoice_number}</p>
                    <p><strong>Invoice Date:</strong> ${formatDate(inv.invoice_date)}</p>
                    <p><strong>Payment Due Date:</strong> ${formatDate(inv.due_date)}</p>
                    <p><strong>Ref Sales Order:</strong> ${inv.sales_order_number || '-'}</p>
                    <div style="margin-top:8px;">${getStatusBadge(inv.status)}</div>
                </div>
            </div>

            <div class="invoice-parties-grid">
                <div>
                    <h4 style="font-size:12px; text-transform:uppercase; color:var(--gray-500); margin-bottom:4px;">Billed To (Customer):</h4>
                    <h3 style="font-size:15px; font-weight:700;">${inv.customer_name}</h3>
                    <p>${inv.customer_address || 'MIDC Industrial Area'}</p>
                    <p><strong>GSTIN:</strong> ${inv.customer_gst || 'N/A'}</p>
                    <p><strong>Contact:</strong> ${inv.customer_phone || ''} | ${inv.customer_email || ''}</p>
                </div>
                <div>
                    <h4 style="font-size:12px; text-transform:uppercase; color:var(--gray-500); margin-bottom:4px;">Payment Remittance Details:</h4>
                    <p style="white-space:pre-line; font-size:12.5px; background:#fff; padding:8px; border:1px solid var(--gray-200); border-radius:4px;">
                        ${inv.bank_details || 'Bank: State Bank of India\nA/C No: 398201948201\nIFSC: SBIN0004521'}
                    </p>
                </div>
            </div>

            <table class="data-table" style="margin-bottom:20px;">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Item Description</th>
                        <th>HSN/SAC</th>
                        <th>Qty</th>
                        <th>Unit Rate (₹)</th>
                        <th>GST %</th>
                        <th style="text-align:right;">Amount (₹)</th>
                    </tr>
                </thead>
                <tbody>
                    ${inv.items.map((item, idx) => `
                        <tr>
                            <td>${idx + 1}</td>
                            <td><strong>${item.description}</strong></td>
                            <td>${item.hsn_sac_code || '8501'}</td>
                            <td>${item.quantity}</td>
                            <td>₹${formatNumber(item.unit_price)}</td>
                            <td>${item.tax_rate}%</td>
                            <td style="text-align:right;">₹${formatNumber(item.line_total)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>

            <div style="display:flex; justify-content:flex-end;">
                <div style="width: 320px;">
                    <div style="display:flex; justify-content:space-between; padding:6px 0;">
                        <span>Subtotal:</span>
                        <span>₹${formatNumber(inv.subtotal)}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; padding:6px 0;">
                        <span>CGST (9%):</span>
                        <span>₹${formatNumber(inv.cgst_amount)}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; padding:6px 0;">
                        <span>SGST (9%):</span>
                        <span>₹${formatNumber(inv.sgst_amount)}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; padding:8px 0; border-top:2px solid var(--navy-900); font-size:15px; font-weight:800;">
                        <span>Grand Total:</span>
                        <span>₹${formatNumber(inv.grand_total)}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; padding:6px 0; color:var(--success); font-weight:600;">
                        <span>Amount Paid:</span>
                        <span>₹${formatNumber(inv.amount_paid)}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; padding:6px 0; color:var(--danger); font-weight:700;">
                        <span>Balance Due:</span>
                        <span>₹${formatNumber(inv.amount_due)}</span>
                    </div>
                </div>
            </div>

            <div style="margin-top: 40px; display:flex; justify-content:space-between; align-items:flex-end; border-top: 1px solid var(--gray-200); padding-top: 20px;">
                <div>
                    <p style="font-size:11.5px; color:var(--gray-500);">Terms & Conditions: Standard 30 days credit. Subject to Mumbai Jurisdiction.</p>
                </div>
                <div style="text-align:center;">
                    <div style="height:45px;"></div>
                    <p><strong>For Apex Precision Engineering Pvt Ltd</strong></p>
                    <p style="font-size:11px; color:var(--gray-500);">Authorized Signatory</p>
                </div>
            </div>
        </div>
    `;

    openModal('modal-invoice-viewer');
}

function printInvoice() {
    window.print();
}

// -----------------------------------------------------------------------------
// 6. Module 5: Payments & Receipts
// -----------------------------------------------------------------------------
async function loadPaymentsData() {
    appState.payments = await API.getPayments();
    const summary = await API.getPaymentSummary();

    document.getElementById('pay-total-inflow').textContent = `₹${formatNumber(summary.total_inflow)}`;
    document.getElementById('pay-total-outflow').textContent = `₹${formatNumber(summary.total_outflow)}`;
    document.getElementById('pay-receivables').textContent = `₹${formatNumber(summary.accounts_receivable)}`;
    document.getElementById('pay-payables').textContent = `₹${formatNumber(summary.accounts_payable)}`;

    renderPaymentsTable();
}

function renderPaymentsTable() {
    const tbody = document.querySelector('#table-payments tbody');
    if (!tbody) return;

    tbody.innerHTML = appState.payments.map(p => `
        <tr>
            <td><strong><code>${p.payment_number}</code></strong></td>
            <td>
                <span class="badge ${p.payment_type === 'CUSTOMER_RECEIPT' ? 'badge-inflow' : 'badge-outflow'}">
                    ${p.payment_type === 'CUSTOMER_RECEIPT' ? '↓ Customer Inflow' : '↑ Vendor Outflow'}
                </span>
            </td>
            <td><strong>${p.party_name}</strong></td>
            <td><code>${p.document_ref}</code></td>
            <td>${formatDate(p.payment_date)}</td>
            <td>${p.payment_method_display}</td>
            <td><code>${p.reference_number || '-'}</code></td>
            <td><strong>₹${formatNumber(p.amount)}</strong></td>
            <td>
                <span class="badge badge-completed"><i class="fas fa-check-circle"></i> Reconciled</span>
            </td>
        </tr>
    `).join('');
}

function filterPaymentsTable() {
    const q = document.getElementById('search-payments').value.toLowerCase();
    document.querySelectorAll('#table-payments tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
}

function openRecordPaymentModal() {
    // Populate Invoices
    const selectInv = document.getElementById('payment-invoice-select');
    selectInv.innerHTML = '<option value="">-- Select Customer Invoice --</option>' +
        appState.invoices.map(i => `<option value="${i.id}" data-due="${i.amount_due}">${i.invoice_number} - ${i.customer_name} (Due: ₹${formatNumber(i.amount_due)})</option>`).join('');

    // Populate POs
    const selectPO = document.getElementById('payment-po-select');
    selectPO.innerHTML = '<option value="">-- Select Vendor PO --</option>' +
        appState.purchaseOrders.map(p => `<option value="${p.id}" data-total="${p.total_amount}">${p.po_number} - ${p.vendor_name} (Total: ₹${formatNumber(p.total_amount)})</option>`).join('');

    openModal('modal-record-payment');
}

function openRecordPaymentForInvoice(invId) {
    openRecordPaymentModal();
    const select = document.getElementById('payment-invoice-select');
    select.value = invId;
    onPaymentInvoiceSelect(invId);
}

function togglePaymentType(type) {
    const isCustomer = type === 'CUSTOMER_RECEIPT';
    document.getElementById('group-payment-invoice').style.display = isCustomer ? 'block' : 'none';
    document.getElementById('group-payment-po').style.display = isCustomer ? 'none' : 'block';
}

function onPaymentInvoiceSelect(invId) {
    const inv = appState.invoices.find(i => i.id == invId);
    if (inv) {
        document.getElementById('payment-amount').value = inv.amount_due;
        document.getElementById('payment-notes').value = `Full settlement for ${inv.invoice_number}`;
    }
}

async function submitPayment(e) {
    e.preventDefault();
    const type = document.getElementById('payment-type-select').value;
    const invId = document.getElementById('payment-invoice-select').value;
    const poId = document.getElementById('payment-po-select').value;
    const amount = parseFloat(document.getElementById('payment-amount').value);
    const date = document.getElementById('payment-date').value;
    const method = document.getElementById('payment-method-select').value;
    const ref = document.getElementById('payment-ref').value;
    const notes = document.getElementById('payment-notes').value;

    const payload = {
        payment_type: type,
        amount,
        payment_date: date,
        payment_method: method,
        reference_number: ref,
        notes,
        status: 'COMPLETED'
    };

    if (type === 'CUSTOMER_RECEIPT') payload.invoice = invId;
    else payload.purchase_order = poId;

    try {
        await API.createPayment(payload);
        showToast("Payment recorded & reconciled successfully!", "success");
        closeModal('modal-record-payment');
        await loadPaymentsData();
        await loadInvoicesData();
        await loadDashboard();
    } catch (err) {
        showToast("Failed to record payment: " + err.message, "danger");
    }
}

// -----------------------------------------------------------------------------
// 7. Module 6: Reports & Analytics Intelligence
// -----------------------------------------------------------------------------
async function renderAnalyticsCharts() {
    try {
        const data = await API.getChartsData();

        // Inventory Category Valuation
        const ctxCat = document.getElementById('chart-inventory-categories')?.getContext('2d');
        if (ctxCat) {
            if (appState.charts.cat) appState.charts.cat.destroy();
            appState.charts.cat = new Chart(ctxCat, {
                type: 'bar',
                data: {
                    labels: data.category_inventory_chart.labels,
                    datasets: [{
                        label: 'Stock Value (₹)',
                        data: data.category_inventory_chart.data,
                        backgroundColor: '#0d9488',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { ticks: { callback: v => '₹' + (v / 1000) + 'k' } }
                    }
                }
            });
        }

        // Top Products Ranking
        const container = document.getElementById('top-products-container');
        if (container) {
            container.innerHTML = data.top_products.map((p, idx) => `
                <div style="display:flex; justify-content:space-between; align-items:center; padding:12px 0; border-bottom:1px solid var(--gray-200);">
                    <div>
                        <span class="badge badge-medium">#${idx + 1}</span>
                        <strong style="margin-left:8px;">${p.product__name}</strong>
                        <div style="font-size:12px; color:var(--gray-500); margin-left:35px;">Units Sold: ${p.total_qty}</div>
                    </div>
                    <strong style="color:var(--primary); font-size:15px;">₹${formatNumber(p.total_rev)}</strong>
                </div>
            `).join('') || '<p style="color:var(--gray-500);">No sales data available yet.</p>';
        }
    } catch (err) {
        console.error("Analytics render failed:", err);
    }
}

function exportData(type) {
    window.location.href = `/api/analytics/export/?type=${type}`;
    showToast(`Downloading ${type} report CSV...`, "info");
}

// -----------------------------------------------------------------------------
// 8. Module 7: User Management & RBAC
// -----------------------------------------------------------------------------
async function loadUsersData() {
    appState.users = await API.getUsers();
    appState.auditLogs = await API.getAuditLogs();
    renderUsersAndAudit();
}

function renderUsersAndAudit() {
    const tbodyUsers = document.querySelector('#table-users tbody');
    if (tbodyUsers) {
        tbodyUsers.innerHTML = appState.users.map(u => `
            <tr>
                <td><strong><code>${u.username}</code></strong></td>
                <td>${u.full_name}</td>
                <td><span class="badge badge-confirmed">${u.role_display}</span></td>
                <td>${u.department}</td>
                <td>${u.designation || 'Staff'}</td>
            </tr>
        `).join('');
    }

    const auditList = document.getElementById('audit-log-list');
    if (auditList) {
        auditList.innerHTML = appState.auditLogs.map(log => `
            <li class="audit-entry">
                <div class="audit-dot"></div>
                <div class="audit-content">
                    <div class="audit-header">
                        <span><strong>${log.user_name || 'System'}</strong> • <span class="badge badge-low">${log.module}</span></span>
                        <span>${log.formatted_time}</span>
                    </div>
                    <p style="font-size:13px; color:var(--navy-900);">${log.description}</p>
                </div>
            </li>
        `).join('');
    }
}

function filterUsersTable() {
    const q = document.getElementById('search-users').value.toLowerCase();
    document.querySelectorAll('#table-users tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
}

function openAddUserModal() {
    openModal('modal-add-user');
}

async function submitAddUser(e) {
    e.preventDefault();
    const payload = {
        username: document.getElementById('new-user-username').value,
        role: document.getElementById('new-user-role').value,
        first_name: document.getElementById('new-user-first-name').value,
        last_name: document.getElementById('new-user-last-name').value,
        email: document.getElementById('new-user-email').value,
        department: document.getElementById('new-user-department').value,
    };

    try {
        await API.createUser(payload);
        showToast("User account created successfully!", "success");
        closeModal('modal-add-user');
        await loadUsersData();
    } catch (err) {
        showToast("Failed to create user: " + err.message, "danger");
    }
}

// -----------------------------------------------------------------------------
// Modals and Helper Forms
// -----------------------------------------------------------------------------
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('active');
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('active');
}

function openNewOrderModal() {
    // Populate customer dropdown
    const select = document.getElementById('order-customer-select');
    select.innerHTML = appState.customers.map(c => `<option value="${c.id}">${c.code} - ${c.company_name}</option>`).join('');

    const tbody = document.getElementById('new-order-items-tbody');
    tbody.innerHTML = '';
    addOrderItemRow();

    openModal('modal-new-order');
}

function addOrderItemRow() {
    const tbody = document.getElementById('new-order-items-tbody');
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>
            <select class="form-control order-prod-select" onchange="onOrderProductChange(this)">
                ${appState.products.map(p => `<option value="${p.id}" data-price="${p.selling_price}">${p.name} (₹${formatNumber(p.selling_price)})</option>`).join('')}
            </select>
        </td>
        <td><input type="number" class="form-control order-qty-input" value="1" min="1" oninput="calculateOrderRow(this)"></td>
        <td><input type="number" class="form-control order-price-input" value="${appState.products[0]?.selling_price || 0}" oninput="calculateOrderRow(this)"></td>
        <td><input type="number" class="form-control order-disc-input" value="0" min="0" max="100" oninput="calculateOrderRow(this)"></td>
        <td><strong class="order-line-total">₹0</strong></td>
        <td><button type="button" class="btn btn-sm btn-danger" onclick="this.closest('tr').remove()">&times;</button></td>
    `;
    tbody.appendChild(tr);
    calculateOrderRow(tr.querySelector('.order-qty-input'));
}

function onOrderProductChange(select) {
    const tr = select.closest('tr');
    const opt = select.options[select.selectedIndex];
    const price = opt.getAttribute('data-price') || 0;
    tr.querySelector('.order-price-input').value = price;
    calculateOrderRow(select);
}

function calculateOrderRow(input) {
    const tr = input.closest('tr');
    const qty = parseFloat(tr.querySelector('.order-qty-input').value) || 0;
    const price = parseFloat(tr.querySelector('.order-price-input').value) || 0;
    const disc = parseFloat(tr.querySelector('.order-disc-input').value) || 0;

    const gross = qty * price;
    const total = gross - (gross * (disc / 100));
    tr.querySelector('.order-line-total').textContent = `₹${formatNumber(total)}`;
}

async function submitNewOrder(e) {
    e.preventDefault();
    const customer = document.getElementById('order-customer-select').value;
    const orderDate = document.getElementById('order-date-input').value;
    const dueDate = document.getElementById('order-due-date-input').value;
    const priority = document.getElementById('order-priority-select').value;
    const paymentTerms = document.getElementById('order-payment-terms').value;
    const specialInstructions = document.getElementById('order-special-instructions').value;

    const items = [];
    document.querySelectorAll('#new-order-items-tbody tr').forEach(tr => {
        items.push({
            product: parseInt(tr.querySelector('.order-prod-select').value),
            quantity: parseInt(tr.querySelector('.order-qty-input').value),
            unit_price: parseFloat(tr.querySelector('.order-price-input').value),
            discount_percentage: parseFloat(tr.querySelector('.order-disc-input').value)
        });
    });

    if (!items.length) {
        showToast("Please add at least one product item.", "warning");
        return;
    }

    try {
        await API.createOrder({
            customer,
            order_date: orderDate,
            delivery_due_date: dueDate,
            priority,
            payment_terms: paymentTerms,
            special_instructions: specialInstructions,
            status: 'CONFIRMED',
            items
        });
        showToast("Sales order booked successfully!", "success");
        closeModal('modal-new-order');
        await loadOrdersData();
        await loadDashboard();
    } catch (err) {
        showToast("Failed to book order: " + err.message, "danger");
    }
}

function openNewPOModal() {
    const tbody = document.getElementById('new-po-items-tbody');
    tbody.innerHTML = '';
    addPOItemRow();
    openModal('modal-new-po');
}

function addPOItemRow(selectedId = null, qty = 10, unitPrice = null) {
    const tbody = document.getElementById('new-po-items-tbody');
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>
            <select class="form-control po-material-select" onchange="onPOMaterialChange(this)">
                ${appState.rawMaterials.map(rm => `<option value="${rm.id}" data-cost="${rm.standard_cost}" ${selectedId === rm.id ? 'selected' : ''}>${rm.code} - ${rm.name} (${rm.unit_of_measure})</option>`).join('')}
            </select>
        </td>
        <td><input type="number" step="0.01" class="form-control po-qty-input" value="${qty}"></td>
        <td><input type="number" step="0.01" class="form-control po-cost-input" value="${unitPrice || appState.rawMaterials[0]?.standard_cost || 0}"></td>
        <td><button type="button" class="btn btn-sm btn-danger" onclick="this.closest('tr').remove()">&times;</button></td>
    `;
    tbody.appendChild(tr);
}

function onPOMaterialChange(select) {
    const tr = select.closest('tr');
    const opt = select.options[select.selectedIndex];
    const cost = opt.getAttribute('data-cost') || 0;
    tr.querySelector('.po-cost-input').value = cost;
}

function openNewPOForMaterial(materialId, name, requiredQty) {
    showTab('tab-procurement');
    openNewPOModal();
    const tbody = document.getElementById('new-po-items-tbody');
    tbody.innerHTML = '';
    const rm = appState.rawMaterials.find(m => m.id === materialId);
    addPOItemRow(materialId, Math.max(10, Math.ceil(requiredQty)), rm ? rm.standard_cost : 100);
}

async function submitNewPO(e) {
    e.preventDefault();
    const vendor = document.getElementById('po-vendor-select').value;
    const orderDate = document.getElementById('po-date-input').value;
    const dueDate = document.getElementById('po-due-date-input').value;
    const notes = document.getElementById('po-notes').value;

    const items = [];
    document.querySelectorAll('#new-po-items-tbody tr').forEach(tr => {
        items.push({
            raw_material: parseInt(tr.querySelector('.po-material-select').value),
            quantity_ordered: parseFloat(tr.querySelector('.po-qty-input').value),
            unit_price: parseFloat(tr.querySelector('.po-cost-input').value),
            tax_rate: 18.0
        });
    });

    if (!items.length) {
        showToast("Please add at least one material item.", "warning");
        return;
    }

    try {
        await API.createPurchaseOrder({
            vendor,
            order_date: orderDate,
            expected_delivery_date: dueDate,
            notes,
            status: 'ISSUED',
            items
        });
        showToast("Purchase Order issued to vendor successfully!", "success");
        closeModal('modal-new-po');
        await loadProcurementData();
        await loadDashboard();
    } catch (err) {
        showToast("Failed to issue PO: " + err.message, "danger");
    }
}

function openAddRawMaterialModal() {
    openModal('modal-add-material');
}

async function submitAddMaterial(e) {
    e.preventDefault();
    const payload = {
        code: document.getElementById('mat-code').value,
        name: document.getElementById('mat-name').value,
        category: document.getElementById('mat-category').value,
        unit_of_measure: document.getElementById('mat-unit').value,
        standard_cost: parseFloat(document.getElementById('mat-cost').value),
        current_stock: parseFloat(document.getElementById('mat-stock').value),
        reorder_level: parseFloat(document.getElementById('mat-reorder').value),
        warehouse_location: document.getElementById('mat-location').value,
    };

    try {
        await API.createRawMaterial(payload);
        showToast("Raw material added to inventory!", "success");
        closeModal('modal-add-material');
        await loadBOMData();
        await loadDashboard();
    } catch (err) {
        showToast("Failed to add raw material: " + err.message, "danger");
    }
}

function openAddCustomerModal() {
    openModal('modal-add-customer');
}

async function submitAddCustomer(e) {
    e.preventDefault();
    const payload = {
        code: document.getElementById('cust-code').value,
        company_name: document.getElementById('cust-company').value,
        contact_person: document.getElementById('cust-contact').value,
        gst_number: document.getElementById('cust-gst').value,
        email: document.getElementById('cust-email').value,
        phone: document.getElementById('cust-phone').value,
        billing_address: document.getElementById('cust-address').value,
        city: document.getElementById('cust-city').value,
        state: document.getElementById('cust-state').value,
        pincode: document.getElementById('cust-pincode').value,
    };

    try {
        await API.createCustomer(payload);
        showToast("Customer registered successfully!", "success");
        closeModal('modal-add-customer');
        await loadOrdersData();
    } catch (err) {
        showToast("Failed to register customer: " + err.message, "danger");
    }
}

function openAddVendorModal() {
    openModal('modal-add-vendor');
}

async function submitAddVendor(e) {
    e.preventDefault();
    const payload = {
        code: document.getElementById('vend-code').value,
        company_name: document.getElementById('vend-company').value,
        contact_person: document.getElementById('vend-contact').value,
        payment_terms: document.getElementById('vend-terms').value,
        email: document.getElementById('vend-email').value,
        phone: document.getElementById('vend-phone').value,
        address: document.getElementById('vend-address').value,
    };

    try {
        await API.createVendor(payload);
        showToast("Vendor onboarded successfully!", "success");
        closeModal('modal-add-vendor');
        await loadProcurementData();
    } catch (err) {
        showToast("Failed to onboard vendor: " + err.message, "danger");
    }
}

// -----------------------------------------------------------------------------
// Utilities & Badges
// -----------------------------------------------------------------------------
function updateBadges() {
    const oCount = document.getElementById('badge-orders-count');
    if (oCount) oCount.textContent = appState.orders.length;
    const poCount = document.getElementById('badge-po-count');
    if (poCount) poCount.textContent = appState.purchaseOrders.length;
}

function formatNumber(num) {
    if (!num) return '0.00';
    return Number(num).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function getStatusBadge(status) {
    const map = {
        'DRAFT': 'badge-draft',
        'CONFIRMED': 'badge-confirmed',
        'IN_PRODUCTION': 'badge-production',
        'READY_FOR_DISPATCH': 'badge-ready',
        'DISPATCHED': 'badge-dispatched',
        'DELIVERED': 'badge-delivered',
        'COMPLETED': 'badge-completed',
        'ISSUED': 'badge-confirmed',
        'ACKNOWLEDGED': 'badge-ready',
        'PARTIALLY_RECEIVED': 'badge-production',
        'PARTIALLY_PAID': 'badge-production',
        'PAID': 'badge-paid',
        'OVERDUE': 'badge-overdue',
        'CANCELLED': 'badge-cancelled',
    };
    const cls = map[status] || 'badge-draft';
    const label = status ? status.replace(/_/g, ' ') : 'N/A';
    return `<span class="badge ${cls}">${label}</span>`;
}

function getPriorityBadge(priority) {
    const map = {
        'URGENT': 'badge-urgent',
        'HIGH': 'badge-high',
        'MEDIUM': 'badge-medium',
        'LOW': 'badge-low',
    };
    return `<span class="badge ${map[priority] || 'badge-low'}">${priority}</span>`;
}

function getStockBadge(status) {
    if (status === 'OUT_OF_STOCK') return `<span class="badge badge-overdue">Out of Stock</span>`;
    if (status === 'LOW_STOCK') return `<span class="badge badge-high"><i class="fas fa-exclamation-triangle"></i> Low Stock</span>`;
    return `<span class="badge badge-delivered">Optimal</span>`;
}
