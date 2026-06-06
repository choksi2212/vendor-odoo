# VENDORBRIDGE - FRONTEND BACKEND INTEGRATION GUIDE
## Complete Step-by-Step Instructions for Connecting Frontend to Real Backend API

---

**Purpose:** This document tells the frontend developer EXACTLY what to change, in which file, and how, to switch from mock data to the real backend API.

**Backend Base URL:** `http://localhost:8000` (development) or your deployed Railway URL (production)

**Authentication:** JWT Bearer tokens in Authorization header

**Data Format:** Backend returns snake_case JSON. Frontend needs camelCase. A transformation utility is provided below.

---

## TABLE OF CONTENTS

1. [Overview of Changes Required](#1-overview-of-changes-required)
2. [Step 1: Create Environment Configuration](#2-step-1-create-environment-configuration)
3. [Step 2: Create API Client with Token Management](#3-step-2-create-api-client-with-token-management)
4. [Step 3: Replace AuthContext with Real JWT Auth](#4-step-3-replace-authcontext-with-real-jwt-auth)
5. [Step 4: Create Data Transformation Utilities](#5-step-4-create-data-transformation-utilities)
6. [Step 5: Replace Mock Data in Each Page](#6-step-5-replace-mock-data-in-each-page)
7. [Step 6: WebSocket Integration for Notifications](#7-step-6-websocket-integration-for-notifications)
8. [Complete API Endpoint Reference](#8-complete-api-endpoint-reference)
9. [Data Type Mappings (Frontend vs Backend)](#9-data-type-mappings)
10. [Role System Changes](#10-role-system-changes)
11. [Error Handling](#11-error-handling)
12. [Testing the Integration](#12-testing-the-integration)

---

## 1. OVERVIEW OF CHANGES REQUIRED

### Files to CREATE (new files):
```
src/lib/api/client.ts           -- API client with auth interceptor
src/lib/api/types.ts            -- TypeScript interfaces matching backend responses
src/lib/api/endpoints.ts        -- All API endpoint functions
src/lib/api/transform.ts        -- snake_case to camelCase converter
src/lib/api/websocket.ts        -- WebSocket client for real-time notifications
```

### Files to MODIFY:
```
src/context/AuthContext.tsx      -- Replace mock auth with real JWT flow
src/routes/login.tsx             -- Call real login API
src/routes/signup.tsx            -- Call real signup API
src/routes/dashboard.tsx         -- Fetch from /api/analytics/dashboard
src/routes/vendors/index.tsx     -- Fetch from /api/vendors
src/routes/vendors/add.tsx       -- POST to /api/vendors
src/routes/vendors/$id.tsx       -- Fetch from /api/vendors/:id
src/routes/vendors/edit/$id.tsx  -- PUT to /api/vendors/:id
src/routes/rfq/index.tsx         -- Fetch from /api/rfqs
src/routes/rfq/create.tsx        -- POST to /api/rfqs
src/routes/rfq/$id/index.tsx     -- Fetch from /api/rfqs/:id
src/routes/rfq/$id/compare.tsx   -- Fetch from /api/quotations/rfq/:id/compare
src/routes/quotations/index.tsx  -- Fetch from /api/quotations/rfq/:rfqId/list
src/routes/quotations/submit/$rfqId.tsx -- POST to /api/quotations
src/routes/approvals.tsx         -- Fetch/POST /api/approvals
src/routes/purchase-orders/index.tsx -- Fetch from /api/purchase-orders
src/routes/purchase-orders/$id.tsx   -- Fetch from /api/purchase-orders/:id
src/routes/invoices/index.tsx    -- Fetch from /api/invoices
src/routes/invoices/$id.tsx      -- Fetch from /api/invoices/:id
src/routes/invoices/create.tsx   -- POST to /api/invoices
src/routes/activity-logs.tsx     -- Fetch from /api/activity-logs
src/routes/reports.tsx           -- Fetch from /api/analytics/*
```

### Files to DELETE (no longer needed after integration):
```
src/data/mockData.ts             -- All mock data removed
src/data/mockVendors.ts          -- All mock vendor data removed
```

---

## 2. STEP 1: CREATE ENVIRONMENT CONFIGURATION

### Create file: `.env.local`

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Create file: `.env.production`

```env
VITE_API_URL=https://your-railway-backend-url.up.railway.app
VITE_WS_URL=wss://your-railway-backend-url.up.railway.app
```

### Create file: `src/lib/config.ts`

```typescript
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
```

---

## 3. STEP 2: CREATE API CLIENT WITH TOKEN MANAGEMENT

### Create file: `src/lib/api/client.ts`

```typescript
import { API_BASE_URL } from '../config';

// ─── Token Management ────────────────────────────────────────────────────────

class TokenManager {
  private accessToken: string | null = null;

  getAccessToken(): string | null {
    return this.accessToken;
  }

  setAccessToken(token: string): void {
    this.accessToken = token;
  }

  getRefreshToken(): string | null {
    return localStorage.getItem('vb_refresh_token');
  }

  setRefreshToken(token: string): void {
    localStorage.setItem('vb_refresh_token', token);
  }

  clearTokens(): void {
    this.accessToken = null;
    localStorage.removeItem('vb_refresh_token');
  }

  async refreshAccessToken(): Promise<string> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      this.clearTokens();
      throw new Error('Token refresh failed');
    }

    const data = await response.json();
    this.setAccessToken(data.access_token);
    this.setRefreshToken(data.refresh_token);
    return data.access_token;
  }
}

export const tokenManager = new TokenManager();

// ─── API Client ──────────────────────────────────────────────────────────────

class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const accessToken = tokenManager.getAccessToken();

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
        ...options?.headers,
      },
    });

    // Handle 401 - try to refresh token
    if (response.status === 401) {
      try {
        await tokenManager.refreshAccessToken();
        // Retry request with new token
        return this.request(endpoint, options);
      } catch {
        tokenManager.clearTokens();
        window.location.href = '/login';
        throw new Error('Session expired. Please login again.');
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API Error: ${response.status}`);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // Special method for file downloads (PDF)
  async getBlob(endpoint: string): Promise<Blob> {
    const url = `${this.baseURL}${endpoint}`;
    const accessToken = tokenManager.getAccessToken();

    const response = await fetch(url, {
      headers: {
        ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
      },
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }

    return response.blob();
  }
}

export const api = new APIClient(API_BASE_URL);
```

---

## 4. STEP 3: REPLACE AUTHCONTEXT WITH REAL JWT AUTH

### Replace file: `src/context/AuthContext.tsx`

```typescript
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { api, tokenManager } from '../lib/api/client';

// Backend role values
export type BackendRole = 'procurement_officer' | 'vendor' | 'manager' | 'admin';

// Display-friendly role names (for UI)
export type DisplayRole = 'Procurement Officer' | 'Vendor' | 'Manager / Approver' | 'Admin';

// Mapping between backend roles and display roles
export const ROLE_MAP: Record<BackendRole, DisplayRole> = {
  procurement_officer: 'Procurement Officer',
  vendor: 'Vendor',
  manager: 'Manager / Approver',
  admin: 'Admin',
};

export const REVERSE_ROLE_MAP: Record<DisplayRole, BackendRole> = {
  'Procurement Officer': 'procurement_officer',
  'Vendor': 'vendor',
  'Manager / Approver': 'manager',
  'Admin': 'admin',
};

interface User {
  id: string;
  email: string;
  username: string | null;
  role: BackendRole;
  displayRole: DisplayRole;
  isVerified: boolean;
  is2faEnabled: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  role: DisplayRole;
  name: string;
  login: (email: string, password: string) => Promise<{ requires2FA?: boolean; pendingToken?: string }>;
  signup: (data: SignupData) => Promise<void>;
  logout: () => Promise<void>;
  verifyOTP: (pendingToken: string, otp: string) => Promise<void>;
}

interface SignupData {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
  role: BackendRole;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount, try to restore session
  useEffect(() => {
    const restoreSession = async () => {
      const refreshToken = tokenManager.getRefreshToken();
      if (!refreshToken) {
        setIsLoading(false);
        return;
      }

      try {
        await tokenManager.refreshAccessToken();
        const userData = await api.get<any>('/api/users/me');
        setUser({
          id: userData.id,
          email: userData.email,
          username: userData.username,
          role: userData.role,
          displayRole: ROLE_MAP[userData.role as BackendRole] || 'Procurement Officer',
          isVerified: userData.is_verified,
          is2faEnabled: userData.is_2fa_enabled,
        });
      } catch {
        tokenManager.clearTokens();
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await api.post<any>('/api/auth/login', { email, password });

    if (response.requires_otp) {
      return { requires2FA: true, pendingToken: response.pending_token };
    }

    // Store tokens
    tokenManager.setAccessToken(response.access_token);
    tokenManager.setRefreshToken(response.refresh_token);

    // Fetch user profile
    const userData = await api.get<any>('/api/users/me');
    setUser({
      id: userData.id,
      email: userData.email,
      username: userData.username,
      role: userData.role,
      displayRole: ROLE_MAP[userData.role as BackendRole] || 'Procurement Officer',
      isVerified: userData.is_verified,
      is2faEnabled: userData.is_2fa_enabled,
    });

    return {};
  };

  const verifyOTP = async (pendingToken: string, otp: string) => {
    const response = await api.post<any>('/api/auth/verify-otp', {
      pending_token: pendingToken,
      otp,
    });

    tokenManager.setAccessToken(response.access_token);
    tokenManager.setRefreshToken(response.refresh_token);

    const userData = await api.get<any>('/api/users/me');
    setUser({
      id: userData.id,
      email: userData.email,
      username: userData.username,
      role: userData.role,
      displayRole: ROLE_MAP[userData.role as BackendRole] || 'Procurement Officer',
      isVerified: userData.is_verified,
      is2faEnabled: userData.is_2fa_enabled,
    });
  };

  const signup = async (data: SignupData) => {
    await api.post('/api/auth/signup', data);
  };

  const logout = async () => {
    const refreshToken = tokenManager.getRefreshToken();
    if (refreshToken) {
      try {
        await api.post('/api/auth/logout', { refresh_token: refreshToken });
      } catch {
        // Ignore logout API errors
      }
    }
    tokenManager.clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        role: user?.displayRole || 'Procurement Officer',
        name: user?.username || user?.email || '',
        login,
        signup,
        logout,
        verifyOTP,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
```

---

## 5. STEP 4: CREATE DATA TRANSFORMATION UTILITIES

### Create file: `src/lib/api/transform.ts`

```typescript
/**
 * Converts snake_case keys to camelCase.
 * Backend returns snake_case, frontend uses camelCase.
 */
export function snakeToCamel(obj: any): any {
  if (obj === null || obj === undefined) return obj;
  if (Array.isArray(obj)) return obj.map(snakeToCamel);
  if (typeof obj !== 'object') return obj;

  const result: any = {};
  for (const key of Object.keys(obj)) {
    const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
    result[camelKey] = snakeToCamel(obj[key]);
  }
  return result;
}

/**
 * Converts camelCase keys to snake_case.
 * For sending data TO the backend.
 */
export function camelToSnake(obj: any): any {
  if (obj === null || obj === undefined) return obj;
  if (Array.isArray(obj)) return obj.map(camelToSnake);
  if (typeof obj !== 'object') return obj;

  const result: any = {};
  for (const key of Object.keys(obj)) {
    const snakeKey = key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
    result[snakeKey] = camelToSnake(obj[key]);
  }
  return result;
}
```

---

## 6. STEP 5: REPLACE MOCK DATA IN EACH PAGE

### Create file: `src/lib/api/endpoints.ts`

This is the central file for ALL API calls. Each page imports from here.

```typescript
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
```

---

## 7. STEP 6: PAGE-BY-PAGE CHANGES

### 7.1 Login Page (`src/routes/login.tsx`)

**BEFORE (mock):**
```tsx
const onSubmit = () => {
  setRole(selectedRole);
  setName("Alex Morgan");
  navigate({ to: '/dashboard' });
};
```

**AFTER (real API):**
```tsx
import { useAuth } from '../context/AuthContext';

const { login } = useAuth();
const [error, setError] = useState<string | null>(null);
const [isLoading, setIsLoading] = useState(false);

const onSubmit = async (data: { email: string; password: string }) => {
  setIsLoading(true);
  setError(null);
  try {
    const result = await login(data.email, data.password);
    if (result.requires2FA) {
      navigate({ to: '/verify-otp', search: { pendingToken: result.pendingToken } });
    } else {
      navigate({ to: '/dashboard' });
    }
  } catch (err: any) {
    setError(err.message || 'Invalid credentials');
  } finally {
    setIsLoading(false);
  }
};
```

### 7.2 Signup Page (`src/routes/signup.tsx`)

**AFTER (real API):**
```tsx
import { useAuth, REVERSE_ROLE_MAP } from '../context/AuthContext';

const { signup } = useAuth();

const onSubmit = async (data: FormData) => {
  setIsLoading(true);
  try {
    await signup({
      email: data.email,
      username: data.username,
      password: data.password,
      confirm_password: data.confirmPassword,
      role: REVERSE_ROLE_MAP[data.role], // Convert display role to backend role
    });
    // Show success, redirect to login
    navigate({ to: '/login' });
  } catch (err: any) {
    setError(err.message);
  } finally {
    setIsLoading(false);
  }
};
```

### 7.3 Dashboard (`src/routes/dashboard.tsx`)

**BEFORE:** Uses hardcoded stat values.

**AFTER:**
```tsx
import { analyticsAPI } from '../lib/api/endpoints';
import { useState, useEffect } from 'react';

const [stats, setStats] = useState<any>(null);
const [isLoading, setIsLoading] = useState(true);

useEffect(() => {
  const loadDashboard = async () => {
    try {
      const data = await analyticsAPI.getDashboard();
      setStats(data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };
  loadDashboard();
}, []);

// Use stats.pendingApprovals, stats.activeRfqs, stats.totalPosThisMonth, etc.
```

### 7.4 Vendors List (`src/routes/vendors/index.tsx`)

**BEFORE:** `const vendors = mockVendors;`

**AFTER:**
```tsx
import { vendorAPI } from '../../lib/api/endpoints';

const [vendors, setVendors] = useState<any[]>([]);
const [total, setTotal] = useState(0);
const [isLoading, setIsLoading] = useState(true);
const [search, setSearch] = useState('');
const [statusFilter, setStatusFilter] = useState<string | undefined>();

const loadVendors = async () => {
  setIsLoading(true);
  try {
    const data = await vendorAPI.list({ search, status: statusFilter });
    setVendors(data.items);
    setTotal(data.total);
  } catch (err) {
    console.error(err);
  } finally {
    setIsLoading(false);
  }
};

useEffect(() => { loadVendors(); }, [search, statusFilter]);
```

### 7.5 Add Vendor (`src/routes/vendors/add.tsx`)

**AFTER:**
```tsx
import { vendorAPI } from '../../lib/api/endpoints';

const onSubmit = async (data: VendorFormData) => {
  setIsLoading(true);
  try {
    await vendorAPI.create({
      name: data.name,
      gstNumber: data.gstNumber,  // Will be converted to gst_number by camelToSnake
      email: data.email,
      phone: data.phone,
      address: data.address,
      categoryId: data.categoryId,
    });
    navigate({ to: '/vendors' });
  } catch (err: any) {
    setError(err.message);
  } finally {
    setIsLoading(false);
  }
};
```

### 7.6 RFQ Create (`src/routes/rfq/create.tsx`)

**AFTER:**
```tsx
import { rfqAPI, vendorAPI } from '../../lib/api/endpoints';

// Load vendors for assignment dropdown
const [vendors, setVendors] = useState<any[]>([]);
useEffect(() => {
  vendorAPI.list({ page: 1 }).then(data => setVendors(data.items));
}, []);

const onSubmit = async (data: RFQFormData) => {
  setIsLoading(true);
  try {
    // Step 1: Create RFQ
    const rfq = await rfqAPI.create({
      title: data.title,
      description: data.description,
      productName: data.productName,
      quantity: data.quantity,
      unit: data.unit,
      deadline: data.deadline, // YYYY-MM-DD string
    });

    // Step 2: Assign vendors (if selected)
    if (data.vendorIds && data.vendorIds.length > 0) {
      await rfqAPI.assignVendors(rfq.id, data.vendorIds);
    }

    navigate({ to: '/rfq' });
  } catch (err: any) {
    setError(err.message);
  } finally {
    setIsLoading(false);
  }
};
```

### 7.7 RFQ Detail (`src/routes/rfq/$id/index.tsx`)

**AFTER:**
```tsx
import { rfqAPI } from '../../../lib/api/endpoints';

const { id } = Route.useParams();
const [rfq, setRFQ] = useState<any>(null);

useEffect(() => {
  rfqAPI.getById(id).then(setRFQ);
}, [id]);

// rfq.title, rfq.productName, rfq.quantity, rfq.deadline, rfq.status
// rfq.vendors (array of assigned vendors)
// rfq.attachments (array of uploaded files)
```

### 7.8 Compare Quotations (`src/routes/rfq/$id/compare.tsx`)

**AFTER:**
```tsx
import { quotationAPI } from '../../../lib/api/endpoints';

const { id } = Route.useParams();
const [comparison, setComparison] = useState<any>(null);

useEffect(() => {
  quotationAPI.compareForRFQ(id).then(setComparison);
}, [id]);

// comparison.quotations - array of quotation items
// Each has: vendorName, unitPrice, totalPrice, deliveryDays, isLowestPrice, isFastestDelivery
// comparison.lowestPrice, comparison.highestPrice, comparison.averagePrice
// comparison.fastestDelivery, comparison.slowestDelivery
```

### 7.9 Quotations - Submit (`src/routes/quotations/submit/$rfqId.tsx`)

**AFTER:**
```tsx
import { quotationAPI } from '../../../lib/api/endpoints';

const { rfqId } = Route.useParams();

const onSubmit = async (data: QuotationFormData) => {
  try {
    // Create quotation (draft)
    const quotation = await quotationAPI.create({
      rfqId: rfqId,
      vendorId: currentVendorId, // Get from user context or vendor list
      unitPrice: data.unitPrice,
      deliveryDays: data.deliveryDays,
      notes: data.notes,
    });

    // Submit it (locks it)
    await quotationAPI.submit(quotation.id);

    navigate({ to: '/quotations' });
  } catch (err: any) {
    setError(err.message);
  }
};
```

### 7.10 Approvals (`src/routes/approvals.tsx`)

**AFTER:**
```tsx
import { approvalAPI } from '../lib/api/endpoints';

const [approvals, setApprovals] = useState<any[]>([]);

useEffect(() => {
  approvalAPI.list().then(data => setApprovals(data.items));
}, []);

// Approve action
const handleApprove = async (approvalId: string) => {
  await approvalAPI.approve(approvalId, 'Approved');
  // Reload list
  const data = await approvalAPI.list();
  setApprovals(data.items);
};

// Reject action
const handleReject = async (approvalId: string, remarks: string) => {
  await approvalAPI.reject(approvalId, remarks);
  const data = await approvalAPI.list();
  setApprovals(data.items);
};
```

### 7.11 Purchase Orders (`src/routes/purchase-orders/index.tsx`)

**AFTER:**
```tsx
import { purchaseOrderAPI } from '../../lib/api/endpoints';

const [pos, setPOs] = useState<any[]>([]);

useEffect(() => {
  purchaseOrderAPI.list().then(data => setPOs(data.items));
}, []);

// Each PO has: poNumber, vendorName, subtotal, taxAmount, totalAmount, status, lineItems
```

### 7.12 Purchase Order Detail (`src/routes/purchase-orders/$id.tsx`)

**AFTER:**
```tsx
import { purchaseOrderAPI, invoiceAPI } from '../../lib/api/endpoints';

const { id } = Route.useParams();
const [po, setPO] = useState<any>(null);

useEffect(() => { purchaseOrderAPI.getById(id).then(setPO); }, [id]);

// Generate Invoice action
const handleGenerateInvoice = async () => {
  await invoiceAPI.create(po.id, 'Net 30 days');
  navigate({ to: '/invoices' });
};
```

### 7.13 Invoices (`src/routes/invoices/index.tsx`)

**AFTER:**
```tsx
import { invoiceAPI } from '../../lib/api/endpoints';

const [invoices, setInvoices] = useState<any[]>([]);

useEffect(() => {
  invoiceAPI.list().then(data => setInvoices(data.items));
}, []);
```

### 7.14 Invoice Detail (`src/routes/invoices/$id.tsx`)

**AFTER:**
```tsx
import { invoiceAPI } from '../../lib/api/endpoints';

const { id } = Route.useParams();
const [invoice, setInvoice] = useState<any>(null);

useEffect(() => { invoiceAPI.getById(id).then(setInvoice); }, [id]);

// Download PDF
const handleDownloadPDF = async () => {
  const blob = await invoiceAPI.downloadPDF(id);
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${invoice.invoiceNumber}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
};

// Mark as Paid
const handleMarkPaid = async () => {
  const updated = await invoiceAPI.markPaid(id);
  setInvoice(updated);
};
```

### 7.15 Activity Logs (`src/routes/activity-logs.tsx`)

**AFTER:**
```tsx
import { activityLogAPI } from '../lib/api/endpoints';

const [logs, setLogs] = useState<any[]>([]);
const [filter, setFilter] = useState<string | undefined>();

useEffect(() => {
  activityLogAPI.list({ entityType: filter }).then(data => setLogs(data.items));
}, [filter]);

// Tab filters: All (undefined), RFQ ("RFQ"), Approval ("APPROVAL"), Invoice ("INVOICE")
```

### 7.16 Reports (`src/routes/reports.tsx`)

**AFTER:**
```tsx
import { analyticsAPI } from '../lib/api/endpoints';

const [spending, setSpending] = useState<any>(null);
const [vendorPerf, setVendorPerf] = useState<any>(null);
const [trends, setTrends] = useState<any>(null);

useEffect(() => {
  analyticsAPI.getSpending().then(setSpending);
  analyticsAPI.getVendorPerformance().then(setVendorPerf);
  analyticsAPI.getMonthlyTrends(6).then(setTrends);
}, []);

// spending.totalSpend, spending.breakdown (array of vendor spending items)
// vendorPerf.vendors (array of vendor performance items)
// trends.months (array of monthly data for charts)
```

---

## 8. STEP 6: WEBSOCKET INTEGRATION

### Create file: `src/lib/api/websocket.ts`

```typescript
import { WS_BASE_URL } from '../config';
import { tokenManager } from './client';

class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: ((data: any) => void)[] = [];

  connect(): void {
    const token = tokenManager.getAccessToken();
    if (!token) return;

    this.ws = new WebSocket(`${WS_BASE_URL}/api/ws/notifications?token=${token}`);

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'notification') {
        this.listeners.forEach((fn) => fn(data.data));
      }
    };

    this.ws.onclose = () => {
      // Reconnect after 5 seconds
      setTimeout(() => this.connect(), 5000);
    };
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }

  onNotification(callback: (data: any) => void): () => void {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((fn) => fn !== callback);
    };
  }
}

export const wsClient = new WebSocketClient();
```

**Usage in Layout component:**
```tsx
import { wsClient } from '../lib/api/websocket';
import { toast } from 'sonner';

useEffect(() => {
  if (isAuthenticated) {
    wsClient.connect();
    const unsub = wsClient.onNotification((data) => {
      toast.info(data.title, { description: data.message });
    });
    return () => { unsub(); wsClient.disconnect(); };
  }
}, [isAuthenticated]);
```

---

## 9. COMPLETE API ENDPOINT REFERENCE

| Method | Endpoint | Purpose | Used In |
|--------|----------|---------|---------|
| POST | /api/auth/signup | Register user | signup.tsx |
| POST | /api/auth/login | Login | login.tsx |
| POST | /api/auth/verify-otp | 2FA OTP verification | verify-otp.tsx |
| POST | /api/auth/refresh | Refresh token | api/client.ts (auto) |
| POST | /api/auth/logout | Logout | AuthContext |
| POST | /api/auth/forgot-password | Request reset | forgot-password.tsx |
| POST | /api/auth/reset-password | Reset password | reset-password.tsx |
| GET | /api/users/me | Get profile | AuthContext |
| POST | /api/users/2fa/enable | Enable 2FA | settings.tsx |
| POST | /api/users/2fa/disable | Disable 2FA | settings.tsx |
| GET | /api/vendors | List vendors | vendors/index.tsx |
| POST | /api/vendors | Create vendor | vendors/add.tsx |
| GET | /api/vendors/:id | Get vendor | vendors/$id.tsx |
| PUT | /api/vendors/:id | Update vendor | vendors/edit/$id.tsx |
| DELETE | /api/vendors/:id | Deactivate | vendors/index.tsx |
| GET | /api/vendors/categories | List categories | vendors/add.tsx |
| POST | /api/vendors/categories | Create category | settings.tsx |
| GET | /api/rfqs | List RFQs | rfq/index.tsx |
| POST | /api/rfqs | Create RFQ | rfq/create.tsx |
| GET | /api/rfqs/:id | RFQ detail | rfq/$id/index.tsx |
| PUT | /api/rfqs/:id | Update RFQ | rfq/$id/index.tsx |
| DELETE | /api/rfqs/:id | Delete RFQ | rfq/index.tsx |
| POST | /api/rfqs/:id/assign-vendors | Assign vendors | rfq/create.tsx |
| POST | /api/rfqs/:id/publish | Publish RFQ | rfq/$id/index.tsx |
| POST | /api/rfqs/:id/close | Close RFQ | rfq/$id/index.tsx |
| POST | /api/quotations | Create quotation | quotations/submit.tsx |
| GET | /api/quotations/:id | Get quotation | quotations/index.tsx |
| PUT | /api/quotations/:id | Update quotation | quotations/submit.tsx |
| POST | /api/quotations/:id/submit | Submit quotation | quotations/submit.tsx |
| GET | /api/quotations/rfq/:id/list | List per RFQ | rfq/$id/index.tsx |
| GET | /api/quotations/rfq/:id/compare | Compare | rfq/$id/compare.tsx |
| GET | /api/approvals | List approvals | approvals.tsx |
| POST | /api/approvals | Create request | rfq/$id/index.tsx |
| GET | /api/approvals/:id | Get detail | approvals.tsx |
| POST | /api/approvals/:id/approve | Approve | approvals.tsx |
| POST | /api/approvals/:id/reject | Reject | approvals.tsx |
| GET | /api/purchase-orders | List POs | purchase-orders/index.tsx |
| POST | /api/purchase-orders | Create PO | purchase-orders/index.tsx |
| GET | /api/purchase-orders/:id | PO detail | purchase-orders/$id.tsx |
| PUT | /api/purchase-orders/:id/status | Update status | purchase-orders/$id.tsx |
| GET | /api/invoices | List invoices | invoices/index.tsx |
| POST | /api/invoices | Create invoice | invoices/create.tsx |
| GET | /api/invoices/:id | Invoice detail | invoices/$id.tsx |
| GET | /api/invoices/:id/pdf | Download PDF | invoices/$id.tsx |
| POST | /api/invoices/:id/issue | Mark issued | invoices/$id.tsx |
| POST | /api/invoices/:id/mark-paid | Mark paid | invoices/$id.tsx |
| GET | /api/analytics/dashboard | Dashboard stats | dashboard.tsx |
| GET | /api/analytics/vendor-performance | Vendor metrics | reports.tsx |
| GET | /api/analytics/monthly-trends | Trends | reports.tsx |
| GET | /api/analytics/spending | Spending | reports.tsx |
| GET | /api/notifications/my | My notifications | Layout.tsx |
| PUT | /api/notifications/:id/read | Mark read | Layout.tsx |
| PUT | /api/notifications/mark-all-read | Mark all | Layout.tsx |
| GET | /api/activity-logs | Audit trail | activity-logs.tsx |
| WS | /api/ws/notifications?token=JWT | Real-time | Layout.tsx |

---

## 10. ROLE SYSTEM CHANGES

### Current Frontend Roles (display names):
```
"Procurement Officer" | "Vendor" | "Manager / Approver" | "Admin"
```

### Backend Roles (stored values):
```
"procurement_officer" | "vendor" | "manager" | "admin"
```

### What to change in Sidebar.tsx:

The sidebar currently uses display role names for filtering. After integration, use the backend role value from `user.role`:

```tsx
// BEFORE
const visibleItems = menuItems.filter(item => 
  item.roles.includes('all') || item.roles.includes(role) // role = "Procurement Officer"
);

// AFTER
const visibleItems = menuItems.filter(item => 
  item.roles.includes('all') || item.roles.includes(user.role) // role = "procurement_officer"
);

// Update menuItems roles to use backend values:
const menuItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['all'] },
  { path: '/vendors', label: 'Vendors', icon: Building2, roles: ['procurement_officer', 'admin'] },
  { path: '/rfq', label: 'RFQs', icon: FileText, roles: ['procurement_officer', 'vendor', 'admin'] },
  { path: '/quotations', label: 'My Quotations', icon: FileCheck, roles: ['vendor'] },
  { path: '/approvals', label: 'Approvals', icon: CheckCircle, roles: ['manager', 'admin'] },
  { path: '/purchase-orders', label: 'Purchase Orders', icon: ShoppingCart, roles: ['procurement_officer', 'admin'] },
  { path: '/invoices', label: 'Invoices', icon: Receipt, roles: ['procurement_officer', 'admin'] },
  { path: '/activity-logs', label: 'Activity Logs', icon: History, roles: ['all'] },
  { path: '/reports', label: 'Reports', icon: BarChart3, roles: ['manager', 'admin', 'procurement_officer'] },
  { path: '/settings', label: 'Settings', icon: Settings, roles: ['admin'] },
];
```

---

## 11. ERROR HANDLING

### Backend Error Format:
```json
{
  "detail": "Human-readable error message"
}
```

### How to handle in frontend:
```tsx
try {
  const data = await someAPICall();
} catch (err: any) {
  // err.message contains the "detail" from backend
  toast.error(err.message);
  // or setError(err.message);
}
```

### Common HTTP Status Codes:
| Code | Meaning | Frontend Action |
|------|---------|-----------------|
| 200 | Success | Use response data |
| 201 | Created | Navigate away or show success |
| 204 | No Content (delete) | Remove from list |
| 400 | Bad Request | Show error message to user |
| 401 | Unauthorized | Auto-refresh token (handled by client) |
| 403 | Forbidden | Show "Access Denied" or hide action |
| 404 | Not Found | Show "Not Found" page |
| 409 | Conflict (duplicate) | Show specific duplicate error |
| 422 | Validation Error | Show field-level errors |
| 429 | Rate Limited | Show "Too many requests, wait" |
| 500 | Server Error | Show "Something went wrong" |

### Validation Error Format (422):
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "gst_number"],
      "msg": "Invalid GST number format.",
      "input": "BADGST"
    }
  ]
}
```

Parse and display per-field:
```tsx
if (response.status === 422) {
  const errors = await response.json();
  errors.detail.forEach((err: any) => {
    const field = err.loc[err.loc.length - 1];
    setFieldError(field, err.msg);
  });
}
```

---

## 12. TESTING THE INTEGRATION

### Step 1: Start Backend Locally
```bash
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### Step 2: Start Frontend
```bash
cd frontend
bun run dev
# or npm run dev
```

### Step 3: Test Each Flow

1. **Signup:** Go to /signup, fill form, submit. Check backend logs for user creation.
2. **Login:** Go to /login, use registered email/password. Should get JWT and redirect.
3. **Dashboard:** Should show real stats (zeroes initially, that's fine).
4. **Create Vendor:** Go to /vendors/add, fill form. Should appear in vendor list.
5. **Create RFQ:** Go to /rfq/create, fill form with real vendor IDs.
6. **Full Workflow:** Create RFQ -> Assign vendor -> Publish -> Submit quotation -> Compare -> Approve -> PO generated -> Create invoice -> Download PDF.

### Step 4: Verify CORS

If you get CORS errors, ensure the backend .env has your frontend URL:
```env
ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

---

## SUMMARY OF KEY DIFFERENCES

| Aspect | Current Frontend (Mock) | After Integration (Real) |
|--------|------------------------|--------------------------|
| Auth | localStorage role string | JWT tokens + /api/users/me |
| Data source | mockData.ts | fetch() to backend API |
| Vendor IDs | String names | UUID strings from backend |
| RFQ IDs | "RFQ-2026-001" format | UUID strings from backend |
| PO Numbers | Same format | Same format (PO-YYYY-XXXX) |
| Invoice Numbers | Same format | Same format (INV-YYYY-XXXX) |
| Field naming | camelCase | Backend: snake_case, use transform.ts |
| Error handling | None | try/catch with toast messages |
| Loading states | None | isLoading state per component |
| Real-time | None | WebSocket notifications |
| PDF download | window.print() | Actual PDF from /api/invoices/:id/pdf |

---

## IMPORTANT NOTES

1. **DO NOT** remove the mock data files until ALL pages are connected and tested.
2. **Keep** the `src/data/` folder as a fallback during development.
3. **Test one page at a time** - don't try to convert everything at once.
4. **Start with auth** (login/signup), then dashboard, then vendors (simplest CRUD).
5. The backend is running on port 8000 by default. Make sure it's started before testing.
6. All backend endpoints return paginated responses for lists: `{ items: [], total: N, page: N, page_size: N, total_pages: N }`.
7. The `transform.ts` utility handles ALL naming conversion automatically.
8. The API client handles token refresh automatically - no manual refresh needed.
