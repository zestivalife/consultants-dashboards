import React, { useState } from 'react';

/**
 * Enhanced Line Chart Component with better styling
 */
const LineChart = ({ data = [], height = 200, color = '#64ae00', label = 'Data', showGrid = true }) => {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No data available
      </div>
    );
  }

  const maxValue = Math.max(...data.map(d => d.value));
  const minValue = Math.min(...data.map(d => d.value));
  const range = maxValue - minValue || 1;
  
  // Add 10% padding to the top for better visualization
  const paddedMax = maxValue + (range * 0.1);
  const paddedMin = Math.max(0, minValue - (range * 0.1));
  const paddedRange = paddedMax - paddedMin;

  const normalizeValue = (value) => {
    return ((value - paddedMin) / paddedRange) * 100;
  };

  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 100 - normalizeValue(d.value);
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="relative w-full" style={{ height: `${height}px`, paddingBottom: '20px' }}>
      <svg
        width="100%"
        height="calc(100% - 20px)"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        className="overflow-visible"
      >
        {/* Grid Lines */}
        {showGrid && [20, 40, 60, 80].map((y) => (
          <line
            key={y}
            x1="0"
            y1={y}
            x2="100"
            y2={y}
            stroke="#f3f4f6"
            strokeWidth="0.3"
            vectorEffect="non-scaling-stroke"
          />
        ))}

        {/* Gradient Fill */}
        <defs>
          <linearGradient id={`gradient-${label}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style={{ stopColor: color, stopOpacity: 0.2 }} />
            <stop offset="100%" style={{ stopColor: color, stopOpacity: 0.02 }} />
          </linearGradient>
          
          {/* Shadow for line */}
          <filter id={`shadow-${label}`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceAlpha" stdDeviation="0.5"/>
            <feOffset dx="0" dy="0.5" result="offsetblur"/>
            <feComponentTransfer>
              <feFuncA type="linear" slope="0.3"/>
            </feComponentTransfer>
            <feMerge>
              <feMergeNode/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* Area under line */}
        <polygon
          points={`0,100 ${points} 100,100`}
          fill={`url(#gradient-${label})`}
        />

        {/* Line with shadow */}
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          filter={`url(#shadow-${label})`}
          vectorEffect="non-scaling-stroke"
        />

        {/* Data Points */}
        {data.map((d, i) => {
          const x = (i / (data.length - 1)) * 100;
          const y = 100 - normalizeValue(d.value);
          const isHovered = hoveredIndex === i;
          
          return (
            <g key={i}>
              {/* Hover area (invisible but large for better UX) */}
              <circle
                cx={x}
                cy={y}
                r="3"
                fill="transparent"
                onMouseEnter={() => setHoveredIndex(i)}
                onMouseLeave={() => setHoveredIndex(null)}
                style={{ cursor: 'pointer' }}
                vectorEffect="non-scaling-stroke"
              />
              
              {/* Visible point */}
              <circle
                cx={x}
                cy={y}
                r={isHovered ? "2.5" : "1.5"}
                fill="white"
                stroke={color}
                strokeWidth={isHovered ? "2" : "1.5"}
                className="transition-all duration-200"
                vectorEffect="non-scaling-stroke"
              />
              
              {/* Tooltip on hover */}
              {isHovered && (
                <g>
                  <rect
                    x={x > 50 ? x - 15 : x + 2}
                    y={y - 8}
                    width="13"
                    height="6"
                    fill="rgba(0,0,0,0.8)"
                    rx="1"
                    vectorEffect="non-scaling-stroke"
                  />
                  <text
                    x={x > 50 ? x - 8.5 : x + 8.5}
                    y={y - 4}
                    fill="white"
                    fontSize="4"
                    fontWeight="600"
                    textAnchor="middle"
                  >
                    {d.value}
                  </text>
                </g>
              )}
            </g>
          );
        })}
      </svg>

      {/* X-Axis Labels */}
      <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-gray-500">
        {data.map((d, i) => (
          <span 
            key={i} 
            className={`transition-all duration-200 ${hoveredIndex === i ? 'text-gray-900 font-semibold' : ''}`}
          >
            {d.label}
          </span>
        ))}
      </div>
    </div>
  );
};

export default LineChart;

