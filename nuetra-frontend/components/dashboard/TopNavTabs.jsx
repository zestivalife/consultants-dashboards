// apps/web/frontend/components/dashboard/TopNavTabs.jsx
import React from 'react';

const defaultTabs = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'focus-mode', label: 'Focus Mode' },
  { key: 'wellness', label: 'Wellness' },
  { key: 'analytics', label: 'Analytics' },
  { key: 'sessions', label: 'Session' },
  { key: 'tools', label: 'Tools' },
];

export default function TopNavTabs({ 
  tabs = defaultTabs, 
  activeTab = 'dashboard', 
  onTabChange,
  className = '' 
}) {
  return (
    <div className={`flex gap-4 items-start ${className}`}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.key;
        
        return (
          <button
            key={tab.key}
            onClick={() => onTabChange?.(tab.key)}
            className={`
              px-10 py-3 rounded-[28px] text-sm font-normal transition-all duration-200
              ${isActive 
                ? 'bg-[#237afc] text-white font-semibold shadow-md' 
                : 'bg-white text-black hover:bg-gray-50 mix-blend-plus-lighter'
              }
            `}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

