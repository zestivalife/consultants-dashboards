import React, { useState } from 'react';
import { AlertCircle, Loader, Zap } from 'lucide-react';
import { teamMemberAPI } from '../lib/api';

const EnergyBalanceForm = ({ onComplete, initialFocusScore, isLoading, setIsLoading, submitText = "Save Energy Log" }) => {
  const focusScore = initialFocusScore !== null ? initialFocusScore : 75; // Default if not found
  
  const [responses, setResponses] = useState({
    sleepHours: null,
    sleepConsistent: null,
    mealGaps: null,
    waterIntake: null,
    afternoonEnergy: null,
    energyCrash: null
  });
  
  const [errors, setErrors] = useState({});

  const calculateEnergyScore = () => {
    let score = 0;
    
    // Sleep (30%)
    if (responses.sleepHours === '>8' || responses.sleepHours === '7-8') score += 20;
    else if (responses.sleepHours === '6-7') score += 10;
    else if (responses.sleepHours === '5-6') score += 5;

    if (responses.sleepConsistent === 'Yes') score += 10;
    else if (responses.sleepConsistent === 'Somewhat') score += 5;

    // Focus Score (30%)
    score += (30 * (focusScore / 100));

    // Meal Timing (20%)
    if (responses.mealGaps === 'No') score += 20;
    else if (responses.mealGaps === '1 long gap') score += 10;

    // Hydration (10%)
    if (responses.waterIntake === '>3 L' || responses.waterIntake === '2-3 L') score += 10;
    else if (responses.waterIntake === '1-2 L') score += 5;

    // Energy Check-ins (10%)
    if (responses.afternoonEnergy === 'High') score += 5;
    else if (responses.afternoonEnergy === 'Moderate') score += 2.5;

    if (responses.energyCrash === 'No') score += 5;
    else if (responses.energyCrash === 'Sometimes') score += 2.5;

    return Math.max(0, Math.min(100, Math.round(score)));
  };

  const handleChange = (field, value) => {
    setResponses(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => {
        const newErrs = { ...prev };
        delete newErrs[field];
        return newErrs;
      });
    }
  };

  const validateForm = () => {
    const newErrors = {};
    Object.keys(responses).forEach(key => {
      if (responses[key] === null) {
        newErrors[key] = 'This field is required';
      }
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsLoading(true);
    setErrors({});

    const finalScore = calculateEnergyScore();

    try {
      await teamMemberAPI.logMetric({
        type: 'ENERGY_BALANCE_SCORE',
        value: finalScore,
        unit: '/100',
        notes: JSON.stringify({ ...responses, focusScore })
      });
      
      onComplete({
        score: finalScore
      });
    } catch (error) {
      console.error('Error saving energy balance metric:', error);
      setErrors({ submit: error.message || 'Failed to save energy log.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <Zap className="h-8 w-8 text-yellow-500 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Energy Balance Assessment</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Check in on your sleep, meals, and daily energy levels.
        </p>
        <div className="bg-yellow-50 text-yellow-800 text-sm p-3 rounded-lg inline-block">
          Using Focus Score: {focusScore} / 100 {initialFocusScore === null ? '(Defaulted)' : '(Auto-linked)'}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* Sleep */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 border-b pb-2">Sleep</h4>
          
          <div>
            <p className="text-sm text-gray-700 mb-2">How many hours did you sleep last night?</p>
            <div className="space-y-2">
              {['<5', '5-6', '6-7', '7-8', '>8'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.sleepHours === opt} onChange={() => handleChange('sleepHours', opt)} className="h-4 w-4 text-yellow-600 border-gray-300 focus:ring-yellow-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.sleepHours && <p className="text-red-500 text-xs mt-1">{errors.sleepHours}</p>}
          </div>

          <div>
            <p className="text-sm text-gray-700 mb-2">Was your sleep timing consistent over the last 3 days?</p>
            <div className="space-y-2">
              {['Yes', 'Somewhat', 'No'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.sleepConsistent === opt} onChange={() => handleChange('sleepConsistent', opt)} className="h-4 w-4 text-yellow-600 border-gray-300 focus:ring-yellow-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.sleepConsistent && <p className="text-red-500 text-xs mt-1">{errors.sleepConsistent}</p>}
          </div>
        </div>

        {/* Meals */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 border-b pb-2">Meals</h4>
          
          <div>
            <p className="text-sm text-gray-700 mb-2">Did you have long gaps (&gt;5 hrs) between meals yesterday?</p>
            <div className="space-y-2">
              {['No', '1 long gap', '2 or more gaps'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.mealGaps === opt} onChange={() => handleChange('mealGaps', opt)} className="h-4 w-4 text-yellow-600 border-gray-300 focus:ring-yellow-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.mealGaps && <p className="text-red-500 text-xs mt-1">{errors.mealGaps}</p>}
          </div>
        </div>

        {/* Hydration */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 border-b pb-2">Hydration</h4>
          
          <div>
            <p className="text-sm text-gray-700 mb-2">Approximate water intake yesterday?</p>
            <div className="space-y-2">
              {['<1 L', '1-2 L', '2-3 L', '>3 L'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.waterIntake === opt} onChange={() => handleChange('waterIntake', opt)} className="h-4 w-4 text-yellow-600 border-gray-300 focus:ring-yellow-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.waterIntake && <p className="text-red-500 text-xs mt-1">{errors.waterIntake}</p>}
          </div>
        </div>

        {/* Energy Check */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 border-b pb-2">Energy Check</h4>
          
          <div>
            <p className="text-sm text-gray-700 mb-2">How was your energy level in the afternoon (2–5 PM)?</p>
            <div className="space-y-2">
              {['High', 'Moderate', 'Low'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.afternoonEnergy === opt} onChange={() => handleChange('afternoonEnergy', opt)} className="h-4 w-4 text-yellow-600 border-gray-300 focus:ring-yellow-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.afternoonEnergy && <p className="text-red-500 text-xs mt-1">{errors.afternoonEnergy}</p>}
          </div>

          <div>
            <p className="text-sm text-gray-700 mb-2">Did you feel a crash or heaviness after meals?</p>
            <div className="space-y-2">
              {['No', 'Sometimes', 'Often'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.energyCrash === opt} onChange={() => handleChange('energyCrash', opt)} className="h-4 w-4 text-yellow-600 border-gray-300 focus:ring-yellow-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.energyCrash && <p className="text-red-500 text-xs mt-1">{errors.energyCrash}</p>}
          </div>
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
            disabled={isLoading}
            className="bg-yellow-500 text-white px-6 py-2 rounded-lg hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
            {submitText}
          </button>
        </div>
      </form>
    </div>
  );
};

export default EnergyBalanceForm;
