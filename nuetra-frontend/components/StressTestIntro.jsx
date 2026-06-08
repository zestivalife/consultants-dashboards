import React, { useState, useEffect } from 'react';
import { Activity, Brain, Heart, Shield, Info, Check } from 'lucide-react';

const StressTestIntro = ({ onComplete, isLoading, setIsLoading }) => {
  const [countdown, setCountdown] = useState(null);
  const [showBreathing, setShowBreathing] = useState(false);

  useEffect(() => {
    if (countdown === null) return;

    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      // Countdown complete
      setIsLoading(false);
    }
  }, [countdown, onComplete]);

  const startBreathingExercise = () => {
    setShowBreathing(true);
    setCountdown(3);
  };

  const skipToTest = () => {
    onComplete({
      stressTestAcknowledged: true,
      acknowledgedAt: new Date().toISOString(),
      skippedBreathing: true
    });
  };

  if (showBreathing && countdown !== null) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="relative">
          {/* Breathing Animation Circle */}
          <div className={`w-48 h-48 rounded-full bg-gradient-to-br from-purple-400 to-blue-500 flex items-center justify-center transition-all duration-1000 ${
            countdown > 0 ? 'scale-100' : 'scale-110 opacity-80'
          }`}>
            <div className="text-white text-center">
              {countdown > 0 ? (
                <>
                  <p className="text-6xl font-bold mb-2">{countdown}</p>
                  <p className="text-sm">
                    {countdown === 3 && 'Inhale...'}
                    {countdown === 2 && 'Hold...'}
                    {countdown === 1 && 'Exhale...'}
                  </p>
                </>
              ) : (
                <>
                  <Check className="h-16 w-16 mx-auto mb-2 animate-bounce" />
                  <p className="text-sm font-bold">Ready</p>
                </>
              )}
            </div>
          </div>
        </div>
        
        <p className="text-gray-600 mt-8 text-center max-w-md font-medium">
          {countdown > 0 
            ? 'Center yourself and follow the rhythm...'
            : 'You are now in a calm state. Ready to begin the assessment.'
          }
        </p>

        {countdown === 0 && (
          <button
            onClick={() => onComplete({
              stressTestAcknowledged: true,
              acknowledgedAt: new Date().toISOString()
            })}
            className="mt-8 bg-purple-600 text-white px-10 py-3 rounded-lg hover:bg-purple-700 transition-all transform hover:scale-105 font-bold shadow-lg"
          >
            Begin Stress Test
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <Activity className="h-10 w-10 text-purple-600 mr-3" />
          <h3 className="text-2xl font-bold text-gray-900">Stress Assessment Introduction</h3>
        </div>
        <p className="text-sm text-gray-600">
          Let's take a moment to understand your current stress levels
        </p>
      </div>

      {/* What is PSS-10 */}
      <div className="bg-purple-50 border-l-4 border-purple-500 p-6 rounded-r-lg">
        <div className="flex items-start">
          <Brain className="h-6 w-6 text-purple-600 mr-3 mt-1 flex-shrink-0" />
          <div>
            <h4 className="text-lg font-semibold text-purple-900 mb-2">
              About the Perceived Stress Scale
            </h4>
            <p className="text-sm text-purple-800 mb-3">
              The Stress Management Test is a scientifically validated questionnaire that measures your perceived stress levels 
              over the past month. It helps us understand how stress might be affecting your eating habits and overall wellness.
            </p>
            <div className="bg-white rounded-md p-3 mt-3">
              <p className="text-xs font-semibold text-gray-700 mb-2">What to expect:</p>
              <ul className="text-xs text-gray-600 space-y-1">
                <li>• 10 simple questions about your recent experiences</li>
                <li>• Takes approximately 3-5 minutes to complete</li>
                <li>• No right or wrong answers - just answer honestly</li>
                <li>• Your responses are completely confidential</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Why This Matters */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start">
          <Info className="h-6 w-6 text-blue-600 mr-3 mt-1 flex-shrink-0" />
          <div>
            <h4 className="text-lg font-semibold text-blue-900 mb-2">
              Why Stress Assessment Matters for Your Diet Plan
            </h4>
            <p className="text-sm text-blue-800 mb-3">
              Stress significantly impacts your nutritional needs, eating patterns, and metabolism. 
              Understanding your stress levels helps us:
            </p>
            <ul className="text-sm text-blue-800 space-y-2">
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>Recommend foods that help manage stress and cortisol levels</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>Create meal plans that fit your stress-related eating patterns</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>Suggest lifestyle modifications alongside dietary changes</span>
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                <span>Provide holistic wellness support, not just nutrition advice</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Privacy & Confidentiality */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-start">
          <Shield className="h-6 w-6 text-green-600 mr-3 mt-1 flex-shrink-0" />
          <div>
            <h4 className="text-lg font-semibold text-green-900 mb-2">
              Your Privacy is Protected
            </h4>
            <div className="text-sm text-green-800 space-y-2">
              <p>
                <strong>Important:</strong> Your stress assessment results will NOT be displayed to you as a score. 
                Only your assigned dietitian will review your responses to better understand your wellness needs.
              </p>
              <p className="text-xs text-green-700 mt-2">
                This approach ensures you receive personalized support without the anxiety of numerical scores.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Breathing Exercise Prompt */}
      <div className="bg-gradient-to-br from-purple-50 to-blue-50 border-2 border-purple-200 rounded-lg p-8 text-center">
        <Heart className="h-12 w-12 text-purple-600 mx-auto mb-4" />
        <h4 className="text-lg font-semibold text-gray-900 mb-3">
          Ready to Begin?
        </h4>
        <p className="text-sm text-gray-600 mb-6 max-w-md mx-auto">
          Before we start, let's take a moment to center yourself with a brief breathing exercise. 
          This will help you answer the questions more mindfully.
        </p>
        
        <div className="flex justify-center space-x-4">
          <button
            onClick={startBreathingExercise}
            className="bg-purple-600 text-white px-8 py-3 rounded-lg hover:bg-purple-700 transition-colors font-medium"
          >
            Start Breathing Exercise (3 seconds)
          </button>
          <button
            onClick={skipToTest}
            className="bg-gray-200 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors font-medium"
          >
            Skip to Assessment
          </button>
        </div>
      </div>

      {/* Tips for Accurate Assessment */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-yellow-900 mb-2">Tips for Accurate Assessment:</h4>
        <ul className="text-xs text-yellow-800 space-y-1">
          <li>• Find a quiet space where you won't be interrupted</li>
          <li>• Answer based on how you've felt over the past month</li>
          <li>• Be honest - there are no "good" or "bad" answers</li>
          <li>• Don't overthink - go with your first instinct</li>
          <li>• Take your time - there's no rush</li>
        </ul>
      </div>
    </div>
  );
};

export default StressTestIntro;

