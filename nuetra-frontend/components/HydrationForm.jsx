import React, { useState } from 'react';
import { AlertCircle, Loader, Droplet } from 'lucide-react';
import { teamMemberAPI } from '../lib/api';

const HydrationForm = ({ onComplete, initialData, isLoading, setIsLoading, submitText = "Save Hydration Log" }) => {
  const [liters, setLiters] = useState(initialData?.liters || null);
  const [errors, setErrors] = useState({});

  const hydrationOptions = [
    { value: 0.5, label: "<1 L" },
    { value: 1.5, label: "1–2 L" },
    { value: 2.5, label: "2–3 L" },
    { value: 3.5, label: ">3 L" }
  ];

  const validateForm = () => {
    const newErrors = {};
    if (!liters) newErrors.liters = 'Please select your approximate water intake';

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
      // Save to metrics
      const result = await teamMemberAPI.logMetric({
        type: 'HYDRATION',
        value: liters,
        unit: 'L'
      });
      
      console.log('Hydration metric saved:', result);

      onComplete({
        litersValue: liters
      });
    } catch (error) {
      console.error('Error saving hydration metric:', error);
      setErrors({ submit: error.message || 'Failed to save hydration log. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <Droplet className="h-8 w-8 text-cyan-500 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Hydration Log</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Tracking your water intake helps ensure your body stays adequately hydrated.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">
            Approximate water intake yesterday?
          </h4>
          <div className="space-y-2">
            {hydrationOptions.map((option) => (
              <label key={option.value} className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name="hydration_liters"
                  value={option.value}
                  checked={liters === option.value}
                  onChange={() => {
                    setLiters(option.value);
                    setErrors(prev => ({ ...prev, liters: null }));
                  }}
                  className="h-4 w-4 text-cyan-600 border-gray-300 focus:ring-cyan-500"
                />
                <span className="ml-3 text-sm text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
          {errors.liters && (
            <p className="text-red-500 text-xs mt-2">{errors.liters}</p>
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
            disabled={isLoading || !liters}
            className="bg-cyan-600 text-white px-6 py-2 rounded-lg hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
            {submitText}
          </button>
        </div>
      </form>
    </div>
  );
};

export default HydrationForm;
