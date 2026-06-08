import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { COLORS } from '../../utils/design-constants';

/**
 * ModernStatCard - Enhanced stat card with glassmorphism effects
 * Displays key metrics with icon, value, trend, and optional actions
 */
const ModernStatCard = ({
  icon: Icon,
  title,
  value,
  subtitle,
  trend,
  trendValue,
  color = 'from-blue-500 to-blue-600',
  onClick,
  loading = false,
  className = '',
}) => {
  const isPositiveTrend = trend === 'up' || (trendValue && parseFloat(trendValue) > 0);
  const isNegativeTrend = trend === 'down' || (trendValue && parseFloat(trendValue) < 0);

  if (loading) {
    return (
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
  }

  return (
    <div
      className={`stat-card group cursor-pointer ${className}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`stat-card-icon bg-gradient-to-br ${color}`}>
          {Icon && <Icon className="w-6 h-6 text-white" />}
        </div>
        {(trend || trendValue) && (
          <div
            className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold ${
              isPositiveTrend
                ? 'bg-green-50 text-green-700'
                : isNegativeTrend
                ? 'bg-red-50 text-red-700'
                : 'bg-gray-50 text-gray-700'
            }`}
          >
            {isPositiveTrend && <TrendingUp className="w-3 h-3" />}
            {isNegativeTrend && <TrendingDown className="w-3 h-3" />}
            {trendValue || ''}
          </div>
        )}
      </div>

      <div className="space-y-1">
        <h3 className="text-sm font-medium text-gray-600 uppercase tracking-wide">
          {title}
        </h3>
        <p className="text-3xl font-bold text-gray-900 transition-all group-hover:text-[#64ae00]">
          {value}
        </p>
        {subtitle && (
          <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
        )}
      </div>

      {onClick && (
        <div className="mt-4 pt-4 border-t border-gray-100 opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="text-xs font-medium text-[#64ae00] flex items-center gap-1">
            View details
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </span>
        </div>
      )}
    </div>
  );
};

export default ModernStatCard;

