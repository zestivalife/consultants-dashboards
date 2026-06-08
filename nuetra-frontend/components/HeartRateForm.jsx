import React, { useState } from 'react';
import { AlertCircle, Loader, Heart } from 'lucide-react';
import { teamMemberAPI } from '../lib/api';

const HeartRateForm = ({ onComplete, isLoading, setIsLoading, submitText = "Save Heart Rate" }) => {
  const [bpm, setBpm] = useState('');
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    if (!bpm || isNaN(bpm) || parseInt(bpm) < 40 || parseInt(bpm) > 220) {
      newErrors.bpm = 'Please enter a valid heart rate (40-220 BPM)';
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
      const val = parseInt(bpm);
      await teamMemberAPI.logMetric({
        type: 'HEART_RATE',
        value: val,
        unit: 'BPM'
      });
      
      onComplete({ bpm: val });
    } catch (error) {
      console.error('Error saving heart rate metric:', error);
      setErrors({ submit: error.message || 'Failed to save heart rate log.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <div className="w-10 h-10 rounded-full bg-pink-100 flex items-center justify-center">
            <Heart className="h-6 w-6 text-pink-500" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 ml-3">Heart Rate Log</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Regularly monitoring your resting heart rate can help track your cardiovascular health and recovery.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            What is your current heart rate? (BPM)
          </label>
          <input
            type="number"
            value={bpm}
            onChange={(e) => setBpm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-pink-500 focus:border-pink-500"
            placeholder="e.g. 72"
          />
          {errors.bpm && (
            <p className="text-red-500 text-xs mt-2">{errors.bpm}</p>
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
            disabled={isLoading || !bpm}
            className="bg-pink-600 text-white px-6 py-2 rounded-lg hover:bg-pink-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center transition-colors"
          >
            {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
            {submitText}
          </button>
        </div>
      </form>
    </div>
  );
};

export default HeartRateForm;
