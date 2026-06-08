// apps/web/frontend/components/dashboard/ActionableInsight.jsx
import React from 'react';
import { Sparkles } from 'lucide-react';

export default function ActionableInsight({ 
  title = "Good day for focus tasks, but schedule regular breaks.",
  description = "Your cognitive clarity peaks between 10 AM to 12 PM today based on sleep cycles",
  className = ''
}) {
  return (
    <div className={`relative bg-[#c0e7ff] rounded-2xl px-4 py-2 ${className}`}>
      {/* Actionable Insight Badge */}
      <div className="absolute -top-3 right-0 bg-[#feca57] rounded-bl-2xl rounded-tr-2xl px-2 py-1 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-black" />
        <span className="text-sm font-medium text-black">Actionable Insight</span>
      </div>
      
      <div className="backdrop-blur-[9.924px] flex flex-col items-start py-4 rounded-2xl">
        <div className="w-full">
          <p className="text-lg font-bold text-black leading-8 mb-0">
            {title.split(' ').map((word, idx) => {
              // Underline specific keywords
              if (['focus', 'tasks'].includes(word.toLowerCase().replace(/[.,]/g, ''))) {
                return (
                  <span key={idx} className="underline decoration-solid">
                    {word}{' '}
                  </span>
                );
              }
              return word + ' ';
            })}
          </p>
          <p className="text-sm font-normal text-black leading-7">
            {description}
          </p>
        </div>
      </div>
    </div>
  );
}

