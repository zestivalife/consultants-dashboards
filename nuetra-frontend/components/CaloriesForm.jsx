import React, { useState } from 'react';
import { AlertCircle, Loader, Flame } from 'lucide-react';
import { teamMemberAPI } from '../lib/api';

const CaloriesForm = ({ onComplete, isLoading, setIsLoading, submitText = "Save Calories Log" }) => {
  const [calories, setCalories] = useState('');
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    if (!calories || isNaN(calories) || parseFloat(calories) < 0) {
      newErrors.calories = 'Please enter a valid number of calories';
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
      const val = parseFloat(calories);
      await teamMemberAPI.logMetric({
        type: 'ACTIVE_CALORIES',
        value: val,
        unit: 'kcal'
      });
      
      onComplete({ calories: val });
    } catch (error) {
      console.error('Error saving calories metric:', error);
      setErrors({ submit: error.message || 'Failed to save calories log.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <Flame className="h-8 w-8 text-orange-500 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Active Calories Log</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Track your active energy expenditure to help us personalize your wellness index.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            How many active calories did you burn today? (kcal)
          </label>
          <input
            type="number"
            value={calories}
            onChange={(e) => setCalories(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-orange-500 focus:border-orange-500"
            placeholder="e.g. 350"
          />
          {errors.calories && (
            <p className="text-red-500 text-xs mt-2">{errors.calories}</p>
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
            disabled={isLoading || !calories}
            className="bg-orange-600 text-white px-6 py-2 rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center transition-colors"
          >
            {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
            {submitText}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CaloriesForm;
