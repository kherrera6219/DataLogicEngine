import React, { createContext, useContext, useState, useCallback } from 'react';
import { useToast } from '@chakra-ui/react';

// Create context
const NotificationContext = createContext();

// Notification types
export const NOTIFICATION_TYPES = {
  INFO: 'info',
  SUCCESS: 'success',
  WARNING: 'warning',
  ERROR: 'error'
};

// Provider component
export const NotificationProvider = ({ children }) => {
  const toast = useToast();
  const [notifications, setNotifications] = useState([]);
  
  // Add notification
  const addNotification = useCallback((message, type = NOTIFICATION_TYPES.INFO, options = {}) => {
    const id = options.id || Date.now().toString();
    const newNotification = {
      id,
      message,
      type,
      timestamp: new Date().toISOString(),
      read: false,
      ...options
    };
    
    // Add to notifications state
    setNotifications(prev => [newNotification, ...prev]);
    
    // Show toast for immediate notification
    if (!options.silent) {
      toast({
        title: options.title || getTypeTitle(type),
        description: message,
        status: type,
        duration: options.duration || 5000,
        isClosable: true,
        position: 'top-right'
      });
    }
    
    return id;
  }, [toast]);
  
  // Get title based on notification type
  const getTypeTitle = (type) => {
    switch (type) {
      case NOTIFICATION_TYPES.SUCCESS:
        return 'Success';
      case NOTIFICATION_TYPES.WARNING:
        return 'Warning';
      case NOTIFICATION_TYPES.ERROR:
        return 'Error';
      case NOTIFICATION_TYPES.INFO:
      default:
        return 'Information';
    }
  };
  
  // Remove notification
  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);
  
  // Mark notification as read
  const markAsRead = useCallback((id) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id 
          ? { ...notification, read: true } 
          : notification
      )
    );
  }, []);
  
  // Mark all notifications as read
  const markAllAsRead = useCallback(() => {
    setNotifications(prev => 
      prev.map(notification => ({ ...notification, read: true }))
    );
  }, []);
  
  // Clear all notifications
  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);
  
  // Get unread count
  const getUnreadCount = useCallback(() => {
    return notifications.filter(notification => !notification.read).length;
  }, [notifications]);
  
  // Convenience methods for different notification types
  const info = useCallback((message, options = {}) => {
    return addNotification(message, NOTIFICATION_TYPES.INFO, options);
  }, [addNotification]);
  
  const success = useCallback((message, options = {}) => {
    return addNotification(message, NOTIFICATION_TYPES.SUCCESS, options);
  }, [addNotification]);
  
  const warning = useCallback((message, options = {}) => {
    return addNotification(message, NOTIFICATION_TYPES.WARNING, options);
  }, [addNotification]);
  
  const error = useCallback((message, options = {}) => {
    return addNotification(message, NOTIFICATION_TYPES.ERROR, options);
  }, [addNotification]);
  
  // Value object with state and actions
  const value = {
    notifications,
    addNotification,
    removeNotification,
    markAsRead,
    markAllAsRead,
    clearAll,
    getUnreadCount,
    info,
    success,
    warning,
    error
  };
  
  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

// Custom hook for using notifications
export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

export default NotificationContext;