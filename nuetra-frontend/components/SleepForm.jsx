import React, { useState } from 'react';
import { AlertCircle, Loader, Moon, Info } from 'lucide-react';
import { teamMemberAPI } from '../lib/api';

const SleepForm = ({ onComplete, initialData, isLoading, setIsLoading, submitText = "Save Sleep Log" }) => {
  const [hours, setHours] = useState(initialData?.hours || null);
  const [consistency, setConsistency] = useState(initialData?.consistency || null);
  const [errors, setErrors] = useState({});

  const sleepOptions = [
    { value: 4.5, label: "<5" },
    { value: 5.5, label: "5–6" },
    { value: 6.5, label: "6–7" },
    { value: 7.5, label: "7–8" },
    { value: 8.5, label: ">8" }
  ];

  const consistencyOptions = [
    { value: 'Yes', label: 'Yes' },
    { value: 'Somewhat', label: 'Somewhat' },
    { value: 'No', label: 'No' }
  ];

  const validateForm = () => {
    const newErrors = {};
    if (!hours) newErrors.hours = 'Please select your sleep duration';
    if (!consistency) newErrors.consistency = 'Please select your sleep consistency';

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
        type: 'SLEEP',
        value: hours,
        unit: 'hours',
        notes: `Consistency: ${consistency}`
      });
      
      console.log('Sleep metric saved:', result);
      
      // We pass back the label to display nicely
      const hoursLabel = sleepOptions.find(o => o.value === hours)?.label || hours;

      onComplete({
        hours: hoursLabel,
        hoursValue: hours,
        consistency
      });
    } catch (error) {
      console.error('Error saving sleep metric:', error);
      setErrors({ submit: error.message || 'Failed to save sleep log. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <Moon className="h-8 w-8 text-indigo-500 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Daily Sleep Log</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Tracking your sleep helps us personalize your recovery and wellness goals.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">
            How many hours did you sleep last night?
          </h4>
          <div className="space-y-2">
            {sleepOptions.map((option) => (
              <label key={option.value} className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name="sleep_hours"
                  value={option.value}
                  checked={hours === option.value}
                  onChange={() => {
                    setHours(option.value);
                    setErrors(prev => ({ ...prev, hours: null }));
                  }}
                  className="h-4 w-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
                />
                <span className="ml-3 text-sm text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
          {errors.hours && (
            <p className="text-red-500 text-xs mt-2">{errors.hours}</p>
          )}
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">
            Was your sleep timing consistent over the last 3 days?
          </h4>
          <div className="space-y-2">
            {consistencyOptions.map((option) => (
              <label key={option.value} className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name="sleep_consistency"
                  value={option.value}
                  checked={consistency === option.value}
                  onChange={() => {
                    setConsistency(option.value);
                    setErrors(prev => ({ ...prev, consistency: null }));
                  }}
                  className="h-4 w-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
                />
                <span className="ml-3 text-sm text-gray-700">{option.label}</span>
              </label>
            ))}
          </div>
          {errors.consistency && (
            <p className="text-red-500 text-xs mt-2">{errors.consistency}</p>
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
            disabled={isLoading || !hours || !consistency}
            className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
            {submitText}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SleepForm;
