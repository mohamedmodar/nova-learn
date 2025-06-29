import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: number;
  full_name: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  has_completed_onboarding: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
  fetchAndSetUser: (token: string) => Promise<User | void>;
}

interface RegisterData {
  full_name: string;
  email: string;
  password: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const API_URL = 'http://localhost:8000';

  useEffect(() => {
    // Check for stored user data on app start
    const token = localStorage.getItem('novalearn_token');
    if (token) {
      fetchAndSetUser(token);
    } else {
    setLoading(false);
    }
  }, []);

  const fetchAndSetUser = async (token: string) => {
    try {
      const response = await fetch(`${API_URL}/students/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch user');
      }

      const userData = await response.json();
      setUser(userData);
      localStorage.setItem('novalearn_user', JSON.stringify(userData));
      return userData;
    } catch (error) {
      console.error(error);
      // Token might be invalid, so log out
      logout();
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await fetch(`${API_URL}/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username: email,
        password: password,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Login failed');
    }

    const data = await response.json();
    const token = data.access_token;
    localStorage.setItem('novalearn_token', token);
    
    return await fetchAndSetUser(token);
  };

  const register = async (userData: RegisterData) => {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        full_name: userData.full_name,
        email: userData.email,
        password: userData.password,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Registration failed');
    }
    
    // Registration successful, but user is not logged in yet.
    // The component will handle redirection to login.
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('novalearn_user');
    localStorage.removeItem('novalearn_token');
  };

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      const updatedUser = { ...user, ...userData };
      setUser(updatedUser);
      localStorage.setItem('novalearn_user', JSON.stringify(updatedUser));
    }
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    updateUser,
    fetchAndSetUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
