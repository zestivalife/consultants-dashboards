// apps/web/frontend/components/dashboard/CircularProgress.jsx
import React from 'react';

export default function CircularProgress({ 
  current = 0, 
  total = 12, 
  size = 180,
  strokeWidth = 12,
  className = '' 
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = total > 0 ? (current / total) : 0;
  const strokeDashoffset = circumference * (1 - progress);
  
  // Center position
  const center = size / 2;

  return (
    <div className={`relative ${className}`} style={{ width: size, height: size }}>
      {/* SVG Progress Ring */}
      <svg 
        width={size} 
        height={size} 
        className="transform -rotate-90"
      >
        {/* Gradient definitions - matching Figma colors */}
        <defs>
          {/* Multi-stop gradient for progress ring */}
          <linearGradient id="focusModeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#8b5cf6" />      {/* Purple */}
            <stop offset="25%" stopColor="#6366f1" />     {/* Indigo */}
            <stop offset="50%" stopColor="#3b82f6" />     {/* Blue */}
            <stop offset="75%" stopColor="#8b5cf6" />     {/* Purple */}
            <stop offset="100%" stopColor="#ec4899" />    {/* Pink */}
          </linearGradient>
        </defs>
        
        {/* Background circle (track) - dark with slight visibility */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="rgba(71, 85, 105, 0.3)"
          strokeWidth={strokeWidth}
        />
        
        {/* Progress circle with gradient */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="url(#focusModeGradient)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-500 ease-out"
        />
      </svg>
      
      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-white/50 text-[10px] font-medium mb-0.5 tracking-wide">Total Questions</span>
        <span className="text-white text-2xl font-bold tracking-tight">
          {String(current).padStart(2, '0')}/{total}
        </span>
        <span className="text-white/50 text-[10px] font-medium mt-0.5 tracking-wide">Completed</span>
      </div>
    </div>
  );
}
