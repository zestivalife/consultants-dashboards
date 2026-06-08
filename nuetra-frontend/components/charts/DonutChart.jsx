import React from 'react';

/**
 * Donut Chart Component
 * SVG-based donut chart with animations
 */
const DonutChart = ({ 
  data = [], 
  size = 200, 
  thickness = 30,
  showLegend = true,
  centerLabel = '',
  centerValue = ''
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No data available
      </div>
    );
  }

  const total = data.reduce((sum, item) => sum + item.value, 0);
  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;

  let currentAngle = -90; // Start from top

  const slices = data.map((item, index) => {
    const percentage = (item.value / total) * 100;
    const angle = (item.value / total) * 360;
    const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`;
    const rotation = currentAngle;
    
    currentAngle += angle;

    return {
      ...item,
      percentage,
      strokeDasharray,
      rotation
    };
  });

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Chart */}
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Background Circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#f3f4f6"
            strokeWidth={thickness}
          />

          {/* Data Slices */}
          {slices.map((slice, index) => (
            <circle
              key={index}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={slice.color}
              strokeWidth={thickness}
              strokeDasharray={slice.strokeDasharray}
              strokeDashoffset="0"
              transform={`rotate(${slice.rotation} ${size / 2} ${size / 2})`}
              strokeLinecap="round"
              className="transition-all duration-1000"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <title>{`${slice.label}: ${slice.value} (${slice.percentage.toFixed(1)}%)`}</title>
            </circle>
          ))}
        </svg>

        {/* Center Label */}
        {(centerLabel || centerValue) && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            {centerValue && (
              <p className="text-3xl font-bold text-gray-900">{centerValue}</p>
            )}
            {centerLabel && (
              <p className="text-sm text-gray-500">{centerLabel}</p>
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      {showLegend && (
        <div className="grid grid-cols-2 gap-3 w-full">
          {slices.map((slice, index) => (
            <div key={index} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: slice.color }}
              ></div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-600 truncate">{slice.label}</p>
                <p className="text-sm font-semibold text-gray-900">
                  {slice.percentage.toFixed(1)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DonutChart;

