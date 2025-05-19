import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

// Create context
const AuthContext = createContext();

// Auth provider component
export const AuthProvider = ({ children, setIsAuthenticated }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('ukg_token') || null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const navigate = useNavigate();
  
  // Configure axios with token
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);
  
  // Check user session on initial load
  useEffect(() => {
    const checkAuth = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      
      try {
        // Fetch user data using token
        const response = await axios.get('/api/auth/me');
        setUser(response.data);
        setIsAuthenticated(true);
        setLoading(false);
      } catch (error) {
        console.error('Authentication error:', error);
        logout();  // Clean up on authentication failure
        setLoading(false);
      }
    };
    
    checkAuth();
  }, [token, setIsAuthenticated]);
  
  // Login function
  const login = async (credentials) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/api/auth/login', credentials);
      const { token, user } = response.data;
      
      // Save token and user data
      localStorage.setItem('ukg_token', token);
      setToken(token);
      setUser(user);
      setIsAuthenticated(true);
      
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.message || 'Authentication failed';
      setError(message);
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };
  
  // Logout function
  const logout = async () => {
    try {
      setLoading(true);
      
      // Optional: Call logout endpoint
      if (token) {
        await axios.post('/api/auth/logout');
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage and state
      localStorage.removeItem('ukg_token');
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);
      setLoading(false);
      navigate('/login');
    }
  };
  
  // Register function for new users
  const register = async (userData) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/api/auth/register', userData);
      return { success: true, message: response.data.message };
    } catch (error) {
      const message = error.response?.data?.message || 'Registration failed';
      setError(message);
      return { success: false, message };
    } finally {
      setLoading(false);
    }
  };
  
  // Context value
  const value = {
    user,
    token,
    loading,
    error,
    isAuthenticated: !!user,
    login,
    logout,
    register
  };
  
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook for using auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;