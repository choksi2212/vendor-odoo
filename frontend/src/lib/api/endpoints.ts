import { api } from './client';
import { snakeToCamel, camelToSnake } from './transform';

// ─── Auth ────────────────────────────────────────────────────────────────────

export const authAPI = {
  login: async (email: string, password: string) => {
    const data = await api.post<any>('/api/auth/login', { email, password });
    return snakeToCamel(data);
  },
  signup: async (payload: any) => {
    return api.post('/api/auth/signup', camelToSnake(payload));
  },
  forgotPassword: async (email: string) => {
    return api.post('/api/auth/forgot-password', { email });
  },
  resetPassword: async (token: string, password: string, confirmPassword: string) => {
    return api.post('/api/auth/reset-password', {
      token, password, confirm_password: confirmPassword,
    });
  },
  getMe: async () => {
    const data = await api.get<any>('/api/users/me');
    return snakeToCamel(data);
  },
  verifyOTP: async (pendingToken: string, otp: string) => {
    const data = await api.post<any>('/api/auth/verify-otp', {
      pending_token: pendingToken,
      otp,
    });
    return snakeToCamel(data);
  },
  logout: async (refreshToken: string) => {
    return api.post('/api/auth/logout', { refresh_token: refreshToken });
  },
};

// ─── Vendors ─────────────────────────────────────────────────────────────────

export const vendorAPI = {
  list: async (params?: { page?: number; search?: string; status?: string; categoryId?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.search) query.set('search', params.search);
    if (params?.status) query.set('status', params.status);
    if (params?.categoryId) query.set('category_id', params.categoryId);
    const data = await api.get<any>(`/api/vendors?${query.toString()}`);
    return snakeToCamel(data);
  },
  getById: async (id: string) => {
    const data = await api.get<any>(`/api/vendors/${id}`);
    return snakeToCamel(data);
  },
  create: async (payload: any) => {
    const data = await api.post<any>('/api/vendors', camelToSnake(payload));
    return snakeToCamel(data);
  },
  update: async (id: string, payload: any) => {
    const data = await api.put<any>(`/api/vendors/${id}`, camelToSnake(payload));
    return snakeToCamel(data);
  },
  deactivate: async (id: string) => {
    return api.delete(`/api/vendors/${id}`);
  },
  getCategories: async () => {
    const data = await api.get<any>('/api/vendors/categories');
    return snakeToCamel(data);
  },
  createCategory: async (name: string, description?: string) => {
    return api.post('/api/vendors/categories', { name, description });
  },
};

// ─── RFQs ────────────────────────────────────────────────────────────────────

export const rfqAPI = {
  list: async (params?: { page?: number; search?: string; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.search) query.set('search', params.search);
    if (params?.status) query.set('status', params.status);
    const data = await api.get<any>(`/api/rfqs?${query.toString()}`);
    return snakeToCamel(data);
  },
  getById: async (id: string) => {
    const data = await api.get<any>(`/api/rfqs/${id}`);
    return snakeToCamel(data);
  },
  create: async (payload: any) => {
    const data = await api.post<any>('/api/rfqs', camelToSnake(payload));
    return snakeToCamel(data);
  },
  update: async (id: string, payload: any) => {
    const data = await api.put<any>(`/api/rfqs/${id}`, camelToSnake(payload));
    return snakeToCamel(data);
  },
  delete: async (id: string) => {
    return api.delete(`/api/rfqs/${id}`);
  },
  assignVendors: async (rfqId: string, vendorIds: string[]) => {
    const data = await api.post<any>(`/api/rfqs/${rfqId}/assign-vendors`, { vendor_ids: vendorIds });
    return snakeToCamel(data);
  },
  publish: async (rfqId: string) => {
    const data = await api.post<any>(`/api/rfqs/${rfqId}/publish`);
    return snakeToCamel(data);
  },
  close: async (rfqId: string) => {
    const data = await api.post<any>(`/api/rfqs/${rfqId}/close`);
    return snakeToCamel(data);
  },
};

// ─── Quotations ──────────────────────────────────────────────────────────────

export const quotationAPI = {
  list: async (params?: { rfqId?: string; vendorId?: string; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.rfqId) query.set('rfq_id', params.rfqId);
    if (params?.vendorId) query.set('vendor_id', params.vendorId);
    if (params?.status) query.set('status', params.status);
    const data = await api.get<any>(`/api/quotations?${query.toString()}`);
    return snakeToCamel(data);
  },
  listForRFQ: async (rfqId: string) => {
    const data = await api.get<any>(`/api/quotations/rfq/${rfqId}/list`);
    return snakeToCamel(data);
  },
  compareForRFQ: async (rfqId: string) => {
    const data = await api.get<any>(`/api/quotations/rfq/${rfqId}/compare`);
    return snakeToCamel(data);
  },
  create: async (payload: any) => {
    const data = await api.post<any>('/api/quotations', camelToSnake(payload));
    return snakeToCamel(data);
  },
  update: async (id: string, payload: any) => {
    const data = await api.put<any>(`/api/quotations/${id}`, camelToSnake(payload));
    return snakeToCamel(data);
  },
  submit: async (id: string) => {
    const data = await api.post<any>(`/api/quotations/${id}/submit`);
    return snakeToCamel(data);
  },
  getById: async (id: string) => {
    const data = await api.get<any>(`/api/quotations/${id}`);
    return snakeToCamel(data);
  },
};

