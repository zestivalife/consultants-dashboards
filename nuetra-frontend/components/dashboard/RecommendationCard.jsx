// apps/web/frontend/components/dashboard/RecommendationCard.jsx
import React from 'react';
import { Timer, Droplet, Wind, Move, ArrowRight } from 'lucide-react';

const themeConfig = {
  yellow: {
    bg: 'bg-[#ffefca]',
    iconBg: 'bg-[#ffe2a0]',
    iconColor: 'text-[#e78701]',
  },
  pink: {
    bg: 'bg-[#f5dee5]',
    iconBg: 'bg-[#ffb5cc]',
    iconColor: 'text-[#ff3c77]',
  },
  green: {
    bg: 'bg-[#e2ffec]',
    iconBg: 'bg-[#c5f3d5]',
    iconColor: 'text-[#19aa41]',
  },
  blue: {
    bg: 'bg-[#e2efff]',
    iconBg: 'bg-[#c9e1ff]',
    iconColor: 'text-[#729fdc]',
  },
};

const iconMap = {
  focus: Timer,
  hydration: Droplet,
  breathing: Wind,
  movement: Move,
};

export default function RecommendationCard({ 
  duration = "15 min",
  title = "Focus Mode",
  description = "Deep work session with binaural beats.",
  theme = 'yellow',
  icon = 'focus',
  onClick,
  className = ''
}) {
  const colors = themeConfig[theme] || themeConfig.yellow;
  const Icon = iconMap[icon] || Timer;

  return (
    <div 
      className={`
        relative ${colors.bg} rounded-2xl px-2 py-3 min-w-[160px]
        hover:shadow-[0px_4px_8px_0px_rgba(0,0,0,0.1)] 
        transition-shadow cursor-pointer
        ${className}
      `}
      onClick={onClick}
    >
      {/* Icon Badge */}
      <div className={`absolute top-0 right-0 w-[42px] h-[42px] ${colors.iconBg} rounded-2xl flex items-center justify-center overflow-hidden`}>
        <Icon className={`h-6 w-6 ${colors.iconColor}`} />
      </div>

      {/* Content */}
      <div className="flex flex-col gap-1">
        {/* Duration */}
        <span className="text-lg font-bold text-black tracking-[-0.45px]">{duration}</span>
        
        {/* Title and Description */}
        <div className="flex flex-col gap-2">
          <h4 className="text-sm font-semibold text-black h-[17px]">{title}</h4>
          
          <div className="flex gap-2 items-start">
            <span className="flex-1 text-xs font-medium text-black opacity-40 tracking-[-0.3px] leading-normal">
              {description}
            </span>
            <div className="w-6 h-6 flex items-center justify-center shrink-0">
              <ArrowRight className="h-4 w-4 text-black" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

