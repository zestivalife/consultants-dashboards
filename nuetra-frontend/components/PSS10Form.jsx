import React, { useState, useEffect } from 'react';
import { AlertCircle, Loader, CheckCircle, Shield, Info, Activity } from 'lucide-react';
import { assessmentAPI } from '../lib/api';

const PSS10Form = ({ dietPlanId, onComplete, initialData, isLoading, setIsLoading, submitText = "Continue to Booking" }) => {
  const [responses, setResponses] = useState(initialData || Array(10).fill(null));
  const [errors, setErrors] = useState({});

  const questions = [
    {
      id: 1,
      text: "In the last month, how often have you been upset because of something that happened unexpectedly?"
    },
    {
      id: 2,
      text: "In the last month, how often have you felt that you were unable to control the important things in your life?"
    },
    {
      id: 3,
      text: "In the last month, how often have you felt nervous and stressed?"
    },
    {
      id: 4,
      text: "In the last month, how often have you felt confident about your ability to handle your personal problems?"
    },
    {
      id: 5,
      text: "In the last month, how often have you felt that things were going your way?"
    },
    {
      id: 6,
      text: "In the last month, how often have you found that you could not cope with all the things that you had to do?"
    },
    {
      id: 7,
      text: "In the last month, how often have you been able to control irritations in your life?"
    },
    {
      id: 8,
      text: "In the last month, how often have you felt that you were on top of things?"
    },
    {
      id: 9,
      text: "In the last month, how often have you been angered because of things that happened that were outside of your control?"
    },
    {
      id: 10,
      text: "In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?"
    }
  ];

  const responseOptions = [
    { value: 0, label: "Never" },
    { value: 1, label: "Almost Never" },
    { value: 2, label: "Sometimes" },
    { value: 3, label: "Fairly Often" },
    { value: 4, label: "Very Often" }
  ];

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
      if (response === null || response === undefined) {
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

    try {
      // Format responses for backend submission
      const formattedResponses = responses.map((value, index) => ({
        question_id: questions[index].id,
        response_value: value
      }));
      
      // Submit PSS10 responses to backend
      const result = await assessmentAPI.submitPSS10(formattedResponses);
      console.log('PSS-10 responses saved:', result);
      
      // Calculate stress score for reference (but do NOT display to user)
      // PSS-10 scoring:
      // - Questions 4, 5, 7, 8 are reverse scored (subtract from 4)
      // - Other questions are direct scored
      // - Total score ranges from 0-40, higher = more stress
      const reverseItems = [3, 4, 6, 7]; // 0-indexed positions (questions 4, 5, 7, 8)
      let calculatedStressScore = 0;
      
      responses.forEach((val, idx) => {
        if (reverseItems.includes(idx)) {
          calculatedStressScore += (4 - val);
        } else {
          calculatedStressScore += val;
        }
      });

      console.log('Calculated stress score:', calculatedStressScore, '(for reference only - not displayed)');

      // Optionally log as a metric for backend tracking only
      try {
        const { teamMemberAPI } = await import('../lib/api');
        await teamMemberAPI.logMetric({
          type: 'STRESS_LEVEL',
          value: calculatedStressScore,
          unit: '/40',
          notes: 'PSS-10 Assessment - For dietitian review only',
          timestamp: new Date().toISOString()
        });
        console.log('Stress metric logged for backend tracking');
      } catch (metricError) {
        // Non-critical - log but don't block flow
        console.warn('Could not log stress metric:', metricError);
      }

      // Complete the step WITHOUT exposing the calculated score
      onComplete({
        pssResponses: responses,
        responseCount: responses.length,
        submittedAt: new Date().toISOString(),
        message: 'Stress assessment completed successfully'
        // NOTE: stressScore is deliberately not included in the response
        // The score is only for backend tracking, not displayed to user
      });
    } catch (error) {
      console.error('Error saving PSS-10 responses:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Failed to save responses. Please try again.';
      setErrors({ submit: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  const completedQuestions = responses.filter(r => r !== null && r !== undefined).length;
  const progressPercentage = (completedQuestions / questions.length) * 100;

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <Activity className="h-8 w-8 text-purple-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Stress Management Test</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          This questionnaire helps us understand your current stress levels to create a more personalized diet plan.
        </p>
        
        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
          <div 
            className="bg-purple-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        <p className="text-xs text-gray-500">
          {completedQuestions} of {questions.length} questions completed
        </p>
      </div>

      {/* Information Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <Info className="h-5 w-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">About this assessment:</p>
            <ul className="space-y-1 text-xs">
              <li>• This assessment helps identify how stress might affect your eating habits</li>
              <li>• Your responses are confidential and will only be used to improve your diet plan</li>
              <li>• There are no right or wrong answers - please answer honestly</li>
              <li>• This information will be reviewed by your assigned dietician</li>
            </ul>
          </div>
        </div>
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
              {responseOptions.map((option) => (
                <label key={option.value} className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name={`question_${index}`}
                    value={option.value}
                    checked={responses[index] === option.value}
                    onChange={(e) => handleResponseChange(index, e.target.value)}
                    className="h-4 w-4 text-purple-600 border-gray-300 focus:ring-purple-500"
                  />
                  <span className="ml-3 text-sm text-gray-700">{option.label}</span>
                </label>
              ))}
            </div>

            {errors[`question_${index}`] && (
              <p className="text-red-500 text-xs mt-2">{errors[`question_${index}`]}</p>
            )}
          </div>
        ))}

        {/* Submit Error */}
        {errors.submit && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <p className="text-red-700">{errors.submit}</p>
          </div>
        )}

        {/* Privacy Notice */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Privacy & Data Usage</h4>
          <div className="text-xs text-gray-600 space-y-1">
            <p>• Your responses will be stored securely and used only for creating your personalized diet plan</p>
            <p>• Only your assigned dietician will have access to review these responses</p>
            <p>• No computed stress scores will be displayed in your dashboard</p>
            <p>• You can request deletion of this data at any time by contacting support</p>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isLoading || completedQuestions < questions.length}
            className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
            {submitText}
          </button>
        </div>
      </form>
    </div>
  );
};

export default PSS10Form;