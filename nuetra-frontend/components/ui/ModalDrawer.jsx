import React from 'react';
import BaseModal from '../Modal/BaseModal';
import Drawer from '../Modal/Drawer';
import BottomSheet from '../Modal/BottomSheet';
import ModalHeader from '../Modal/ModalHeader';
import ModalFooter from '../Modal/ModalFooter';
import ModalContent from '../Modal/ModalContent';

/**
 * ModalDrawer - Unified modal/drawer system with smooth animations
 * Adaptive component that renders as modal, drawer, or bottom sheet
 */
const ModalDrawer = ({
  isOpen,
  onClose,
  variant = 'modal', // 'modal', 'drawer', 'bottom-sheet'
  size = 'md',
  title,
  subtitle,
  icon,
  children,
  primaryAction,
  primaryLabel,
  primaryLoading,
  primaryDisabled,
  secondaryAction,
  secondaryLabel,
  showFooter = true,
  showSecondary = true,
  closeOnBackdrop = true,
  closeOnEsc = true,
  className = '',
  ...props
}) => {
  // Modal variant
  if (variant === 'modal') {
    return (
      <BaseModal
        isOpen={isOpen}
        onClose={onClose}
        size={size}
        closeOnBackdrop={closeOnBackdrop}
        closeOnEsc={closeOnEsc}
        className={className}
      >
        {(title || subtitle || icon) && (
          <ModalHeader title={title} subtitle={subtitle} icon={icon} />
        )}
        <ModalContent>{children}</ModalContent>
        {showFooter && (
          <ModalFooter
            primaryAction={primaryAction}
            primaryLabel={primaryLabel}
            primaryLoading={primaryLoading}
            primaryDisabled={primaryDisabled}
            secondaryAction={secondaryAction || onClose}
            secondaryLabel={secondaryLabel}
            showSecondary={showSecondary}
          />
        )}
      </BaseModal>
    );
  }

  // Drawer variant
  if (variant === 'drawer') {
    return (
      <Drawer
        isOpen={isOpen}
        onClose={onClose}
        title={title}
        subtitle={subtitle}
        size={size}
        closeOnBackdrop={closeOnBackdrop}
        closeOnEsc={closeOnEsc}
        className={className}
        {...props}
      >
        <div className="p-6">{children}</div>
        {showFooter && (
          <ModalFooter
            primaryAction={primaryAction}
            primaryLabel={primaryLabel}
            primaryLoading={primaryLoading}
            primaryDisabled={primaryDisabled}
            secondaryAction={secondaryAction || onClose}
            secondaryLabel={secondaryLabel}
            showSecondary={showSecondary}
          />
        )}
      </Drawer>
    );
  }

  // Bottom Sheet variant (mobile-friendly)
  if (variant === 'bottom-sheet') {
    return (
      <BottomSheet
        isOpen={isOpen}
        onClose={onClose}
        title={title}
        subtitle={subtitle}
        closeOnBackdrop={closeOnBackdrop}
        closeOnEsc={closeOnEsc}
        className={className}
        {...props}
      >
        {children}
        {showFooter && (
          <ModalFooter
            primaryAction={primaryAction}
            primaryLabel={primaryLabel}
            primaryLoading={primaryLoading}
            primaryDisabled={primaryDisabled}
            secondaryAction={secondaryAction || onClose}
            secondaryLabel={secondaryLabel}
            showSecondary={showSecondary}
          />
        )}
      </BottomSheet>
    );
  }

  return null;
};

export default ModalDrawer;

