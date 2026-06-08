import React from 'react';

/**
 * ModalHeader - Consistent header with close button
 * Provides standardized modal header styling
 */
const ModalHeader = ({
  title,
  subtitle,
  icon: Icon,
  className = '',
}) => {
  return (
    <div className={`px-6 py-5 border-b border-gray-200 ${className}`}>
      <div className="flex items-start gap-4">
        {Icon && (
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#64ae00] to-[#7dc41f] flex items-center justify-center flex-shrink-0">
            <Icon className="w-6 h-6 text-white" />
          </div>
        )}
        <div className="flex-1 pr-8">
          <h2 className="text-xl font-bold text-gray-900">{title}</h2>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ModalHeader;

