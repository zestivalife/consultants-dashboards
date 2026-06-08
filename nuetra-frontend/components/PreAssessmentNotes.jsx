import React, { useState } from 'react';
import { FileText, AlertCircle, CheckCircle, Upload, Clock } from 'lucide-react';

const PreAssessmentNotes = ({ onComplete, initialData, isLoading, setIsLoading }) => {
  const [acknowledged, setAcknowledged] = useState(initialData?.acknowledged || false);
  const [error, setError] = useState('');

  const handleContinue = () => {
    if (!acknowledged) {
      setError('Please acknowledge that you understand and will follow these instructions');
      return;
    }

    setError('');
    onComplete({
      preAssessmentNotes: {
        acknowledged: true,
        acknowledgedAt: new Date().toISOString()
      }
    });
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <FileText className="h-10 w-10 text-blue-600 mr-3" />
          <h3 className="text-2xl font-bold text-gray-900">Before You Begin</h3>
        </div>
        <p className="text-sm text-gray-600">
          Please read these important instructions carefully before proceeding
        </p>
      </div>

      {/* Important Instructions */}
      <div className="space-y-4">
        {/* Note 1: Upload Health Report */}
        <div className="bg-blue-50 border-l-4 border-blue-500 p-6 rounded-r-lg">
          <div className="flex items-start">
            <Upload className="h-6 w-6 text-blue-600 mr-3 mt-1 flex-shrink-0" />
            <div>
              <h4 className="text-lg font-semibold text-blue-900 mb-2">
                1. Upload Your Health Checkup Report
              </h4>
              <p className="text-sm text-blue-800 mb-3">
                Please have your <span className="font-semibold">full-body health checkup report</span> ready to upload. 
                Ideally, this should be from within the last <span className="font-semibold">3 months</span>.
              </p>
              <div className="bg-white rounded-md p-3 mt-2">
                <p className="text-xs text-gray-700 font-medium mb-2">Accepted formats:</p>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• PDF documents</li>
                  <li>• JPG/JPEG images</li>
                  <li>• PNG images</li>
                  <li>• Maximum file size: 10MB</li>
                </ul>
              </div>
              <p className="text-xs text-blue-700 mt-3 italic">
                💡 Having your health report helps us create a more accurate and personalized diet plan for you.
              </p>
            </div>
          </div>
        </div>

        {/* Note 2: Quiet Space for Stress Test */}
        <div className="bg-purple-50 border-l-4 border-purple-500 p-6 rounded-r-lg">
          <div className="flex items-start">
            <Clock className="h-6 w-6 text-purple-600 mr-3 mt-1 flex-shrink-0" />
            <div>
              <h4 className="text-lg font-semibold text-purple-900 mb-2">
                2. Find a Quiet, Uninterrupted Space
              </h4>
              <p className="text-sm text-purple-800 mb-3">
                For the <span className="font-semibold">stress assessment test</span>, please ensure you're in a:
              </p>
              <div className="bg-white rounded-md p-3 mt-2">
                <ul className="text-sm text-gray-700 space-y-2">
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Quiet environment without distractions</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Comfortable seating position</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                    <span>15-20 minutes of uninterrupted time</span>
                  </li>
                  <li className="flex items-start">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2 mt-0.5 flex-shrink-0" />
                    <span>Calm and relaxed state of mind</span>
                  </li>
                </ul>
              </div>
              <p className="text-xs text-purple-700 mt-3 italic">
                💡 This helps us get the most accurate assessment of your stress levels.
              </p>
            </div>
          </div>
        </div>

        {/* Time Estimate */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-center text-sm text-gray-700">
            <Clock className="h-5 w-5 text-gray-500 mr-2" />
            <span>
              <span className="font-semibold">Estimated time:</span> 10-15 minutes to complete all steps
            </span>
          </div>
        </div>
      </div>

      {/* Acknowledgement Checkbox */}
      <div className="bg-white border-2 border-gray-300 rounded-lg p-6">
        <label className="flex items-start cursor-pointer">
          <input
            type="checkbox"
            checked={acknowledged}
            onChange={(e) => {
              setAcknowledged(e.target.checked);
              setError('');
            }}
            className="h-5 w-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-0.5 flex-shrink-0"
          />
          <span className="ml-3 text-sm text-gray-700">
            <span className="font-semibold">I understand and will follow these instructions.</span>
            <br />
            <span className="text-xs text-gray-500 mt-1 block">
              I confirm that I have read the above requirements and am ready to proceed with the diet plan assessment.
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

      {/* Continue Button */}
      <div className="flex justify-end">
        <button
          onClick={handleContinue}
          disabled={!acknowledged || isLoading}
          className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          I'm Ready - Let's Begin
        </button>
      </div>

      {/* Privacy Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-xs text-blue-800 text-center">
          🔒 Your information is secure and confidential. We follow strict privacy guidelines to protect your health data.
        </p>
      </div>
    </div>
  );
};

export default PreAssessmentNotes;

