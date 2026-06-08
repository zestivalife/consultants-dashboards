import React, { useState } from 'react';
import { AlertCircle, Loader, Sun } from 'lucide-react';
import { teamMemberAPI } from '../lib/api';

const SunlightForm = ({ onComplete, isLoading, setIsLoading, submitText = "Save Sunlight Log" }) => {
  const [minutes, setMinutes] = useState('');
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    if (!minutes || isNaN(minutes) || parseInt(minutes) < 0 || parseInt(minutes) > 1440) {
      newErrors.minutes = 'Please enter a valid duration (0-1440 minutes)';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setErrors({});

    try {
      const val = parseInt(minutes);
      await teamMemberAPI.logMetric({
        type: 'SUNLIGHT',
        value: val,
        unit: 'min'
      });
      
      onComplete({ minutes: val });
    } catch (error) {
      console.error('Error saving sunlight metric:', error);
      setErrors({ submit: error.message || 'Failed to save sunlight log.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <div className="w-10 h-10 rounded-full bg-yellow-100 flex items-center justify-center">
            <Sun className="h-6 w-6 text-yellow-500" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 ml-3">Sunlight Exposure Log</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Getting enough sunlight helps regulate your circadian rhythm and boosts Vitamin D levels.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            How many minutes of direct sunlight did you get today?
          </label>
          <input
            type="number"
            value={minutes}
            onChange={(e) => setMinutes(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-yellow-500 focus:border-yellow-500"
            placeholder="e.g. 20"
          />
          {errors.minutes && (
            <p className="text-red-500 text-xs mt-2">{errors.minutes}</p>
          )}
        </div>

        {errors.submit && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <p className="text-red-700">{errors.submit}</p>
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isLoading || !minutes}
            className="bg-yellow-600 text-white px-6 py-2 rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center transition-colors"
          >
            {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
            {submitText}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SunlightForm;
