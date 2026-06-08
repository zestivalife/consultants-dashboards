import React from 'react';

/**
 * ModalContent - Scrollable content area
 * Provides the main content area with proper scrolling
 */
const ModalContent = ({
  children,
  className = '',
  padding = true,
}) => {
  return (
    <div
      className={`overflow-y-auto custom-scrollbar max-h-[70vh] ${
        padding ? 'px-6 py-4' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
};

export default ModalContent;

