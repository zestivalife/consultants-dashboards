import React, { useState } from 'react';
import { Filter, X, ChevronDown } from 'lucide-react';

/**
 * FilterBar - Advanced filtering component
 * Provides dropdown filters with multi-select capability
 */
const FilterBar = ({
  filters = [],
  onFilterChange,
  showClearAll = true,
  className = '',
}) => {
  const [activeFilters, setActiveFilters] = useState({});
  const [openDropdown, setOpenDropdown] = useState(null);

  const handleFilterSelect = (filterKey, value) => {
    const updated = { ...activeFilters };
    
    if (!updated[filterKey]) {
      updated[filterKey] = [];
    }
    
    const index = updated[filterKey].indexOf(value);
    if (index > -1) {
      updated[filterKey].splice(index, 1);
      if (updated[filterKey].length === 0) {
        delete updated[filterKey];
      }
    } else {
      updated[filterKey].push(value);
    }
    
    setActiveFilters(updated);
    if (onFilterChange) onFilterChange(updated);
  };

  const handleClearAll = () => {
    setActiveFilters({});
    if (onFilterChange) onFilterChange({});
  };

  const getActiveCount = () => {
    return Object.values(activeFilters).reduce((sum, arr) => sum + arr.length, 0);
  };

  return (
    <div className={`flex flex-wrap items-center gap-3 ${className}`}>
      <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
        <Filter className="w-4 h-4" />
        <span>Filters</span>
        {getActiveCount() > 0 && (
          <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-[#64ae00] text-white">
            {getActiveCount()}
          </span>
        )}
      </div>

      {filters.map((filter) => (
        <div key={filter.key} className="relative">
          <button
            onClick={() =>
              setOpenDropdown(openDropdown === filter.key ? null : filter.key)
            }
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all ${
              activeFilters[filter.key]?.length > 0
                ? 'bg-[#64ae00] text-white border-[#64ae00]'
                : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
            }`}
          >
            <span className="text-sm font-medium">{filter.label}</span>
            {activeFilters[filter.key]?.length > 0 && (
              <span className="px-1.5 py-0.5 text-xs font-semibold rounded bg-white text-[#64ae00]">
                {activeFilters[filter.key].length}
              </span>
            )}
            <ChevronDown className="w-4 h-4" />
          </button>

          {openDropdown === filter.key && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setOpenDropdown(null)}
              ></div>
              <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-xl shadow-xl border border-gray-200 z-20 max-h-80 overflow-y-auto custom-scrollbar">
                <div className="p-2">
                  {filter.options.map((option) => (
                    <label
                      key={option.value}
                      className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={
                          activeFilters[filter.key]?.includes(option.value) ||
                          false
                        }
                        onChange={() =>
                          handleFilterSelect(filter.key, option.value)
                        }
                        className="w-4 h-4 text-[#64ae00] border-gray-300 rounded focus:ring-[#64ae00] cursor-pointer"
                      />
                      <span className="text-sm text-gray-700 flex-1">
                        {option.label}
                      </span>
                      {option.count !== undefined && (
                        <span className="text-xs text-gray-500">
                          {option.count}
                        </span>
                      )}
                    </label>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      ))}

      {showClearAll && getActiveCount() > 0 && (
        <button
          onClick={handleClearAll}
          className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
        >
          <X className="w-4 h-4" />
          <span>Clear all</span>
        </button>
      )}
    </div>
  );
};

export default FilterBar;

