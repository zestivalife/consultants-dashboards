import React from 'react';

/**
 * LoadingState - Skeleton loaders matching new design
 * Provides consistent loading states for different content types
 */

export const SkeletonCard = ({ className = '' }) => (
  <div className={`card-default p-6 ${className}`}>
    <div className="animate-pulse">
      <div className="flex items-center justify-between mb-4">
        <div className="w-12 h-12 bg-gray-200 rounded-xl"></div>
        <div className="w-16 h-6 bg-gray-200 rounded-full"></div>
      </div>
      <div className="space-y-3">
        <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/3"></div>
      </div>
    </div>
  </div>
);

export const SkeletonTable = ({ rows = 5 }) => (
  <div className="animate-pulse space-y-3">
    <div className="h-12 bg-gray-200 rounded-lg"></div>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="h-16 bg-gray-100 rounded-lg"></div>
    ))}
  </div>
);

export const SkeletonText = ({ lines = 3, className = '' }) => (
  <div className={`animate-pulse space-y-2 ${className}`}>
    {Array.from({ length: lines }).map((_, i) => (
      <div
        key={i}
        className="h-4 bg-gray-200 rounded"
        style={{ width: `${100 - i * 10}%` }}
      ></div>
    ))}
  </div>
);

export const SkeletonCircle = ({ size = 'base', className = '' }) => {
  const sizeClasses = {
    sm: 'w-8 h-8',
    base: 'w-12 h-12',
    lg: 'w-16 h-16',
    xl: 'w-24 h-24',
  };

  return (
    <div
      className={`${sizeClasses[size]} bg-gray-200 rounded-full animate-pulse ${className}`}
    ></div>
  );
};

export const SkeletonList = ({ items = 5, className = '' }) => (
  <div className={`space-y-4 ${className}`}>
    {Array.from({ length: items }).map((_, i) => (
      <div key={i} className="flex items-center gap-4 animate-pulse">
        <div className="w-12 h-12 bg-gray-200 rounded-lg flex-shrink-0"></div>
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-3 bg-gray-100 rounded w-1/2"></div>
        </div>
      </div>
    ))}
  </div>
);

const LoadingState = ({ type = 'card', ...props }) => {
  switch (type) {
    case 'table':
      return <SkeletonTable {...props} />;
    case 'text':
      return <SkeletonText {...props} />;
    case 'circle':
      return <SkeletonCircle {...props} />;
    case 'list':
      return <SkeletonList {...props} />;
    case 'card':
    default:
      return <SkeletonCard {...props} />;
  }
};

export default LoadingState;

