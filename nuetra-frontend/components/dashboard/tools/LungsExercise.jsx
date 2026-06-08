// apps/web/frontend/components/dashboard/tools/LungsExercise.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, Trophy, TrendingUp } from 'lucide-react';

const LUNG_EXERCISES = {
  'pursed-lip': {
    name: 'Pursed Lip Breathing',
    description: 'Breathe in through nose, out through pursed lips. Strengthens breathing muscles.',
    inhaleTime: 2,
    exhaleTime: 4,
    rounds: 10,
    tip: 'Purse your lips as if blowing out a candle'
  },
  'diaphragmatic': {
    name: 'Diaphragmatic Breathing',
    description: 'Deep belly breathing to strengthen the diaphragm and increase lung capacity.',
    inhaleTime: 4,
    exhaleTime: 6,
    rounds: 8,
    tip: 'Place hand on belly - it should rise as you inhale'
  },
  'breath-hold': {
    name: 'Breath Hold Training',
    description: 'Gradually increase breath holding time to improve lung capacity.',
    inhaleTime: 4,
    holdTime: 10,
    exhaleTime: 4,
    rounds: 5,
    tip: 'Try to increase hold time each round'
  },
  'counting': {
    name: 'Counting Breath',
    description: 'Inhale while counting to 4, exhale counting to 8. Builds control.',
    inhaleTime: 4,
    exhaleTime: 8,
    rounds: 6,
    tip: 'Count slowly and steadily'
  }
};

// Animated Lung SVG Component
function AnimatedLungs({ phase, progress }) {
  const scale = phase === 'inhale' ? 0.8 + (progress * 0.2) : 
                phase === 'exhale' ? 1 - (progress * 0.2) : 0.9;
  const color = phase === 'inhale' ? '#3b82f6' : 
                phase === 'exhale' ? '#06b6d4' : '#8b5cf6';

  return (
    <svg 
      width="200" 
      height="200" 
      viewBox="0 0 200 200"
      className="transition-transform duration-500"
      style={{ transform: `scale(${scale})` }}
    >
      {/* Trachea */}
      <path
        d="M100 20 L100 60"
        stroke={color}
        strokeWidth="8"
        strokeLinecap="round"
        fill="none"
      />
      {/* Bronchi */}
      <path
        d="M100 60 Q80 80 60 100"
        stroke={color}
        strokeWidth="6"
        fill="none"
      />
      <path
        d="M100 60 Q120 80 140 100"
        stroke={color}
        strokeWidth="6"
        fill="none"
      />
      {/* Left Lung */}
      <ellipse
        cx="55"
        cy="130"
        rx="40"
        ry="55"
        fill={`${color}30`}
        stroke={color}
        strokeWidth="3"
      />
      {/* Right Lung */}
      <ellipse
        cx="145"
        cy="130"
        rx="40"
        ry="55"
        fill={`${color}30`}
        stroke={color}
        strokeWidth="3"
      />
      {/* Lung details - left */}
      <path
        d="M35 110 Q55 115 45 140 Q55 145 40 160"
        stroke={color}
        strokeWidth="2"
        fill="none"
        opacity="0.5"
      />
      {/* Lung details - right */}
      <path
        d="M165 110 Q145 115 155 140 Q145 145 160 160"
        stroke={color}
        strokeWidth="2"
        fill="none"
        opacity="0.5"
      />
    </svg>
  );
}

