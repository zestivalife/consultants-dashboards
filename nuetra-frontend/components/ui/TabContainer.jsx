import React, { useState } from 'react';

/**
 * TabContainer - Modern tab system with smooth transitions
 * Organizes content into switchable tabs
 */
const TabContainer = ({
  tabs,
  defaultTab = 0,
  onChange,
  className = '',
  variant = 'default', // 'default', 'pills', 'underline'
}) => {
  const [activeTab, setActiveTab] = useState(defaultTab);

  const handleTabChange = (index) => {
    setActiveTab(index);
    if (onChange) onChange(index);
  };

  const variantStyles = {
    default: {
      container: 'border-b border-gray-200',
      tab: 'px-6 py-3 text-sm font-medium transition-colors border-b-2',
      active: 'border-[#64ae00] text-[#64ae00]',
      inactive: 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300',
    },
    pills: {
      container: 'bg-gray-100 rounded-xl p-1',
      tab: 'px-6 py-2 text-sm font-medium rounded-lg transition-all',
      active: 'bg-white text-[#64ae00] shadow-sm',
      inactive: 'text-gray-600 hover:text-gray-900',
    },
    underline: {
      container: 'space-x-8',
      tab: 'pb-3 text-sm font-medium transition-colors relative',
      active: 'text-[#64ae00] after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-[#64ae00]',
      inactive: 'text-gray-600 hover:text-gray-900',
    },
  };

  const styles = variantStyles[variant];

  return (
    <div className={className}>
      {/* Tab Headers */}
      <div className={`flex ${styles.container}`}>
        {tabs.map((tab, index) => (
          <button
            key={index}
            onClick={() => handleTabChange(index)}
            className={`${styles.tab} ${
              activeTab === index ? styles.active : styles.inactive
            }`}
            role="tab"
            aria-selected={activeTab === index}
          >
            {tab.icon && (
              <span className="inline-flex items-center gap-2">
                {tab.icon}
                {tab.label}
              </span>
            )}
            {!tab.icon && tab.label}
            {tab.badge && (
              <span className="ml-2 px-2 py-0.5 text-xs font-semibold rounded-full bg-gray-200 text-gray-700">
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {tabs.map((tab, index) => (
          <div
            key={index}
            className={`transition-all duration-300 ${
              activeTab === index
                ? 'opacity-100 block animate-fadeIn'
                : 'opacity-0 hidden'
            }`}
            role="tabpanel"
            hidden={activeTab !== index}
          >
            {tab.content}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TabContainer;

