import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

/**
 * CollapsiblePanel - Accordion-style panels for dense information
 * Allows sections to be expanded/collapsed to manage screen space
 */
const CollapsiblePanel = ({
  title,
  subtitle,
  children,
  defaultOpen = false,
  icon: Icon,
  badge,
  className = '',
  headerClassName = '',
  contentClassName = '',
  onToggle,
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const handleToggle = () => {
    const newState = !isOpen;
    setIsOpen(newState);
    if (onToggle) onToggle(newState);
  };

  return (
    <div className={`card-default overflow-hidden ${className}`}>
      <button
        onClick={handleToggle}
        className={`w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors ${headerClassName}`}
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-3">
          {Icon && (
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#64ae00] to-[#7dc41f] flex items-center justify-center flex-shrink-0">
              <Icon className="w-5 h-5 text-white" />
            </div>
          )}
          <div className="text-left">
            <h3 className="text-base font-semibold text-gray-900 flex items-center gap-2">
              {title}
              {badge && (
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-[#64ae00] text-white">
                  {badge}
                </span>
              )}
            </h3>
            {subtitle && (
              <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isOpen ? (
            <ChevronUp className="w-5 h-5 text-gray-400 transition-transform" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400 transition-transform" />
          )}
        </div>
      </button>

      <div
        className={`transition-all duration-300 ease-in-out ${
          isOpen ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
        } overflow-hidden`}
      >
        <div className={`px-6 py-4 border-t border-gray-100 ${contentClassName}`}>
          {children}
        </div>
      </div>
    </div>
  );
};

export default CollapsiblePanel;

