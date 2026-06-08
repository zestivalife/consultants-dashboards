import React, { useState } from 'react';
import { FileText, ExternalLink, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { apiRequest } from '../lib/api';

const HealthQuestionnaire = ({ dietPlanId, onComplete, isLoading, setIsLoading }) => {
  const [formSubmitted, setFormSubmitted] = useState(false);
  const [responseNotes, setResponseNotes] = useState('');
  const [error, setError] = useState('');

  /**
   * Health questionnaire points:
   * Users open the form in a new tab and complete it externally
   * When they return, they confirm completion
   * We save this confirmation to track that they've completed the step
   */
  const GOOGLE_FORM_URL = 'https://forms.gle/health-questionnaire-2024';

  const handleFormSubmitted = async () => {
    if (!formSubmitted) {
      setError('Please confirm that you have completed the Google Form');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Save questionnaire completion status to backend
      if (dietPlanId) {
        try {
          await apiRequest(`/nutrition/diet-plans/${dietPlanId}/questionnaire`, {
            method: 'POST',
            body: {
              completed: true,
              completedAt: new Date().toISOString(),
              responseNotes: responseNotes || '',
              source: 'google-form',
              skipped: false
            }
          });
          console.log('Questionnaire completion saved');
        } catch (apiErr) {
          // Non-critical - questionnaire response still continues
          console.warn('Could not save questionnaire status to backend:', apiErr);
          // Only throw if it's an auth error
          if (apiErr.status === 401 || apiErr.status === 403) {
            throw apiErr;
          }
        }
      }
      
      // Always continue to next step
      onComplete({
        healthQuestionnaireCompleted: true,
        questionnaireNotes: responseNotes,
        completedAt: new Date().toISOString()
      });
    } catch (err) {
      console.error('Error saving questionnaire completion:', err);
      // On auth error, throw; otherwise continue
      if (err.status === 401 || err.status === 403) {
        setError('Your session has expired. Please refresh and try again.');
        throw err;
      }
      // For other errors, continue anyway
      onComplete({
        healthQuestionnaireCompleted: true,
        questionnaireNotes: responseNotes,
        completedAt: new Date().toISOString()
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    onComplete({
      healthQuestionnaireCompleted: false,
      skipped: true
    });
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <FileText className="h-10 w-10 text-green-600 mr-3" />
          <h3 className="text-2xl font-bold text-gray-900">Health Questionnaire</h3>
        </div>
        <p className="text-sm text-gray-600">
          Please complete the health questionnaire to help us understand your health history and goals
        </p>
      </div>

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h4 className="text-sm font-semibold text-blue-900 mb-3">Instructions:</h4>
        <ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside">
          <li>Click the button below to open the health questionnaire in a new tab</li>
          <li>Complete all required fields in the Google Form</li>
          <li>Submit the form when you're done</li>
          <li>Return to this page and click "I've Completed the Form" to continue</li>
        </ol>
      </div>

      {/* External Form Link */}
      <div className="bg-white border-2 border-dashed border-green-300 rounded-lg p-8 text-center">
        <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h4 className="text-lg font-semibold text-gray-900 mb-3">
          Health & Lifestyle Questionnaire
        </h4>
        <p className="text-sm text-gray-600 mb-6 max-w-md mx-auto">
          This questionnaire will help us understand your dietary preferences, health conditions, 
          lifestyle habits, and wellness goals. It typically takes 5-10 minutes to complete.
        </p>
        <a
          href={GOOGLE_FORM_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors font-medium"
        >
          Open Health Questionnaire
          <ExternalLink className="h-4 w-4" />
        </a>
      </div>

      {/* Optional Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Additional Notes (Optional)
        </label>
        <textarea
          value={responseNotes}
          onChange={(e) => setResponseNotes(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
          rows="3"
          placeholder="Any additional health information you'd like to share with your dietitian..."
        />
      </div>

      {/* Confirmation Checkbox */}
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <label className="flex items-start cursor-pointer">
          <input
            type="checkbox"
            checked={formSubmitted}
            onChange={(e) => {
              setFormSubmitted(e.target.checked);
              if (e.target.checked) setError('');
            }}
            className="h-5 w-5 text-green-600 border-gray-300 rounded focus:ring-green-500 mt-0.5 flex-shrink-0"
          />
          <span className="ml-3 text-sm text-gray-700">
            <span className="font-semibold">I have completed the health questionnaire</span>
            <br />
            <span className="text-xs text-gray-500 mt-1 block">
              I confirm that I have filled out and submitted the Google Form with accurate information.
            </span>
          </span>
        </label>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
          <AlertCircle className="h-5 w-5 text-red-600 mr-2 flex-shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Privacy Notice */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Privacy & Data Usage</h4>
        <div className="text-xs text-gray-600 space-y-1">
          <p>• Your responses will be stored securely and used only for creating your personalized diet plan</p>
          <p>• Only your assigned dietician will have access to review these responses</p>
          <p>• No computed scores will be displayed in your dashboard</p>
          <p>• You can request deletion of this data at any time by contacting support</p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between">
        <button
          onClick={handleSkip}
          disabled={isLoading}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50"
        >
          Skip for now
        </button>
        
        <button
          onClick={handleFormSubmitted}
          disabled={isLoading || !formSubmitted}
          className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
          I've Completed the Form
        </button>
      </div>
    </div>
  );
};

export default HealthQuestionnaire;
