import React, { useState } from 'react';
import { AlertCircle, Loader, Activity, Info } from 'lucide-react';
import { assessmentAPI } from '../lib/api';

const PhysicalEaseForm = ({ onComplete, initialData, isLoading, setIsLoading, submitText = "Submit Assessment" }) => {
  const [responses, setResponses] = useState(initialData || Array(9).fill(null));
  const [errors, setErrors] = useState({});
  const [calculatedScore, setCalculatedScore] = useState(null);

  const questions = [
    {
      id: 1,
      text: "Do you have any joint or muscle pain today?",
      options: [{ value: 1, label: "Yes" }, { value: 0, label: "No" }]
    },
    {
      id: 2,
      text: "How intense is your pain today? (0 = No pain to 10 = Severe pain)",
      type: "scale",
      min: 0,
      max: 10
    },
    {
      id: 3,
      text: "Do you experience morning stiffness lasting more than 30 minutes?",
      options: [{ value: 1, label: "Yes" }, { value: 0, label: "No" }]
    },
    {
      id: 4,
      text: "Does pain limit your daily activities today?",
      options: [
        { value: 0, label: "Not at all" },
        { value: 1, label: "Slightly" },
        { value: 2, label: "Moderately" },
        { value: 3, label: "Severely" }
      ]
    },
    {
      id: 5,
      text: "Do you feel discomfort while sitting or standing for long periods?",
      options: [
        { value: 0, label: "No" },
        { value: 1, label: "Sometimes" },
        { value: 2, label: "Often" }
      ]
    },
    {
      id: 6,
      text: "Was your sedentary (sitting) time more than 6 hours today?",
      options: [{ value: 1, label: "Yes" }, { value: 0, label: "No" }]
    },
    {
      id: 7,
      text: "How physically fresh do you feel on waking up today?",
      options: [
        { value: 0, label: "Fresh" },
        { value: 1, label: "Somewhat fresh" },
        { value: 2, label: "Not fresh" }
      ]
    },
    {
      id: 8,
      text: "Did you do any stretching or mobility work today?",
      options: [{ value: 1, label: "Yes" }, { value: 0, label: "No" }]
    },
    {
      id: 9,
      text: "Did you take regular movement breaks during the day?",
      options: [
        { value: 1, label: "Yes" },
        { value: 2, label: "Sometimes" },
        { value: 0, label: "No" }
      ]
    }
  ];

  const calculateScore = (currentResponses) => {
    let score = 100;
    
    // Q1
    if (currentResponses[0] === 1) score -= 12;
    // Q2
    if (currentResponses[1] !== null) score -= (currentResponses[1] * 3);
    // Q3
    if (currentResponses[2] === 1) score -= 10;
    // Q4
    if (currentResponses[3] === 1) score -= 5;
    if (currentResponses[3] === 2) score -= 10;
    if (currentResponses[3] === 3) score -= 20;
    // Q5
    if (currentResponses[4] === 1) score -= 5;
    if (currentResponses[4] === 2) score -= 10;
    // Q6
    if (currentResponses[5] === 1) score -= 8;
    // Q7
    if (currentResponses[6] === 1) score -= 5;
    if (currentResponses[6] === 2) score -= 10;
    // Q8
    if (currentResponses[7] === 1) score += 10;
    // Q9
    if (currentResponses[8] === 1) score += 8;
    if (currentResponses[8] === 2) score += 4;

    score = Math.max(0, Math.min(100, score));
    return score;
  };

  const getInterpretation = (score) => {
    if (score >= 75) return 'Comfortable & Ready';
    if (score >= 55) return 'Mild Physical Strain';
    if (score >= 35) return 'High Physical Load';
    return 'Recovery Needed';
  };

  const getInsight = (score) => {
    if (score >= 75) return 'Great job maintaining your mobility and movement today!';
    if (score >= 55) return 'Consider adding some gentle stretching to ease that mild strain.';
    if (score >= 35) return 'Try taking more frequent movement breaks and focus on recovery.';
    return 'Prioritize rest and recovery. If pain persists, consult a professional.';
  };

  const handleResponseChange = (questionIndex, value) => {
    const newResponses = [...responses];
    newResponses[questionIndex] = parseInt(value);
    setResponses(newResponses);
    
    // Clear error for this question
    if (errors[`question_${questionIndex}`]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[`question_${questionIndex}`];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    const newErrors = {};
    responses.forEach((response, index) => {
      // For Q2 (scale), 0 is a valid falsy value, so we must check explicitly for null/undefined
      if (response === null || response === undefined || Number.isNaN(response)) {
        newErrors[`question_${index}`] = 'This question is required';
      }
    });

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

    const score = calculateScore(responses);
    setCalculatedScore(score);

    try {
      const formattedResponses = responses.map((value, index) => ({
        question_id: questions[index].id,
        response_value: value
      }));
      
      const result = await assessmentAPI.submitPhysicalEase(formattedResponses);
      console.log('Physical Ease responses saved:', result);
      
      // Also log as a metric for dashboard persistence
      try {
        const { teamMemberAPI } = await import('../lib/api');
        await teamMemberAPI.logMetric({
          type: 'PHYSICAL_EASE_SCORE',
          value: score,
          unit: '/100',
          notes: 'Log from PhysicalEaseForm'
        });
      } catch (metricError) {
        console.error('Error logging Physical Ease metric:', metricError);
        // Don't fail the whole submission if metric logging fails
      }
      
      // Pass the computed score back to parent
      setTimeout(() => {
        setIsLoading(false);
        onComplete({
          score,
          interpretation: getInterpretation(score),
          insight: getInsight(score)
        });
      }, 2500); // Wait a bit so the user can see their score
    } catch (error) {
      console.error('Error saving Physical Ease responses:', error);
      setErrors({ submit: error.message || 'Failed to save responses. Please try again.' });
      setIsLoading(false);
    }
  };

  const completedQuestions = responses.filter(r => r !== null && r !== undefined && !Number.isNaN(r)).length;
  const progressPercentage = (completedQuestions / questions.length) * 100;

  if (calculatedScore !== null && !errors.submit) {
    return (
      <div className="text-center py-8">
        <h3 className="text-2xl font-bold mb-4">Your Physical Ease Score</h3>
        <div className="relative inline-flex items-center justify-center w-32 h-32 rounded-full border-8 mb-4 border-indigo-500">
          <span className="text-4xl font-bold text-gray-800">{calculatedScore}</span>
        </div>
        <h4 className="text-lg font-semibold text-gray-700">{getInterpretation(calculatedScore)}</h4>
        <p className="text-gray-500 mt-2 max-w-sm mx-auto">{getInsight(calculatedScore)}</p>
        {isLoading && (
          <div className="mt-6 flex items-center justify-center text-indigo-600">
            <Loader className="h-5 w-5 animate-spin mr-2" />
            <span>Saving results...</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <Activity className="h-8 w-8 text-indigo-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Physical Ease Assessment</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Measure your daily body comfort, mobility, and physical strain.
        </p>
        
        <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
          <div 
            className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        <p className="text-xs text-gray-500">
          {completedQuestions} of {questions.length} questions completed
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {questions.map((question, index) => (
          <div key={question.id} className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">
                Question {question.id} of {questions.length}
              </h4>
              <p className="text-sm text-gray-700">{question.text}</p>
            </div>

            <div className="space-y-2">
              {question.type === 'scale' ? (
                <div className="flex flex-col space-y-2">
                  <input
                    type="range"
                    min={question.min}
                    max={question.max}
                    value={responses[index] !== null ? responses[index] : 0}
                    onChange={(e) => handleResponseChange(index, e.target.value)}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                  />
                  <div className="flex justify-between text-xs text-gray-500 px-1">
                    <span>0 (No pain)</span>
                    <span className="font-bold text-indigo-600">{responses[index] !== null ? responses[index] : ''}</span>
                    <span>10 (Severe)</span>
                  </div>
                </div>
              ) : (
                question.options.map((option) => (
                  <label key={option.value} className="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name={`question_${index}`}
                      value={option.value}
                      checked={responses[index] === option.value}
                      onChange={(e) => handleResponseChange(index, e.target.value)}
                      className="h-4 w-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
                    />
                    <span className="ml-3 text-sm text-gray-700">{option.label}</span>
                  </label>
                ))
              )}
            </div>

            {errors[`question_${index}`] && (
              <p className="text-red-500 text-xs mt-2">{errors[`question_${index}`]}</p>
            )}
          </div>
        ))}

        {errors.submit && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <p className="text-red-700">{errors.submit}</p>
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isLoading || completedQuestions < questions.length}
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

export default PhysicalEaseForm;
