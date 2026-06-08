// apps/web/frontend/components/dashboard/FocusModeQuestionnaire.jsx
import React, { useState } from 'react';
import { X } from 'lucide-react';
import CircularProgress from './CircularProgress';
import FocusModeResult from './FocusModeResult';

// All 11 questions organized by category
const questions = [
  // Category 1: Energy & Focus (Q1-3)
  {
    id: 1,
    category: 'Energy & Focus',
    question: 'How would you describe your energy levels during work hours?',
    options: [
      { value: 4, label: 'Very high and consistent' },
      { value: 3, label: 'Good but dips during the day' },
      { value: 2, label: 'Low most of the time' },
      { value: 1, label: 'Very inconsistent' },
    ],
  },
  {
    id: 2,
    category: 'Energy & Focus',
    question: 'How often do you feel fully focused while working?',
    options: [
      { value: 4, label: 'Most of the day' },
      { value: 3, label: 'A few productive hours' },
      { value: 2, label: 'Rarely' },
      { value: 1, label: 'Almost never' },
    ],
  },
  {
    id: 3,
    category: 'Energy & Focus',
    question: 'At what time do you feel most productive?',
    options: [
      { value: 4, label: 'Early morning' },
      { value: 3, label: 'Mid-day' },
      { value: 2, label: 'Evening' },
      { value: 1, label: 'Productivity varies daily' },
    ],
  },
  // Category 2: Mood & Emotional State (Q4-5)
  {
    id: 4,
    category: 'Mood & Emotional State',
    question: 'How would you describe your general mood on workdays?',
    options: [
      { value: 4, label: 'Calm and positive' },
      { value: 3, label: 'Mostly fine with occasional stress' },
      { value: 2, label: 'Frequently stressed or anxious' },
      { value: 1, label: 'Drained or overwhelmed' },
    ],
  },
  {
    id: 5,
    category: 'Mood & Emotional State',
    question: 'How often do work-related thoughts affect your mood outside work hours?',
    options: [
      { value: 4, label: 'Rarely' },
      { value: 3, label: 'Sometimes' },
      { value: 2, label: 'Often' },
      { value: 1, label: 'Almost always' },
    ],
  },
  // Category 3: Stress & Mental Load (Q6-7)
  {
    id: 6,
    category: 'Stress & Mental Load',
    question: 'How do you usually feel at the end of a workday?',
    options: [
      { value: 4, label: 'Energized' },
      { value: 3, label: 'Neutral' },
      { value: 2, label: 'Mentally tired' },
      { value: 1, label: 'Completely exhausted' },
    ],
  },
  {
    id: 7,
    category: 'Stress & Mental Load',
    question: 'How well do you disconnect from work after office hours?',
    options: [
      { value: 4, label: 'Very well' },
      { value: 3, label: 'Fairly well' },
      { value: 2, label: 'Struggle often' },
      { value: 1, label: 'Cannot disconnect' },
    ],
  },
  // Category 4: Work-Life Balance (Q8-9)
  {
    id: 8,
    category: 'Work-Life Balance',
    question: 'How balanced does your work and personal life feel currently?',
    options: [
      { value: 4, label: 'Very balanced' },
      { value: 3, label: 'Mostly balanced' },
      { value: 2, label: 'Slightly imbalanced' },
      { value: 1, label: 'Highly imbalanced' },
    ],
  },
  {
    id: 9,
    category: 'Work-Life Balance',
    question: 'How much personal time do you get on weekdays?',
    options: [
      { value: 4, label: 'Enough time' },
      { value: 3, label: 'Some time' },
      { value: 2, label: 'Very little time' },
      { value: 1, label: 'Almost none' },
    ],
  },
  // Category 5: Lifestyle Signals (Q10-11)
  {
    id: 10,
    category: 'Lifestyle Signals',
    question: 'How would you rate your sleep quality on most nights?',
    options: [
      { value: 4, label: 'Refreshing' },
      { value: 3, label: 'Adequate' },
      { value: 2, label: 'Disturbed' },
      { value: 1, label: 'Poor' },
    ],
  },
  {
    id: 11,
    category: 'Lifestyle Signals',
    question: 'How often do you feel physically tired during the day?',
    options: [
      { value: 4, label: 'Rarely' },
      { value: 3, label: 'Sometimes' },
      { value: 2, label: 'Often' },
      { value: 1, label: 'Almost always' },
    ],
  },
];

