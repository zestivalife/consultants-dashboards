// apps/web/frontend/components/dashboard/NourishmentChart.jsx
import React, { useState } from 'react';
import { Sparkles, Moon, Zap, Heart, ArrowUp } from 'lucide-react';

const categoryTabs = [
  { 
    key: 'recovery', 
    label: 'Recovery', 
    icon: Sparkles,
    gradient: 'bg-gradient-to-b from-[rgba(255,222,54,0.2)] to-[rgba(231,135,1,0.2)]'
  },
  { 
    key: 'sleep', 
    label: 'Sleep', 
    icon: Moon,
    gradient: 'bg-gradient-to-b from-[rgba(132,36,32,0.2)] to-[rgba(217,37,28,0.2)]'
  },
  { 
    key: 'nourishment', 
    label: 'Nourishment', 
    icon: Zap,
    gradient: 'bg-gradient-to-b from-[rgba(20,67,33,0.2)] to-[rgba(25,170,65,0.2)]'
  },
  { 
    key: 'hrv', 
    label: 'HRV', 
    icon: Heart,
    gradient: 'bg-gradient-to-b from-[rgba(39,77,141,0.2)] to-[rgba(35,122,252,0.2)]'
  },
];

const timePeriods = [
  { key: '7d', label: '7 Days' },
  { key: '30d', label: '30 Days' },
  { key: '90d', label: '90 Days' },
];

const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

// Sample chart data - heights as percentages
const chartData = [
  { day: 'Mon', value: 15 },
  { day: 'Tue', value: 21 },
  { day: 'Wed', value: 26 },
  { day: 'Thu', value: 35 },
  { day: 'Wed', value: 32 },
  { day: 'Sat', value: 10 },
  { day: 'Sun', value: 10 },
];

export default function NourishmentChart({ 
  title = "Nourishment",
  description = "Based on your recovery signals, you're well-positioned for steady progress today. Avoid over-exertion in the late afternoon.",
  currentValue = 74,
  data = chartData,
  className = ''
}) {
  const [activeCategory, setActiveCategory] = useState('nourishment');
  const [activePeriod, setActivePeriod] = useState('7d');

  return (
    <div className={`flex flex-col items-start ${className}`}>
      {/* Category Tabs */}
      <div className="flex flex-wrap gap-2 items-center w-[482px]">
        {categoryTabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeCategory === tab.key;
          
          return (
            <button
              key={tab.key}
              onClick={() => setActiveCategory(tab.key)}
              className={`
                flex gap-0.5 items-center p-2 rounded-t-lg w-20 transition-all
                ${tab.gradient}
                ${isActive ? 'opacity-100' : 'opacity-60 hover:opacity-80'}
              `}
            >
              <Icon className="h-3 w-3 text-black" />
              <span className="text-[10px] font-medium text-black">{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Chart Container */}
      <div className="w-full border border-[#e7e7e9] rounded-bl-2xl rounded-br-2xl rounded-tr-2xl overflow-hidden relative bg-white shadow-[inset_0px_4px_4px_-1px_rgba(12,12,13,0.05)]">
        {/* Header */}
        <div className="absolute top-3 left-3 right-3 flex justify-between items-start z-10">
          <div className="flex flex-col gap-1 max-w-[236px]">
            <h3 className="text-base font-bold text-black leading-tight">{title}</h3>
            <p className="text-sm font-normal text-black leading-[21px]">{description}</p>
          </div>

          {/* Time Period Selector */}
          <div className="flex items-center bg-[#f6f6f6] rounded-[20px]">
            {timePeriods.map((period) => {
              const isActive = activePeriod === period.key;
              
              return (
                <button
                  key={period.key}
                  onClick={() => setActivePeriod(period.key)}
                  className={`
                    px-4 py-2.5 rounded-[20px] text-[10px] text-center transition-all
                    ${isActive 
                      ? 'bg-black text-white' 
                      : 'text-black hover:bg-gray-200'
                    }
                  `}
                >
                  {period.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Current Value Display */}
        <div className="absolute top-[127px] left-[319px] flex gap-2 items-center z-10">
          <div className="flex flex-col items-start">
            <span className="text-lg font-bold text-black leading-5">{currentValue}%</span>
            <span className="text-[10px] font-normal text-black capitalize leading-[15px]">Current</span>
          </div>
          <ArrowUp className="h-4 w-3 text-[#19aa41]" />
        </div>

        {/* Chart Area */}
        <div className="h-[288px] pt-[140px] relative">
          {/* Green Gradient Background for chart area */}
          <div className="absolute bottom-0 left-0 right-0 h-[148px]">
            <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 482 148">
              <defs>
                <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#19aa41" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#19aa41" stopOpacity="1" />
                </linearGradient>
              </defs>
              {/* Curved area fill */}
              <path
                d="M0,148 L0,100 Q60,80 120,70 T240,50 T360,60 T482,40 L482,148 Z"
                fill="url(#chartGradient)"
              />
              {/* Curve line */}
              <path
                d="M0,100 Q60,80 120,70 T240,50 T360,60 T482,40"
                fill="none"
                stroke="#19aa41"
                strokeWidth="2"
              />
              {/* Current point indicator */}
              <circle cx="320" cy="55" r="6" fill="white" stroke="#19aa41" strokeWidth="2" />
            </svg>
          </div>

          {/* Bar Chart */}
          <div className="absolute bottom-[20px] left-[8.65%] right-[5.35%] flex justify-between items-end h-[100px]">
            {data.map((item, index) => (
              <div key={index} className="flex flex-col items-center gap-1">
                <div 
                  className="w-2 bg-white rounded-t-full transition-all"
                  style={{ height: `${Math.max(item.value, 7)}px` }}
                />
              </div>
            ))}
          </div>

          {/* Day Labels */}
          <div className="absolute bottom-[4px] left-0 right-0 flex justify-around px-4">
            {weekDays.map((day, index) => (
              <span key={index} className="text-xs text-white text-center w-8">
                {day}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