export default function LungsExercise({ onComplete }) {
  const [selectedExercise, setSelectedExercise] = useState('pursed-lip');
  const [isRunning, setIsRunning] = useState(false);
  const [phase, setPhase] = useState('ready'); // ready, inhale, hold, exhale
  const [timeLeft, setTimeLeft] = useState(0);
  const [currentRound, setCurrentRound] = useState(1);
  const [isCompleted, setIsCompleted] = useState(false);
  const [totalTime, setTotalTime] = useState(0);
  const [bestHoldTime, setBestHoldTime] = useState(0);
  
  const intervalRef = useRef(null);
  const exercise = LUNG_EXERCISES[selectedExercise];

  const getPhaseColor = () => {
    switch (phase) {
      case 'inhale': return '#3b82f6';
      case 'hold': return '#8b5cf6';
      case 'exhale': return '#06b6d4';
      default: return '#6b7280';
    }
  };

  const getNextPhase = () => {
    if (phase === 'inhale') {
      return exercise.holdTime ? 'hold' : 'exhale';
    }
    if (phase === 'hold') return 'exhale';
    if (phase === 'exhale') return 'inhale';
    return 'inhale';
  };

  const getPhaseTime = (p) => {
    switch (p) {
      case 'inhale': return exercise.inhaleTime;
      case 'hold': return exercise.holdTime || 0;
      case 'exhale': return exercise.exhaleTime;
      default: return 0;
    }
  };

  useEffect(() => {
    if (isRunning && !isCompleted) {
      intervalRef.current = setInterval(() => {
        setTimeLeft(prev => {
          setTotalTime(t => t + 1);
          
          if (prev <= 1) {
            const nextPhase = getNextPhase();
            
            // Track best hold time
            if (phase === 'hold' && timeLeft > bestHoldTime) {
              setBestHoldTime(timeLeft);
            }
            
            // Check if we completed a full breath cycle
            if (phase === 'exhale') {
              if (currentRound >= exercise.rounds) {
                setIsRunning(false);
                setIsCompleted(true);
                setPhase('ready');
                onComplete?.();
                return 0;
              }
              setCurrentRound(r => r + 1);
            }
            
            setPhase(nextPhase);
            return getPhaseTime(nextPhase);
          }
          return prev - 1;
        });
      }, 1000);
    }
    
    return () => clearInterval(intervalRef.current);
  }, [isRunning, phase, currentRound, exercise, isCompleted, bestHoldTime, onComplete]);

  const handleStart = () => {
    if (isCompleted) {
      handleReset();
    }
    setIsRunning(true);
    if (phase === 'ready') {
      setPhase('inhale');
      setTimeLeft(exercise.inhaleTime);
    }
  };

  const handlePause = () => {
    setIsRunning(false);
  };

  const handleReset = () => {
    setIsRunning(false);
    setPhase('ready');
    setTimeLeft(0);
    setCurrentRound(1);
    setIsCompleted(false);
    setTotalTime(0);
  };

  const handleExerciseChange = (key) => {
    handleReset();
    setSelectedExercise(key);
  };

  const progress = timeLeft > 0 ? (getPhaseTime(phase) - timeLeft) / getPhaseTime(phase) : 0;

  return (
    <div className="flex flex-col items-center">
      {/* Exercise Selector */}
      <div className="flex flex-wrap gap-2 justify-center mb-6">
        {Object.entries(LUNG_EXERCISES).map(([key, ex]) => (
          <button
            key={key}
            onClick={() => handleExerciseChange(key)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
              selectedExercise === key
                ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {ex.name}
          </button>
        ))}
      </div>

      {/* Description */}
      <p className="text-sm text-gray-500 text-center mb-2 max-w-md">
        {exercise.description}
      </p>
      <p className="text-xs text-blue-500 text-center mb-6 max-w-md italic">
        💡 {exercise.tip}
      </p>

      {/* Animated Lungs */}
      <div className="relative mb-6">
        <div 
          className="p-8 rounded-full transition-all duration-500"
          style={{
            background: `radial-gradient(circle, ${getPhaseColor()}10 0%, ${getPhaseColor()}20 100%)`,
            boxShadow: isRunning ? `0 0 40px ${getPhaseColor()}30` : 'none'
          }}
        >
          <AnimatedLungs phase={phase} progress={progress} />
        </div>
      </div>

      {/* Phase Display */}
      <div className="text-center mb-6">
        <div 
          className="text-5xl font-bold mb-2 transition-colors duration-300"
          style={{ color: getPhaseColor() }}
        >
          {timeLeft || '-'}
        </div>
        <div 
          className="text-xl font-medium capitalize transition-colors duration-300"
          style={{ color: getPhaseColor() }}
        >
          {phase === 'ready' ? 'Ready to Start' : phase}
        </div>
      </div>

      {/* Progress */}
      <div className="w-full max-w-xs mb-6">
        <div className="flex justify-between text-sm text-gray-500 mb-2">
          <span>Round {currentRound} of {exercise.rounds}</span>
          <span>{Math.floor(totalTime / 60)}:{(totalTime % 60).toString().padStart(2, '0')}</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-300"
            style={{ width: `${(currentRound / exercise.rounds) * 100}%` }}
          />
        </div>
      </div>

      {/* Controls */}
      <div className="flex gap-4">
        {!isRunning ? (
          <button
            onClick={handleStart}
            className="flex items-center gap-2 px-8 py-3 bg-blue-500 text-white rounded-full font-medium hover:bg-blue-600 transition-colors shadow-lg shadow-blue-500/30"
          >
            <Play className="w-5 h-5" />
            {isCompleted ? 'Restart' : (phase !== 'ready' ? 'Resume' : 'Start')}
          </button>
        ) : (
          <button
            onClick={handlePause}
            className="flex items-center gap-2 px-8 py-3 bg-orange-500 text-white rounded-full font-medium hover:bg-orange-600 transition-colors shadow-lg shadow-orange-500/30"
          >
            <Pause className="w-5 h-5" />
            Pause
          </button>
        )}
        
        <button
          onClick={handleReset}
          className="flex items-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-full font-medium hover:bg-gray-200 transition-colors"
        >
          <RotateCcw className="w-5 h-5" />
          Reset
        </button>
      </div>

      {/* Completion Stats */}
      {isCompleted && (
        <div className="mt-8 p-6 bg-gradient-to-r from-green-50 to-cyan-50 rounded-2xl border border-green-200">
          <div className="flex items-center gap-2 justify-center mb-4">
            <Trophy className="w-6 h-6 text-yellow-500" />
            <span className="text-lg font-semibold text-green-700">Exercise Complete!</span>
          </div>
          <div className="flex gap-6 justify-center">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-800">{exercise.rounds}</div>
              <div className="text-xs text-gray-500">Rounds</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-800">
                {Math.floor(totalTime / 60)}:{(totalTime % 60).toString().padStart(2, '0')}
              </div>
              <div className="text-xs text-gray-500">Total Time</div>
            </div>
            {exercise.holdTime && (
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-800">{exercise.holdTime}s</div>
                <div className="text-xs text-gray-500">Breath Hold</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

