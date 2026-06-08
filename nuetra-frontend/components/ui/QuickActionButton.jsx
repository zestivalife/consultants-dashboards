import React, { useState } from 'react';
import { Plus, X } from 'lucide-react';

/**
 * QuickActionButton - Floating action button with expandable menu
 * Provides quick access to common actions
 */
const QuickActionButton = ({
  actions = [],
  position = 'bottom-right', // 'bottom-right', 'bottom-left', 'top-right', 'top-left'
  mainIcon: MainIcon = Plus,
  mainLabel = 'Quick Actions',
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const positionClasses = {
    'bottom-right': 'bottom-6 right-6',
    'bottom-left': 'bottom-6 left-6',
    'top-right': 'top-6 right-6',
    'top-left': 'top-6 left-6',
  };

  const menuPositionClasses = {
    'bottom-right': 'bottom-full right-0 mb-4',
    'bottom-left': 'bottom-full left-0 mb-4',
    'top-right': 'top-full right-0 mt-4',
    'top-left': 'top-full left-0 mt-4',
  };

  return (
    <div className={`fixed ${positionClasses[position]} z-50 ${className}`}>
      {/* Action Menu */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black bg-opacity-20 z-40"
            onClick={() => setIsOpen(false)}
          ></div>

          {/* Menu Items */}
          <div
            className={`absolute ${menuPositionClasses[position]} z-50 space-y-2 animate-fadeInUp`}
          >
            {actions.map((action, index) => (
              <button
                key={index}
                onClick={() => {
                  action.onClick();
                  setIsOpen(false);
                }}
                className="flex items-center gap-3 px-4 py-3 bg-white rounded-xl shadow-lg hover:shadow-xl transition-all hover:-translate-y-0.5 min-w-[200px] group"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${action.color || 'from-gray-500 to-gray-600'} flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform`}>
                  {action.icon && <action.icon className="w-5 h-5 text-white" />}
                </div>
                <div className="text-left">
                  <p className="font-semibold text-gray-900 text-sm">
                    {action.label}
                  </p>
                  {action.description && (
                    <p className="text-xs text-gray-500">{action.description}</p>
                  )}
                </div>
              </button>
            ))}
          </div>
        </>
      )}

      {/* Main FAB */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-14 h-14 rounded-full bg-gradient-to-br from-[#64ae00] to-[#7dc41f] text-white shadow-lg hover:shadow-xl transition-all hover:scale-110 flex items-center justify-center group relative z-50 ${
          isOpen ? 'rotate-45' : ''
        }`}
        aria-label={mainLabel}
        title={mainLabel}
      >
        {isOpen ? (
          <X className="w-6 h-6 transition-transform" />
        ) : (
          <MainIcon className="w-6 h-6 transition-transform" />
        )}
      </button>
    </div>
  );
};

export default QuickActionButton;

