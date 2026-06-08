import React, { useState } from 'react';
import { AlertCircle, Loader, Apple } from 'lucide-react';
import { teamMemberAPI } from '../lib/api';

const NourishmentForm = ({ onComplete, isLoading, setIsLoading, submitText = "Save Nourishment Log" }) => {
  const [responses, setResponses] = useState({
    mealFrequency: null,
    proteinSource: null,
    proteinIntake: null,
    fruitVeg: null,
    mealGaps: null,
    waterIntake: null,
    foodType: null
  });
  
  const [errors, setErrors] = useState({});

  const calculateNourishmentScore = () => {
    let score = 0;
    
    // Protein Adequacy (35%)
    if (responses.proteinSource === 'Yes, most meals') score += 20;
    else if (responses.proteinSource === 'Some meals') score += 10;
    
    if (responses.proteinIntake === 'Adequate') score += 15;
    else if (responses.proteinIntake === 'Slightly low') score += 7.5;

    // Meal Regularity (25%)
    if (responses.mealFrequency === '3' || responses.mealFrequency === '4-5') score += 10;
    else if (responses.mealFrequency === '1-2') score += 5;

    if (responses.mealGaps === 'No') score += 15;
    else if (responses.mealGaps === 'Yes, once') score += 7.5;

    // Food Quality (25%)
    if (responses.fruitVeg === '>5' || responses.fruitVeg === '4-5') score += 12.5;
    else if (responses.fruitVeg === '2-3') score += 6.25;

    if (responses.foodType === 'Home-cooked') score += 12.5;
    else if (responses.foodType === 'Mixed') score += 6.25;

    // Hydration (15%)
    if (responses.waterIntake === '>3 L' || responses.waterIntake === '2-3 L') score += 15;
    else if (responses.waterIntake === '1-2 L') score += 7.5;

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

    const finalScore = calculateNourishmentScore();

    try {
      await teamMemberAPI.logMetric({
        type: 'NOURISHMENT_SCORE',
        value: finalScore,
        unit: '/100',
        notes: JSON.stringify(responses)
      });
      
      onComplete({
        score: finalScore
      });
    } catch (error) {
      console.error('Error saving nourishment metric:', error);
      setErrors({ submit: error.message || 'Failed to save nourishment log.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <Apple className="h-8 w-8 text-green-500 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Nourishment Assessment</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Track your daily dietary habits to optimize your nutrition and health.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* Meal Frequency & Gaps (Meal Regularity) */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 border-b pb-2">Meal Regularity</h4>
          
          <div>
            <p className="text-sm text-gray-700 mb-2">How many meals did you eat today?</p>
            <div className="space-y-2">
              {['1-2', '3', '4-5'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.mealFrequency === opt} onChange={() => handleChange('mealFrequency', opt)} className="h-4 w-4 text-green-600 border-gray-300 focus:ring-green-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.mealFrequency && <p className="text-red-500 text-xs mt-1">{errors.mealFrequency}</p>}
          </div>

          <div>
            <p className="text-sm text-gray-700 mb-2">Did you skip meals or have long gaps (&gt;5 hrs)?</p>
            <div className="space-y-2">
              {['No', 'Yes, once', 'Yes, multiple times'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.mealGaps === opt} onChange={() => handleChange('mealGaps', opt)} className="h-4 w-4 text-green-600 border-gray-300 focus:ring-green-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.mealGaps && <p className="text-red-500 text-xs mt-1">{errors.mealGaps}</p>}
          </div>
        </div>

        {/* Protein Adequacy */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 border-b pb-2">Protein Adequacy</h4>
          
          <div>
            <p className="text-sm text-gray-700 mb-2">Did each main meal include a protein source?</p>
            <div className="space-y-2">
              {['Yes, most meals', 'Some meals', 'Rarely'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.proteinSource === opt} onChange={() => handleChange('proteinSource', opt)} className="h-4 w-4 text-green-600 border-gray-300 focus:ring-green-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.proteinSource && <p className="text-red-500 text-xs mt-1">{errors.proteinSource}</p>}
          </div>

          <div>
            <p className="text-sm text-gray-700 mb-2">How would you rate your protein intake today?</p>
            <div className="space-y-2">
              {['Adequate', 'Slightly low', 'Very low'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.proteinIntake === opt} onChange={() => handleChange('proteinIntake', opt)} className="h-4 w-4 text-green-600 border-gray-300 focus:ring-green-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.proteinIntake && <p className="text-red-500 text-xs mt-1">{errors.proteinIntake}</p>}
          </div>
        </div>

        {/* Food Quality & Hydration */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 border-b pb-2">Food Quality & Hydration</h4>
          
          <div>
            <p className="text-sm text-gray-700 mb-2">How many servings of fruits & vegetables did you consume today?</p>
            <div className="space-y-2">
              {['0-1', '2-3', '4-5', '>5'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.fruitVeg === opt} onChange={() => handleChange('fruitVeg', opt)} className="h-4 w-4 text-green-600 border-gray-300 focus:ring-green-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.fruitVeg && <p className="text-red-500 text-xs mt-1">{errors.fruitVeg}</p>}
          </div>

          <div>
            <p className="text-sm text-gray-700 mb-2">Food type today was mostly:</p>
            <div className="space-y-2">
              {['Home-cooked', 'Mixed', 'Mostly packaged / outside'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.foodType === opt} onChange={() => handleChange('foodType', opt)} className="h-4 w-4 text-green-600 border-gray-300 focus:ring-green-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.foodType && <p className="text-red-500 text-xs mt-1">{errors.foodType}</p>}
          </div>

          <div>
            <p className="text-sm text-gray-700 mb-2">Water intake today?</p>
            <div className="space-y-2">
              {['<1 L', '1-2 L', '2-3 L', '>3 L'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.waterIntake === opt} onChange={() => handleChange('waterIntake', opt)} className="h-4 w-4 text-green-600 border-gray-300 focus:ring-green-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.waterIntake && <p className="text-red-500 text-xs mt-1">{errors.waterIntake}</p>}
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
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
            {submitText}
          </button>
        </div>
      </form>
    </div>
  );
};

export default NourishmentForm;
