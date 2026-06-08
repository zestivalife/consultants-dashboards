import React, { useEffect } from 'react';
import { X } from 'lucide-react';

/**
 * Drawer - Slide-over panel variant
 * Slides in from the right side of the screen
 */
const Drawer = ({
  isOpen,
  onClose,
  children,
  title,
  subtitle,
  position = 'right', // 'left', 'right'
  size = 'md', // 'sm', 'md', 'lg'
  closeOnBackdrop = true,
  closeOnEsc = true,
  className = '',
}) => {
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-2xl',
  };

  const positionClasses = {
    left: {
      container: 'left-0',
      animation: isOpen ? 'translate-x-0' : '-translate-x-full',
    },
    right: {
      container: 'right-0',
      animation: isOpen ? 'translate-x-0' : 'translate-x-full',
    },
  };

  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e) => {
      if (closeOnEsc && e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, closeOnEsc, onClose]);

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black transition-opacity z-[var(--z-modal)] ${
          isOpen ? 'opacity-50' : 'opacity-0 pointer-events-none'
        }`}
        onClick={closeOnBackdrop ? onClose : undefined}
        aria-hidden="true"
      ></div>

      {/* Drawer Panel */}
      <div
        className={`fixed top-0 ${positionClasses[position].container} h-full w-full ${sizeClasses[size]} bg-white shadow-2xl z-[var(--z-modal)] transform transition-transform duration-300 ease-in-out ${positionClasses[position].animation} ${className}`}
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-200 flex items-start justify-between">
          <div className="flex-1 pr-8">
            {title && (
              <h2 className="text-xl font-bold text-gray-900">{title}</h2>
            )}
            {subtitle && (
              <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors flex-shrink-0"
            aria-label="Close drawer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto custom-scrollbar h-[calc(100%-80px)]">
          {children}
        </div>
      </div>
    </>
  );
};

export default Drawer;

