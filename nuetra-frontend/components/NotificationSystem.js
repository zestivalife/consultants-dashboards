const React = require('react');
const { useState, useEffect } = React;
const { Bell, X, Calendar, Users, TrendingUp, AlertCircle } = require('lucide-react');
const { apiRequest } = require('../lib/api');

const NotificationSystem = () => {
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const data = await apiRequest('/notifications?limit=50');
      const items = Array.isArray(data) ? data : (data?.notifications || []);
      setNotifications(items);
      setUnreadCount(items.filter((n) => !n.read).length);
    } catch (error) {
      // Silently fail — notifications are non-critical
      setNotifications([]);
      setUnreadCount(0);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await apiRequest(`/notifications/${notificationId}/read`, { method: 'PUT' });
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await apiRequest('/notifications/mark-all-read', { method: 'PUT' });
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };

  const deleteNotification = async (notificationId) => {
    try {
      await apiRequest(`/notifications/${notificationId}`, { method: 'DELETE' });
      const target = notifications.find((n) => n.id === notificationId);
      if (target && !target.read) setUnreadCount((prev) => Math.max(0, prev - 1));
      setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  const getNotificationIcon = (type) => {
    const iconProps = { className: 'h-5 w-5' };
    switch (type) {
      case 'session':
        return React.createElement(Calendar, { ...iconProps, className: 'h-5 w-5 text-blue-500' });
      case 'wellness':
        return React.createElement(TrendingUp, { ...iconProps, className: 'h-5 w-5 text-green-500' });
      case 'system':
        return React.createElement(AlertCircle, { ...iconProps, className: 'h-5 w-5 text-yellow-500' });
      case 'achievement':
        return React.createElement(Users, { ...iconProps, className: 'h-5 w-5 text-purple-500' });
      default:
        return React.createElement(Bell, { ...iconProps, className: 'h-5 w-5 text-gray-500' });
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'border-red-200 bg-red-50';
      case 'medium': return 'border-yellow-200 bg-yellow-50';
      default: return 'border-gray-200 bg-white';
    }
  };

  return React.createElement('div', { className: 'relative' },
    React.createElement('button', {
      onClick: () => setIsOpen(!isOpen),
      className: 'relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors'
    },
      React.createElement(Bell, { className: 'h-6 w-6' }),
      unreadCount > 0 && React.createElement('span', {
        className: 'absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center'
      }, unreadCount > 9 ? '9+' : unreadCount)
    ),

    isOpen && React.createElement('div', {
      className: 'absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50'
    },
      React.createElement('div', { className: 'p-4 border-b border-gray-200' },
        React.createElement('div', { className: 'flex items-center justify-between' },
          React.createElement('h3', { className: 'text-lg font-semibold' }, 'Notifications'),
          React.createElement('div', { className: 'flex items-center gap-2' },
            unreadCount > 0 && React.createElement('button', {
              onClick: markAllAsRead,
              className: 'text-sm text-blue-600 hover:text-blue-800'
            }, 'Mark all read'),
            React.createElement('button', {
              onClick: () => setIsOpen(false),
              className: 'text-gray-400 hover:text-gray-600'
            }, React.createElement(X, { className: 'h-5 w-5' }))
          )
        )
      ),

      React.createElement('div', { className: 'max-h-96 overflow-y-auto' },
        notifications.length === 0
          ? React.createElement('div', { className: 'p-6 text-center text-gray-500' },
              React.createElement(Bell, { className: 'h-12 w-12 mx-auto mb-3 text-gray-300' }),
              React.createElement('p', null, 'No notifications yet')
            )
          : notifications.map((notification) =>
              React.createElement('div', {
                key: notification.id,
                className: `p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                  !notification.read ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                } ${getPriorityColor(notification.priority)}`
              },
                React.createElement('div', { className: 'flex items-start gap-3' },
                  getNotificationIcon(notification.type),
                  React.createElement('div', { className: 'flex-1 min-w-0' },
                    React.createElement('p', { className: 'text-sm font-medium text-gray-900 mb-1' }, notification.title),
                    React.createElement('p', { className: 'text-sm text-gray-600 mb-2' }, notification.message),
                    React.createElement('p', { className: 'text-xs text-gray-400' }, new Date(notification.timestamp).toLocaleString())
                  ),
                  React.createElement('div', { className: 'flex items-center gap-1' },
                    !notification.read && React.createElement('button', {
                      onClick: () => markAsRead(notification.id),
                      className: 'text-xs text-blue-600 hover:text-blue-800'
                    }, 'Mark read'),
                    React.createElement('button', {
                      onClick: () => deleteNotification(notification.id),
                      className: 'text-gray-400 hover:text-red-600 p-1'
                    }, React.createElement(X, { className: 'h-3 w-3' }))
                  )
                )
              )
            )
      ),

      React.createElement('div', { className: 'p-3 border-t border-gray-200' },
        React.createElement('button', {
          onClick: () => setIsOpen(false),
          className: 'text-sm text-center text-blue-600 hover:text-blue-800 w-full'
        }, 'View all notifications')
      )
    )
  );
};

module.exports = NotificationSystem;