// ─── Approvals ───────────────────────────────────────────────────────────────

export const approvalAPI = {
  list: async (params?: { page?: number; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.status) query.set('status', params.status);
    const data = await api.get<any>(`/api/approvals?${query.toString()}`);
    return snakeToCamel(data);
  },
  getById: async (id: string) => {
    const data = await api.get<any>(`/api/approvals/${id}`);
    return snakeToCamel(data);
  },
  create: async (rfqId: string, quotationId: string) => {
    const data = await api.post<any>('/api/approvals', {
      rfq_id: rfqId, quotation_id: quotationId,
    });
    return snakeToCamel(data);
  },
  approve: async (id: string, remarks?: string) => {
    const data = await api.post<any>(`/api/approvals/${id}/approve`, { remarks });
    return snakeToCamel(data);
  },
  reject: async (id: string, remarks?: string) => {
    const data = await api.post<any>(`/api/approvals/${id}/reject`, { remarks });
    return snakeToCamel(data);
  },
};

// ─── Purchase Orders ─────────────────────────────────────────────────────────

export const purchaseOrderAPI = {
  list: async (params?: { page?: number; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.status) query.set('status', params.status);
    const data = await api.get<any>(`/api/purchase-orders?${query.toString()}`);
    return snakeToCamel(data);
  },
  getById: async (id: string) => {
    const data = await api.get<any>(`/api/purchase-orders/${id}`);
    return snakeToCamel(data);
  },
  create: async (approvalId: string, notes?: string) => {
    const data = await api.post<any>('/api/purchase-orders', {
      approval_id: approvalId, notes,
    });
    return snakeToCamel(data);
  },
  updateStatus: async (id: string, status: string, notes?: string) => {
    const data = await api.put<any>(`/api/purchase-orders/${id}/status`, { status, notes });
    return snakeToCamel(data);
  },
};

// ─── Invoices ────────────────────────────────────────────────────────────────

export const invoiceAPI = {
  list: async (params?: { page?: number; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.status) query.set('status', params.status);
    const data = await api.get<any>(`/api/invoices?${query.toString()}`);
    return snakeToCamel(data);
  },
  getById: async (id: string) => {
    const data = await api.get<any>(`/api/invoices/${id}`);
    return snakeToCamel(data);
  },
  create: async (purchaseOrderId: string, notes?: string) => {
    const data = await api.post<any>('/api/invoices', {
      purchase_order_id: purchaseOrderId, notes,
    });
    return snakeToCamel(data);
  },
  issue: async (id: string) => {
    const data = await api.post<any>(`/api/invoices/${id}/issue`);
    return snakeToCamel(data);
  },
  markPaid: async (id: string) => {
    const data = await api.post<any>(`/api/invoices/${id}/mark-paid`);
    return snakeToCamel(data);
  },
  downloadPDF: async (id: string) => {
    return api.getBlob(`/api/invoices/${id}/pdf`);
  },
};

// ─── Analytics ───────────────────────────────────────────────────────────────

export const analyticsAPI = {
  getDashboard: async () => {
    const data = await api.get<any>('/api/analytics/dashboard');
    return snakeToCamel(data);
  },
  getVendorPerformance: async () => {
    const data = await api.get<any>('/api/analytics/vendor-performance');
    return snakeToCamel(data);
  },
  getMonthlyTrends: async (months: number = 6) => {
    const data = await api.get<any>(`/api/analytics/monthly-trends?months=${months}`);
    return snakeToCamel(data);
  },
  getSpending: async () => {
    const data = await api.get<any>('/api/analytics/spending');
    return snakeToCamel(data);
  },
};

// ─── Notifications ───────────────────────────────────────────────────────────

export const notificationAPI = {
  list: async (params?: { page?: number; unreadOnly?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.unreadOnly) query.set('unread_only', 'true');
    const data = await api.get<any>(`/api/notifications/my?${query.toString()}`);
    return snakeToCamel(data);
  },
  markRead: async (id: string) => {
    return api.put(`/api/notifications/${id}/read`);
  },
  markAllRead: async () => {
    return api.put('/api/notifications/mark-all-read');
  },
};

// ─── Activity Logs ───────────────────────────────────────────────────────────

export const activityLogAPI = {
  list: async (params?: { page?: number; entityType?: string; action?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.entityType) query.set('entity_type', params.entityType);
    if (params?.action) query.set('action', params.action);
    const data = await api.get<any>(`/api/activity-logs?${query.toString()}`);
    return snakeToCamel(data);
  },
};
