import React, { useEffect } from 'react';
import { X } from 'lucide-react';

/**
 * BottomSheet - Mobile-friendly bottom modal
 * Slides up from the bottom of the screen
 */
const BottomSheet = ({
  isOpen,
  onClose,
  children,
  title,
  subtitle,
  height = 'auto', // 'auto', 'half', 'full'
  closeOnBackdrop = true,
  closeOnEsc = true,
  showHandle = true,
  className = '',
}) => {
  const heightClasses = {
    auto: 'max-h-[80vh]',
    half: 'h-[50vh]',
    full: 'h-[90vh]',
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

      {/* Bottom Sheet */}
      <div
        className={`fixed bottom-0 left-0 right-0 bg-white rounded-t-3xl shadow-2xl z-[var(--z-modal)] transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-y-0' : 'translate-y-full'
        } ${heightClasses[height]} ${className}`}
        role="dialog"
        aria-modal="true"
      >
        {/* Handle */}
        {showHandle && (
          <div className="flex justify-center pt-3 pb-2">
            <div className="w-12 h-1.5 bg-gray-300 rounded-full"></div>
          </div>
        )}

        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-start justify-between">
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
            aria-label="Close bottom sheet"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto custom-scrollbar px-6 py-4" style={{ height: 'calc(100% - 100px)' }}>
          {children}
        </div>
      </div>
    </>
  );
};

export default BottomSheet;

