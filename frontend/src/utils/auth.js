// Authentication utility functions

export const isAuthenticated = () => {
  const token = localStorage.getItem('authToken');
  return !!token;
};

export const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

// Alias for getAuthToken
export const getToken = () => {
  return localStorage.getItem('authToken');
};

// Check if token is valid (basic check)
export const isValidToken = (token) => {
  if (!token) {
    token = getAuthToken();
  }
  if (!token) return false;

  // Basic validation - token exists and is not empty
  // In a real app, you'd decode and check expiration
  return token.length > 0;
};

export const setAuthToken = (token) => {
  localStorage.setItem('authToken', token);
};

export const removeAuthToken = () => {
  localStorage.removeItem('authToken');
};

export const getUser = () => {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    try {
      return JSON.parse(userStr);
    } catch (e) {
      return null;
    }
  }
  return null;
};

export const setUser = (user) => {
  localStorage.setItem('user', JSON.stringify(user));
};

export const removeUser = () => {
  localStorage.removeItem('user');
};

export const logout = () => {
  removeAuthToken();
  removeUser();
};

export default {
  isAuthenticated,
  getAuthToken,
  getToken,
  isValidToken,
  setAuthToken,
  removeAuthToken,
  getUser,
  setUser,
  removeUser,
  logout,
};
