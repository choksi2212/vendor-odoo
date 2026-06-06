import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { api, tokenManager } from '../lib/api/client';

// Backend role values
export type BackendRole = 'procurement_officer' | 'vendor' | 'manager' | 'admin';

// Display-friendly role names (for UI)
export type DisplayRole = 'Procurement Officer' | 'Vendor' | 'Manager / Approver' | 'Admin';

// For backward compatibility
export type Role = DisplayRole;

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
  // Backward compatibility
  setRole: (r: DisplayRole) => void;
  setName: (n: string) => void;
  // New real auth methods
  login: (email: string, password: string) => Promise<{ requires2FA?: boolean; pendingToken?: string }>;
  signup: (data: SignupData) => Promise<void>;
  logout: () => Promise<void>;
  verifyOTP: (pendingToken: string, otp: string) => Promise<void>;
}

interface SignupData {
  email: string;
  username?: string;
  password: string;
  confirmPassword: string;
  role: BackendRole;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount, try to restore session
  useEffect(() => {
    const restoreSession = async () => {
      // Skip on server-side rendering
      if (typeof window === 'undefined') {
        setIsLoading(false);
        return;
      }

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
    await api.post('/api/auth/signup', {
      email: data.email,
      username: data.username || null,
      password: data.password,
      confirm_password: data.confirmPassword,
      role: data.role,
    });
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

  // Backward compatibility methods (no-ops for now)
  const setRole = (r: DisplayRole) => {
    console.warn('setRole is deprecated, use real authentication');
  };

  const setName = (n: string) => {
    console.warn('setName is deprecated, use real authentication');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        role: user?.displayRole || 'Procurement Officer',
        name: user?.username || user?.email || '',
        setRole,
        setName,
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
