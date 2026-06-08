import React, { useState } from 'react';
import { AlertCircle, Loader, Heart } from 'lucide-react';
import { teamMemberAPI } from '../lib/api';
import PhysicalEaseForm from './PhysicalEaseForm';

const BodySupportForm = ({ onComplete, initialMobilityScore, userAge, isLoading, setIsLoading, submitText = "Save Body Support Log" }) => {
  const [mobilityScore, setMobilityScore] = useState(initialMobilityScore);
  const [showPhysicalEase, setShowPhysicalEase] = useState(initialMobilityScore === null || initialMobilityScore === undefined);
  
  const [responses, setResponses] = useState({
    steps: null,
    exercise: null,
    fatigue: null,
    pain: null
  });
  
  const [errors, setErrors] = useState({});

  const calculateBodySupportScore = () => {
    let score = 0;
    
    // Movement (35%)
    if (responses.steps === '>10,000') score += 35;
    else if (responses.steps === '6,000–10,000') score += 25;
    else if (responses.steps === '3,000–6,000') score += 15;

    // Mobility (25%) - from Physical Ease Score out of 100
    const validMobility = mobilityScore !== null ? mobilityScore : 80;
    score += (25 * (validMobility / 100));

    // Exercise frequency (20%)
    if (responses.exercise === 'Intense') score += 20;
    else if (responses.exercise === 'Moderate') score += 15;
    else if (responses.exercise === 'Light') score += 10;

    // Fatigue/Pain (20%)
    // Fatigue max 10
    if (responses.fatigue === 'No') score += 10;
    else if (responses.fatigue === 'Mild') score += 6;
    else if (responses.fatigue === 'Moderate') score += 3;
    
    // Pain max 10
    if (responses.pain === 'No') score += 10;
    else if (responses.pain === 'Yes – mild') score += 5;

    // Age factor is listed as modifier but omitted from % formula
    // (Movement 35 + Mobility 25 + Exercise 20 + Fatigue/Pain 20 = 100)
    
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

    const finalScore = calculateBodySupportScore();

    try {
      await teamMemberAPI.logMetric({
        type: 'BODY_SUPPORT_SCORE',
        value: finalScore,
        unit: '/100',
        notes: JSON.stringify({ ...responses, mobilityScore, userAge })
      });
      
      onComplete({
        score: finalScore
      });
    } catch (error) {
      console.error('Error saving body support metric:', error);
      setErrors({ submit: error.message || 'Failed to save body support log.' });
    } finally {
      setIsLoading(false);
    }
  };

  if (showPhysicalEase) {
    return (
      <div className="space-y-4">
        <div className="bg-pink-50 p-4 rounded-lg">
          <p className="text-pink-800 text-sm">
            We need your current Mobility / Physical Ease Score to calculate your Body Support accurately. Please complete the Physical Ease assessment first.
          </p>
        </div>
        <PhysicalEaseForm 
          isLoading={isLoading} 
          setIsLoading={setIsLoading} 
          submitText="Calculate Mobility Score"
          onComplete={({ score }) => {
            setMobilityScore(score);
            setShowPhysicalEase(false);
          }} 
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <Heart className="h-8 w-8 text-pink-500 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Body Support Assessment</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Track your movement, exercise, and physical ease to maintain optimal body support.
        </p>
        {mobilityScore !== null && (
          <div className="bg-green-50 text-green-800 text-sm p-3 rounded-lg inline-block">
            Using Mobility Score: {mobilityScore} / 100
          </div>
        )}
        {userAge && (
          <div className="bg-gray-50 text-gray-800 text-sm p-3 rounded-lg inline-block ml-2">
            Age Modifier Active: {userAge} yrs
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* Movement */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 border-b pb-2">Movement</h4>
          
          <div>
            <p className="text-sm text-gray-700 mb-2">How many steps did you take today (approx.)?</p>
            <div className="space-y-2">
              {['<3,000', '3,000–6,000', '6,000–10,000', '>10,000'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.steps === opt} onChange={() => handleChange('steps', opt)} className="h-4 w-4 text-pink-600 border-gray-300 focus:ring-pink-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.steps && <p className="text-red-500 text-xs mt-1">{errors.steps}</p>}
          </div>
        </div>

        {/* Exercise */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 border-b pb-2">Exercise</h4>
          
          <div>
            <p className="text-sm text-gray-700 mb-2">Did you do any structured exercise today?</p>
            <div className="space-y-2">
              {['No', 'Light', 'Moderate', 'Intense'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.exercise === opt} onChange={() => handleChange('exercise', opt)} className="h-4 w-4 text-pink-600 border-gray-300 focus:ring-pink-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.exercise && <p className="text-red-500 text-xs mt-1">{errors.exercise}</p>}
          </div>
        </div>

        {/* Pain & Fatigue */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 border-b pb-2">Pain & Fatigue</h4>
          
          <div>
            <p className="text-sm text-gray-700 mb-2">Did you feel physical fatigue today?</p>
            <div className="space-y-2">
              {['No', 'Mild', 'Moderate', 'Severe'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.fatigue === opt} onChange={() => handleChange('fatigue', opt)} className="h-4 w-4 text-pink-600 border-gray-300 focus:ring-pink-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.fatigue && <p className="text-red-500 text-xs mt-1">{errors.fatigue}</p>}
          </div>

          <div>
            <p className="text-sm text-gray-700 mb-2">Any pain or discomfort affecting movement today?</p>
            <div className="space-y-2">
              {['No', 'Yes – mild', 'Yes – significant'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.pain === opt} onChange={() => handleChange('pain', opt)} className="h-4 w-4 text-pink-600 border-gray-300 focus:ring-pink-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.pain && <p className="text-red-500 text-xs mt-1">{errors.pain}</p>}
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
            className="bg-pink-600 text-white px-6 py-2 rounded-lg hover:bg-pink-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
            {submitText}
          </button>
        </div>
      </form>
    </div>
  );
};

export default BodySupportForm;
