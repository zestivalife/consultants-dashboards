import React, { useState } from 'react';
import { AlertCircle, Loader, Activity } from 'lucide-react';
import { teamMemberAPI } from '../lib/api';
import PSS10Form from './PSS10Form';

const RecoveryForm = ({ onComplete, initialStressScore, isLoading, setIsLoading, submitText = "Save Recovery Log" }) => {
  const [stressScore, setStressScore] = useState(initialStressScore);
  const [showPss, setShowPss] = useState(initialStressScore === null || initialStressScore === undefined);
  
  const [responses, setResponses] = useState({
    sleepConsistent: null,
    sleepHours: null,
    relaxation: null,
    shortBreaks: null,
    screens: null,
    caffeine: null
  });
  
  const [errors, setErrors] = useState({});

  const calculatePssScore = (pssResponses) => {
    // PSS-10 Scoring logic: 4, 5, 7, 8 are reversed
    const reverseItems = [3, 4, 6, 7]; // 0-indexed
    let score = 0;
    pssResponses.forEach((val, idx) => {
      if (reverseItems.includes(idx)) {
        score += (4 - val);
      } else {
        score += val;
      }
    });
    return score;
  };

  const calculateRecoveryScore = () => {
    let score = 0;
    
    // Sleep quality (40%)
    if (responses.sleepConsistent === 'Yes') score += 15;
    else if (responses.sleepConsistent === 'Somewhat') score += 7.5;

    if (responses.sleepHours === '>8' || responses.sleepHours === '7-8') score += 25;
    else if (responses.sleepHours === '6-7') score += 12.5;

    // Stress score (30%)
    // PSS-10 ranges from 0 to 40. Lower stress = better recovery.
    const validStress = stressScore !== null ? stressScore : 20;
    score += (30 * ((40 - validStress) / 40));

    // Recovery habits (20%)
    if (responses.relaxation === 'Yes') score += 10;

    if (responses.shortBreaks === 'Yes') score += 10;
    else if (responses.shortBreaks === 'Sometimes') score += 5;

    // Screen/caffeine hygiene (10%)
    if (responses.screens === 'No') score += 5;

    if (responses.caffeine === 'No') score += 5;

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

    const finalScore = calculateRecoveryScore();

    try {
      await teamMemberAPI.logMetric({
        type: 'RECOVERY_SCORE',
        value: finalScore,
        unit: '/100',
        notes: JSON.stringify({ ...responses, stressScore })
      });
      
      onComplete({
        score: finalScore
      });
    } catch (error) {
      console.error('Error saving recovery metric:', error);
      setErrors({ submit: error.message || 'Failed to save recovery log.' });
    } finally {
      setIsLoading(false);
    }
  };

  if (showPss) {
    return (
      <div className="space-y-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-blue-800 text-sm">
            We need your current Stress Score to calculate your Recovery accurately. Please complete the PSS-10 questionnaire first.
          </p>
        </div>
        <PSS10Form 
          isLoading={isLoading} 
          setIsLoading={setIsLoading} 
          submitText="Calculate Stress Score"
          onComplete={(res) => {
            const score = calculatePssScore(res.pssResponses);
            setStressScore(score);
            setShowPss(false);
          }} 
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <Activity className="h-8 w-8 text-blue-500 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Recovery Assessment</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Track your daily recovery habits to optimize your performance.
        </p>
        {stressScore !== null && (
          <div className="bg-green-50 text-green-800 text-sm p-3 rounded-lg inline-block">
            Using Stress Score: {stressScore} / 40
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Sleep Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 border-b pb-2">Sleep</h4>
          
          <div>
            <p className="text-sm text-gray-700 mb-2">Did you sleep and wake at similar times over the last 3 days?</p>
            <div className="space-y-2">
              {['Yes', 'Somewhat', 'No'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.sleepConsistent === opt} onChange={() => handleChange('sleepConsistent', opt)} className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.sleepConsistent && <p className="text-red-500 text-xs mt-1">{errors.sleepConsistent}</p>}
          </div>

          <div>
            <p className="text-sm text-gray-700 mb-2">How many hours did you sleep last night?</p>
            <div className="space-y-2">
              {['<5', '5-6', '6-7', '7-8', '>8'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.sleepHours === opt} onChange={() => handleChange('sleepHours', opt)} className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.sleepHours && <p className="text-red-500 text-xs mt-1">{errors.sleepHours}</p>}
          </div>
        </div>

        {/* Recovery Habits Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 border-b pb-2">Recovery Habits</h4>
          
          <div>
            <p className="text-sm text-gray-700 mb-2">Did you do any breathing, relaxation, or mindfulness activity today?</p>
            <div className="space-y-2">
              {['Yes', 'No'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.relaxation === opt} onChange={() => handleChange('relaxation', opt)} className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.relaxation && <p className="text-red-500 text-xs mt-1">{errors.relaxation}</p>}
          </div>

          <div>
            <p className="text-sm text-gray-700 mb-2">Did you take short breaks to relax during the day?</p>
            <div className="space-y-2">
              {['Yes', 'Sometimes', 'No'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.shortBreaks === opt} onChange={() => handleChange('shortBreaks', opt)} className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.shortBreaks && <p className="text-red-500 text-xs mt-1">{errors.shortBreaks}</p>}
          </div>
        </div>

        {/* Screen & Caffeine Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 border-b pb-2">Screen & Caffeine</h4>
          
          <div>
            <p className="text-sm text-gray-700 mb-2">Did you use screens within 1 hour of bedtime?</p>
            <div className="space-y-2">
              {['No', 'Yes'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.screens === opt} onChange={() => handleChange('screens', opt)} className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.screens && <p className="text-red-500 text-xs mt-1">{errors.screens}</p>}
          </div>

          <div>
            <p className="text-sm text-gray-700 mb-2">Did you consume caffeine after 4 PM?</p>
            <div className="space-y-2">
              {['No', 'Yes'].map(opt => (
                <label key={opt} className="flex items-center cursor-pointer">
                  <input type="radio" checked={responses.caffeine === opt} onChange={() => handleChange('caffeine', opt)} className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500" />
                  <span className="ml-3 text-sm text-gray-700">{opt}</span>
                </label>
              ))}
            </div>
            {errors.caffeine && <p className="text-red-500 text-xs mt-1">{errors.caffeine}</p>}
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
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
            {submitText}
          </button>
        </div>
      </form>
    </div>
  );
};

export default RecoveryForm;
