// apps/web/frontend/components/dashboard/tools/EyeRestExercise.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, Eye, EyeOff } from 'lucide-react';

const EYE_EXERCISES = {
  '20-20-20': {
    name: '20-20-20 Rule',
    description: 'Every 20 minutes, look at something 20 feet away for 20 seconds.',
    duration: 20,
    icon: '👀',
    instructions: 'Look at an object at least 20 feet (6 meters) away'
  },
  'palming': {
    name: 'Palming',
    description: 'Cover eyes with palms to relax eye muscles and reduce strain.',
    duration: 60,
    icon: '🙌',
    instructions: 'Cup your palms over closed eyes without pressing'
  },
  'blinking': {
    name: 'Rapid Blinking',
    description: 'Conscious blinking to refresh tear film and reduce dryness.',
    duration: 30,
    icon: '😌',
    instructions: 'Blink rapidly for 20 seconds, then rest with eyes closed'
  },
  'focus-shift': {
    name: 'Focus Shifting',
    description: 'Alternate focus between near and far objects to exercise eye muscles.',
    duration: 45,
    icon: '🎯',
    instructions: 'Hold thumb 10 inches away, focus on it, then focus on distant object. Repeat.'
  }
};

export default function EyeRestExercise({ onComplete }) {
  const [selectedExercise, setSelectedExercise] = useState('20-20-20');
  const [isRunning, setIsRunning] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);
  const [sessionsCompleted, setSessionsCompleted] = useState(0);
  
  const intervalRef = useRef(null);
  const exercise = EYE_EXERCISES[selectedExercise];
  const progress = timeLeft > 0 ? ((exercise.duration - timeLeft) / exercise.duration) * 100 : 0;

  useEffect(() => {
    if (isRunning && timeLeft > 0) {
      intervalRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            setIsRunning(false);
            setIsCompleted(true);
            setSessionsCompleted(s => s + 1);
            onComplete?.();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    
    return () => clearInterval(intervalRef.current);
  }, [isRunning, timeLeft, onComplete]);

  const handleStart = () => {
    setIsCompleted(false);
    setIsRunning(true);
    setTimeLeft(exercise.duration);
  };

  const handlePause = () => {
    setIsRunning(false);
  };

  const handleResume = () => {
    setIsRunning(true);
  };

  const handleReset = () => {
    setIsRunning(false);
    setTimeLeft(0);
    setIsCompleted(false);
  };

  const handleExerciseChange = (key) => {
    handleReset();
    setSelectedExercise(key);
  };

  return (
    <div className="flex flex-col items-center">
      {/* Exercise Selector */}
      <div className="grid grid-cols-2 gap-3 mb-6 w-full max-w-md">
        {Object.entries(EYE_EXERCISES).map(([key, ex]) => (
          <button
            key={key}
            onClick={() => handleExerciseChange(key)}
            className={`p-4 rounded-xl text-left transition-all ${
              selectedExercise === key
                ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30'
                : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
            }`}
          >
            <span className="text-2xl mb-2 block">{ex.icon}</span>
            <span className="font-medium text-sm">{ex.name}</span>
          </button>
        ))}
      </div>

      {/* Description */}
      <p className="text-sm text-gray-500 text-center mb-8 max-w-md">
        {exercise.description}
      </p>

      {/* Timer Circle */}
      <div className="relative mb-8">
        <svg width="280" height="280" className="transform -rotate-90">
          <circle
            cx="140"
            cy="140"
            r="120"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="12"
          />
          <circle
            cx="140"
            cy="140"
            r="120"
            fill="none"
            stroke="url(#eyeGradient)"
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={2 * Math.PI * 120}
            strokeDashoffset={2 * Math.PI * 120 * (1 - progress / 100)}
            className="transition-all duration-1000"
          />
          <defs>
            <linearGradient id="eyeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#6366f1" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
          </defs>
        </svg>
        
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {isRunning ? (
            <Eye className="w-12 h-12 text-indigo-500 mb-2 animate-pulse" />
          ) : isCompleted ? (
            <EyeOff className="w-12 h-12 text-green-500 mb-2" />
          ) : (
            <Eye className="w-12 h-12 text-gray-400 mb-2" />
          )}
          <span className="text-5xl font-bold text-gray-800">
            {timeLeft || exercise.duration}
          </span>
          <span className="text-sm text-gray-500 mt-1">seconds</span>
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 mb-6 max-w-md text-center">
        <p className="text-indigo-700 text-sm">
          {isRunning ? exercise.instructions : isCompleted ? '✨ Great job! Your eyes thank you.' : 'Press Start to begin'}
        </p>
      </div>

      {/* Controls */}
      <div className="flex gap-4">
        {!isRunning && !isCompleted && (
          <button
            onClick={handleStart}
            className="flex items-center gap-2 px-8 py-3 bg-indigo-500 text-white rounded-full font-medium hover:bg-indigo-600 transition-colors shadow-lg shadow-indigo-500/30"
          >
            <Play className="w-5 h-5" />
            Start
          </button>
        )}
        
        {isRunning && (
          <button
            onClick={handlePause}
            className="flex items-center gap-2 px-8 py-3 bg-orange-500 text-white rounded-full font-medium hover:bg-orange-600 transition-colors shadow-lg shadow-orange-500/30"
          >
            <Pause className="w-5 h-5" />
            Pause
          </button>
        )}
        
        {!isRunning && timeLeft > 0 && !isCompleted && (
          <button
            onClick={handleResume}
            className="flex items-center gap-2 px-8 py-3 bg-indigo-500 text-white rounded-full font-medium hover:bg-indigo-600 transition-colors shadow-lg shadow-indigo-500/30"
          >
            <Play className="w-5 h-5" />
            Resume
          </button>
        )}
        
        {isCompleted && (
          <button
            onClick={handleStart}
            className="flex items-center gap-2 px-8 py-3 bg-green-500 text-white rounded-full font-medium hover:bg-green-600 transition-colors shadow-lg shadow-green-500/30"
          >
            <RotateCcw className="w-5 h-5" />
            Do Again
          </button>
        )}
        
        {(isRunning || timeLeft > 0) && (
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-full font-medium hover:bg-gray-200 transition-colors"
          >
            <RotateCcw className="w-5 h-5" />
            Reset
          </button>
        )}
      </div>

      {/* Sessions Counter */}
      {sessionsCompleted > 0 && (
        <div className="mt-6 text-center">
          <span className="text-sm text-gray-500">
            Sessions completed today: <span className="font-bold text-indigo-600">{sessionsCompleted}</span>
          </span>
        </div>
      )}
    </div>
  );
}

