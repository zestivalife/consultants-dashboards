import React from 'react';
import { Plus, Apple } from 'lucide-react';

const StartDietPlanButton = ({ onClick, className = '' }) => {
  return (
    <button
      onClick={onClick}
      className={`
        inline-flex items-center px-4 py-2 
        bg-gradient-to-r from-green-500 to-green-600 
        hover:from-green-600 hover:to-green-700 
        text-white font-semibold text-sm rounded-lg 
        shadow-md hover:shadow-xl 
        transition-all duration-200 
        focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2
        transform hover:scale-105
        ${className}
      `}
    >
      <Apple className="h-4 w-4 mr-2" />
      Get Your Personalized Diet Plan
    </button>
  );
};

export default StartDietPlanButton;