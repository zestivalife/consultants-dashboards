import React from 'react';
import { Inbox, Search, AlertCircle, FileText, Users, Calendar } from 'lucide-react';

/**
 * EmptyState - Consistent empty state designs
 * Displays when there's no data to show with contextual messaging
 */
const EmptyState = ({
  icon: CustomIcon,
  iconType = 'inbox',
  title = 'No data available',
  description = 'Get started by adding your first item.',
  action,
  actionLabel = 'Get Started',
  className = '',
}) => {
  const iconMap = {
    inbox: Inbox,
    search: Search,
    alert: AlertCircle,
    file: FileText,
    users: Users,
    calendar: Calendar,
  };

  const Icon = CustomIcon || iconMap[iconType] || Inbox;

  return (
    <div className={`flex flex-col items-center justify-center py-12 px-4 text-center ${className}`}>
      <div className="w-16 h-16 mb-4 rounded-full bg-gray-100 flex items-center justify-center">
        <Icon className="w-8 h-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-500 max-w-sm mb-6">{description}</p>
      {action && (
        <button
          onClick={action}
          className="btn-primary"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};

export default EmptyState;

