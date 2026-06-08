import React from 'react';

/**
 * Simple Bar Chart Component
 * Pure CSS implementation with animations
 */
const BarChart = ({ 
  data = [], 
  height = 200, 
  color = '#64ae00',
  horizontal = false,
  showValues = true 
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No data available
      </div>
    );
  }

  const maxValue = Math.max(...data.map(d => d.value));

  if (horizontal) {
    return (
      <div className="space-y-3" style={{ height: `${height}px` }}>
        {data.map((item, index) => (
          <div key={index} className="flex items-center gap-3">
            <span className="text-sm text-gray-600 min-w-[80px] text-right">
              {item.label}
            </span>
            <div className="flex-1 bg-gray-200 rounded-full h-8 relative overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-1000 ease-out flex items-center justify-end px-3"
                style={{
                  width: `${(item.value / maxValue) * 100}%`,
                  backgroundColor: item.color || color,
                  animationDelay: `${index * 100}ms`
                }}
              >
                {showValues && (
                  <span className="text-xs font-semibold text-white">
                    {item.value}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="flex items-end justify-between gap-2" style={{ height: `${height}px` }}>
      {data.map((item, index) => (
        <div key={index} className="flex-1 flex flex-col items-center gap-2">
          <div className="w-full bg-gray-200 rounded-t-lg relative overflow-hidden flex-1 flex flex-col justify-end">
            <div
              className="w-full rounded-t-lg transition-all duration-1000 ease-out relative group"
              style={{
                height: `${(item.value / maxValue) * 100}%`,
                backgroundColor: item.color || color,
                animationDelay: `${index * 100}ms`
              }}
            >
              {showValues && (
                <span className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs font-semibold text-gray-700 opacity-0 group-hover:opacity-100 transition-opacity">
                  {item.value}
                </span>
              )}
            </div>
          </div>
          <span className="text-xs text-gray-600 text-center truncate w-full">
            {item.label}
          </span>
        </div>
      ))}
    </div>
  );
};

export default BarChart;

