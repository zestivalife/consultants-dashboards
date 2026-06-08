// apps/web/frontend/components/dashboard/HealthInsightCard.jsx
import React from 'react';
import { Zap, Heart, Leaf, RefreshCw, ArrowUp, ArrowDown, ArrowRight } from 'lucide-react';

const themeConfig = {
  yellow: {
    border: 'border-[#ffe2a0]',
    iconBg: 'bg-[#ffe2a0]',
    iconColor: 'text-[#e78701]',
    trendUp: 'text-[#19aa41]',
    trendDown: 'text-[#d9251c]',
    trendNeutral: 'text-[#e78701]',
  },
  pink: {
    border: 'border-[#ffb5cc]',
    iconBg: 'bg-[#ffb5cc]',
    iconColor: 'text-[#ff3c77]',
    trendUp: 'text-[#19aa41]',
    trendDown: 'text-[#d9251c]',
    trendNeutral: 'text-[#e78701]',
  },
  green: {
    border: 'border-[#c5f3d5]',
    iconBg: 'bg-[#c5f3d5]',
    iconColor: 'text-[#19aa41]',
    trendUp: 'text-[#19aa41]',
    trendDown: 'text-[#d9251c]',
    trendNeutral: 'text-[#e78701]',
  },
  blue: {
    border: 'border-[#c9e1ff]',
    iconBg: 'bg-[#c9e1ff]',
    iconColor: 'text-[#729fdc]',
    trendUp: 'text-[#19aa41]',
    trendDown: 'text-[#d9251c]',
    trendNeutral: 'text-[#e78701]',
  },
};

const iconMap = {
  energy: Zap,
  body: Heart,
  nourishment: Leaf,
  recovery: RefreshCw,
};

export default function HealthInsightCard({ 
  value = 82,
  title = "Energy Balance",
  subtitle = "Strong Today",
  theme = 'yellow',
  icon = 'energy',
  trend = 'up', // 'up', 'down', 'neutral'
  onClick,
  className = ''
}) {
  const colors = themeConfig[theme] || themeConfig.yellow;
  const Icon = iconMap[icon] || Zap;
  
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <ArrowUp className={`h-4 w-4 ${colors.trendUp}`} />;
      case 'down':
        return <ArrowDown className={`h-4 w-4 ${colors.trendDown}`} />;
      default:
        return <ArrowRight className={`h-4 w-4 ${colors.trendNeutral}`} />;
    }
  };

  return (
    <div 
      className={`
        relative bg-white border-[0.5px] ${colors.border} rounded-2xl p-3 
        shadow-[0px_4px_4px_0px_rgba(0,0,0,0.08)] 
        hover:shadow-[0px_6px_8px_0px_rgba(0,0,0,0.12)] 
        transition-shadow cursor-pointer
        ${className}
      `}
      onClick={onClick}
    >
      {/* Icon Badge */}
      <div className={`absolute -top-0 right-0 w-[42px] h-[42px] ${colors.iconBg} rounded-bl-2xl rounded-tr-2xl flex items-center justify-center overflow-hidden`}>
        <Icon className={`h-6 w-6 ${colors.iconColor}`} />
      </div>

      {/* Content */}
      <div className="flex flex-col gap-1">
        {/* Value */}
        <span className="text-lg font-bold text-black tracking-[-0.45px]">
          {value !== null && value !== undefined ? `${value}%` : "No data found"}
        </span>
        
        {/* Title and Status */}
        <div className="flex flex-col gap-2">
          <h4 className="text-sm font-semibold text-black h-[17px]">{title}</h4>
          
          <div className="flex gap-2 items-center">
            <span className="flex-1 text-xs font-medium text-black opacity-40 tracking-[-0.3px]">
              {subtitle}
            </span>
            <div className="w-6 h-6 flex items-center justify-center">
              {getTrendIcon()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

