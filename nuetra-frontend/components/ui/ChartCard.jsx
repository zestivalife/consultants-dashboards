import React from 'react';
import { TrendingUp, TrendingDown, MoreVertical } from 'lucide-react';

/**
 * ChartCard - Wrapper for charts with consistent styling
 * Provides a consistent container for data visualizations
 */
const ChartCard = ({
  title,
  subtitle,
  value,
  trend,
  trendValue,
  children,
  actions,
  className = '',
  headerClassName = '',
}) => {
  const isPositiveTrend = trend === 'up' || (trendValue && parseFloat(trendValue) > 0);
  const isNegativeTrend = trend === 'down' || (trendValue && parseFloat(trendValue) < 0);

  return (
    <div className={`card-elevated p-6 ${className}`}>
      {/* Header */}
      <div className={`flex items-start justify-between mb-6 ${headerClassName}`}>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
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
          {subtitle && (
            <p className="text-sm text-gray-500">{subtitle}</p>
          )}
          {value && (
            <p className="text-2xl font-bold text-gray-900 mt-2">{value}</p>
          )}
        </div>
        {actions && (
          <div className="relative">
            <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <MoreVertical className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        )}
      </div>

      {/* Chart Content */}
      <div className="relative">
        {children}
      </div>
    </div>
  );
};

export default ChartCard;

