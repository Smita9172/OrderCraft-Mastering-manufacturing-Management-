/**
 * OrderCraft ERP - Centralized API Service Layer
 * Interfaces with Django REST Framework endpoints.
 */

const API_BASE = '/api';

// Utility: get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Toast notification helper
function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'fa-check-circle';
    if (type === 'danger') icon = 'fa-exclamation-circle';
    if (type === 'warning') icon = 'fa-exclamation-triangle';

    toast.innerHTML = `
        <i class="fas ${icon}" style="color: ${type === 'danger' ? '#ef4444' : (type === 'warning' ? '#f59e0b' : '#10b981')}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// HTTP request wrapper
async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') || '',
        }
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Network error or invalid response' }));
            const msg = errorData.error || errorData.detail || JSON.stringify(errorData);
            throw new Error(msg);
        }
        return await response.json();
    } catch (err) {
        console.error(`API Error on [${method}] ${endpoint}:`, err);
        throw err;
    }
}

// Authentication services are named functions so they are exported reliably
// through the shared API object used by every Django-rendered page.
async function registerAccount(email, password, confirmPassword) {
    return apiRequest('/accounts/auth/register/', 'POST', {
        email,
        password,
        confirm_password: confirmPassword,
    });
}

// OrderCraft API Services for 7 Modules
const API = {
    // Analytics (Module 6)
    getDashboardOverview: () => apiRequest('/analytics/dashboard/'),
    getChartsData: () => apiRequest('/analytics/charts/'),

    // Orders (Module 1)
    getCustomers: () => apiRequest('/orders/customers/'),
    createCustomer: (data) => apiRequest('/orders/customers/', 'POST', data),
    getOrders: () => apiRequest('/orders/orders/'),
    getOrder: (id) => apiRequest(`/orders/orders/${id}/`),
    createOrder: (data) => apiRequest('/orders/orders/', 'POST', data),
    updateOrderStatus: (id, status) => apiRequest(`/orders/orders/${id}/update_status/`, 'POST', { status }),
    checkOrderMaterials: (id) => apiRequest(`/orders/orders/${id}/check_materials/`),
    createInvoiceFromOrder: (id) => apiRequest(`/orders/orders/${id}/create_invoice/`, 'POST'),

    // BOM & Materials (Module 2)
    getRawMaterials: () => apiRequest('/bom/raw-materials/'),
    createRawMaterial: (data) => apiRequest('/bom/raw-materials/', 'POST', data),
    adjustStock: (id, quantity, reason) => apiRequest(`/bom/raw-materials/${id}/adjust_stock/`, 'POST', { quantity, reason }),
    getProducts: () => apiRequest('/bom/products/'),
    createProduct: (data) => apiRequest('/bom/products/', 'POST', data),
    getBOMs: () => apiRequest('/bom/boms/'),
    explodeBOM: (productId, quantity) => apiRequest('/bom/explode/', 'POST', { product_id: productId, quantity }),

    // Procurement & POs (Module 3)
    getVendors: () => apiRequest('/procurement/vendors/'),
    createVendor: (data) => apiRequest('/procurement/vendors/', 'POST', data),
    getPurchaseOrders: () => apiRequest('/procurement/purchase-orders/'),
    createPurchaseOrder: (data) => apiRequest('/procurement/purchase-orders/', 'POST', data),
    updatePOStatus: (id, status) => apiRequest(`/procurement/purchase-orders/${id}/update_status/`, 'POST', { status }),
    receiveGoodsGRN: (poId, data) => apiRequest(`/procurement/purchase-orders/${poId}/receive_goods/`, 'POST', data),
    getCommunications: () => apiRequest('/procurement/communications/'),
    logCommunication: (data) => apiRequest('/procurement/communications/', 'POST', data),

    // Invoices (Module 4)
    getInvoices: () => apiRequest('/invoices/invoices/'),
    getInvoice: (id) => apiRequest(`/invoices/invoices/${id}/`),
    createInvoice: (data) => apiRequest('/invoices/invoices/', 'POST', data),
    updateInvoiceStatus: (id, status) => apiRequest(`/invoices/invoices/${id}/update_status/`, 'POST', { status }),
    recordInvoicePayment: (id, data) => apiRequest(`/invoices/invoices/${id}/record_payment/`, 'POST', data),

    // Payments (Module 5)
    getPayments: () => apiRequest('/payments/payments/'),
    createPayment: (data) => apiRequest('/payments/payments/', 'POST', data),
    getPaymentSummary: () => apiRequest('/payments/payments/summary/'),

    // Accounts & RBAC (Module 7)
    getUsers: () => apiRequest('/accounts/users/'),
    createUser: (data) => apiRequest('/accounts/users/', 'POST', data),
    getCurrentUser: () => apiRequest('/accounts/auth/me/'),
    getAuditLogs: () => apiRequest('/accounts/audit-logs/'),
    login: (username, password, rememberMe = false) => apiRequest('/accounts/auth/login/', 'POST', { username, password, remember_me: rememberMe }),
    register: registerAccount,
    logout: () => apiRequest('/accounts/auth/logout/', 'POST'),
};

window.API = API;
window.OrderCraftAPI = API;
window.showToast = showToast;