export default function FocusModeQuestionnaire({ onClose }) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);

  const totalQuestions = questions.length;
  const currentQuestion = questions[currentQuestionIndex];
  const answeredCount = Object.keys(answers).length;

  const handleOptionSelect = (questionId, value) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value,
    }));
  };

  const handleNext = () => {
    if (currentQuestionIndex < totalQuestions - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      // All questions answered, show results
      setShowResults(true);
    }
  };

  const handleBack = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  const handleRetake = () => {
    setAnswers({});
    setCurrentQuestionIndex(0);
    setShowResults(false);
  };

  const isCurrentAnswered = answers[currentQuestion?.id] !== undefined;
  const isLastQuestion = currentQuestionIndex === totalQuestions - 1;

  if (showResults) {
    return (
      <FocusModeResult 
        answers={answers} 
        questions={questions}
        onClose={onClose}
        onRetake={handleRetake}
        isContained={true}
      />
    );
  }

  return (
    <div 
      className="relative rounded-2xl overflow-hidden"
      style={{
        background: 'linear-gradient(180deg, #050d1a 0%, #0a1628 50%, #0f1d32 100%)',
        minHeight: '600px',
      }}
    >
      {/* Subtle blue glow effects */}
      <div 
        className="absolute top-0 left-1/4 w-[400px] h-[400px] rounded-full opacity-20 pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(59, 130, 246, 0.4) 0%, transparent 70%)',
          filter: 'blur(60px)',
        }}
      />
      <div 
        className="absolute bottom-0 right-1/4 w-[300px] h-[300px] rounded-full opacity-15 pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.4) 0%, transparent 70%)',
          filter: 'blur(50px)',
        }}
      />

      {/* Close button - centered at top */}
      <div className="flex justify-center pt-6">
        <button
          onClick={onClose}
          className="w-10 h-10 rounded-full bg-[#1e293b] border border-[#334155] flex items-center justify-center hover:bg-[#334155] transition-colors"
        >
          <X className="w-4 h-4 text-white/70" />
        </button>
      </div>

      {/* Main content */}
      <div className="relative z-10 flex flex-col lg:flex-row items-center justify-center gap-8 px-8 py-8">
        {/* Question Card */}
        <div 
          className="rounded-2xl p-6 w-full max-w-[460px]"
          style={{
            background: 'linear-gradient(180deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)',
            border: '1px solid rgba(71, 85, 105, 0.3)',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          }}
        >
          {/* Title */}
          <h2 className="text-xl font-bold text-white mb-5">
            Focus Mode Questionnaire
          </h2>

          {/* Question */}
          <p className="text-white/90 text-base mb-5 leading-relaxed">
            {currentQuestion.question}
          </p>

          {/* Options */}
          <div className="space-y-2.5 mb-6">
            {currentQuestion.options.map((option, index) => {
              const isSelected = answers[currentQuestion.id] === option.value;
              
              return (
                <button
                  key={index}
                  onClick={() => handleOptionSelect(currentQuestion.id, option.value)}
                  className={`
                    w-full flex items-center gap-3 p-3.5 rounded-xl text-left transition-all duration-200
                    ${isSelected 
                      ? 'bg-[#3b82f6]/20 border-[#3b82f6]/50' 
                      : 'bg-[#1e293b]/50 border-[#334155]/50 hover:bg-[#1e293b]/80'
                    }
                    border
                  `}
                >
                  {/* Custom checkbox - matching Figma (light purple/blue square) */}
                  <div 
                    className={`
                      w-5 h-5 rounded flex items-center justify-center transition-all shrink-0
                      ${isSelected 
                        ? 'bg-[#6366f1]' 
                        : 'bg-[#475569]/60'
                      }
                    `}
                  >
                    {isSelected && (
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                  <span className="text-white/80 text-sm">{option.label}</span>
                </button>
              );
            })}
          </div>

          {/* Navigation buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleBack}
              disabled={currentQuestionIndex === 0}
              className={`
                flex-1 py-3 px-5 rounded-xl font-medium text-sm transition-all duration-200
                ${currentQuestionIndex === 0
                  ? 'bg-[#1e293b]/50 text-white/30 cursor-not-allowed border border-[#334155]/30'
                  : 'bg-[#1e293b] text-white border border-[#475569] hover:bg-[#334155]'
                }
              `}
            >
              Back
            </button>
            <button
              onClick={handleNext}
              disabled={!isCurrentAnswered}
              className={`
                flex-1 py-3 px-5 rounded-xl font-medium text-sm transition-all duration-200
                ${isCurrentAnswered
                  ? 'bg-[#6366f1] text-white hover:bg-[#4f46e5] shadow-lg shadow-[#6366f1]/25'
                  : 'bg-[#6366f1]/40 text-white/50 cursor-not-allowed'
                }
              `}
            >
              {isLastQuestion ? 'See Results' : 'Next'}
            </button>
          </div>
        </div>

        {/* Circular Progress */}
        <CircularProgress 
          current={answeredCount} 
          total={totalQuestions}
          size={180}
          strokeWidth={12}
        />
      </div>
    </div>
  );
}
