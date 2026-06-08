import React from 'react';

/**
 * ModalFooter - Action buttons area
 * Provides standardized modal footer with action buttons
 */
const ModalFooter = ({
  primaryAction,
  primaryLabel = 'Confirm',
  primaryLoading = false,
  primaryDisabled = false,
  secondaryAction,
  secondaryLabel = 'Cancel',
  showSecondary = true,
  align = 'right', // 'left', 'center', 'right', 'between'
  className = '',
}) => {
  const alignClasses = {
    left: 'justify-start',
    center: 'justify-center',
    right: 'justify-end',
    between: 'justify-between',
  };

  return (
    <div className={`px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-2xl ${className}`}>
      <div className={`flex items-center gap-3 ${alignClasses[align]}`}>
        {showSecondary && (
          <button
            onClick={secondaryAction}
            className="btn-secondary"
            type="button"
          >
            {secondaryLabel}
          </button>
        )}
        <button
          onClick={primaryAction}
          disabled={primaryDisabled || primaryLoading}
          className="btn-primary"
          type="button"
        >
          {primaryLoading ? (
            <>
              <svg
                className="animate-spin h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              <span>Processing...</span>
            </>
          ) : (
            primaryLabel
          )}
        </button>
      </div>
    </div>
  );
};

export default ModalFooter;

