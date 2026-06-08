import React, { useState } from 'react';
import { AlertCircle, Loader, Activity } from 'lucide-react';
import { teamMemberAPI } from '../lib/api';

const StepsForm = ({ onComplete, isLoading, setIsLoading, submitText = "Save Steps Log" }) => {
  const [steps, setSteps] = useState('');
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    if (!steps || isNaN(steps) || parseInt(steps) < 0) {
      newErrors.steps = 'Please enter a valid number of steps';
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
      const val = parseInt(steps);
      await teamMemberAPI.logMetric({
        type: 'STEPS',
        value: val,
        unit: 'steps'
      });
      
      onComplete({ steps: val });
    } catch (error) {
      console.error('Error saving steps metric:', error);
      setErrors({ submit: error.message || 'Failed to save steps log.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
            <Activity className="h-6 w-6 text-blue-500" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 ml-3">Steps Today</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Tracking your daily steps is a great way to stay active and improve your physical wellness.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            How many steps have you taken today?
          </label>
          <input
            type="number"
            value={steps}
            onChange={(e) => setSteps(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g. 8500"
          />
          {errors.steps && (
            <p className="text-red-500 text-xs mt-2">{errors.steps}</p>
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
            disabled={isLoading || !steps}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center transition-colors"
          >
            {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
            {submitText}
          </button>
        </div>
      </form>
    </div>
  );
};

export default StepsForm;
