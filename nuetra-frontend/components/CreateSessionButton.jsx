import React from 'react';
import { Plus, Calendar, Users } from 'lucide-react';

const CreateSessionButton = ({ onClick, className = '' }) => {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-lg hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 shadow-sm hover:shadow-md ${className}`}
    >
      <Plus className="w-4 h-4 mr-2" />
      Create Wellness Session
    </button>
  );
};

export default CreateSessionButton;