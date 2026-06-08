// apps/web/frontend/components/dashboard/tools/BreathingExercise.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, ChevronDown } from 'lucide-react';

const BREATHING_TECHNIQUES = {
  'box': {
    name: 'Box Breathing',
    description: 'Equal parts inhale, hold, exhale, hold. Great for stress relief.',
    phases: [
      { name: 'Inhale', duration: 4, color: '#3b82f6' },
      { name: 'Hold', duration: 4, color: '#8b5cf6' },
      { name: 'Exhale', duration: 4, color: '#06b6d4' },
      { name: 'Hold', duration: 4, color: '#10b981' },
    ],
    cycles: 4
  },
  '478': {
    name: '4-7-8 Breathing',
    description: 'Calming technique for anxiety and sleep. Inhale 4, hold 7, exhale 8.',
    phases: [
      { name: 'Inhale', duration: 4, color: '#3b82f6' },
      { name: 'Hold', duration: 7, color: '#8b5cf6' },
      { name: 'Exhale', duration: 8, color: '#06b6d4' },
    ],
    cycles: 4
  },
  'deep': {
    name: 'Deep Breathing',
    description: 'Simple deep breaths for relaxation and oxygen boost.',
    phases: [
      { name: 'Inhale', duration: 5, color: '#3b82f6' },
      { name: 'Exhale', duration: 5, color: '#06b6d4' },
    ],
    cycles: 6
  },
  'energizing': {
    name: 'Energizing Breath',
    description: 'Quick breaths to boost energy and alertness.',
    phases: [
      { name: 'Inhale', duration: 2, color: '#f97316' },
      { name: 'Exhale', duration: 2, color: '#eab308' },
    ],
    cycles: 10
  }
};

export default function BreathingExercise({ onComplete }) {
  const [selectedTechnique, setSelectedTechnique] = useState('box');
  const [isRunning, setIsRunning] = useState(false);
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);
  const [currentCycle, setCurrentCycle] = useState(1);
  const [timeLeft, setTimeLeft] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);
  const [showTechniqueDropdown, setShowTechniqueDropdown] = useState(false);
  
  const intervalRef = useRef(null);
  const technique = BREATHING_TECHNIQUES[selectedTechnique];
  const currentPhase = technique.phases[currentPhaseIndex];
  const totalPhases = technique.phases.length;
  
  // Calculate progress for the circle animation
  const progress = currentPhase ? (currentPhase.duration - timeLeft) / currentPhase.duration : 0;
  const circleScale = currentPhase?.name === 'Inhale' ? 1 + (progress * 0.3) : 
                      currentPhase?.name === 'Exhale' ? 1.3 - (progress * 0.3) : 1.15;

  useEffect(() => {
    if (isRunning && !isCompleted) {
      intervalRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            // Move to next phase
            const nextPhaseIndex = (currentPhaseIndex + 1) % totalPhases;
            
            if (nextPhaseIndex === 0) {
              // Completed a cycle
              if (currentCycle >= technique.cycles) {
                // All cycles complete
                setIsRunning(false);
                setIsCompleted(true);
                onComplete?.();
                return 0;
              }
              setCurrentCycle(c => c + 1);
            }
            
            setCurrentPhaseIndex(nextPhaseIndex);
            return technique.phases[nextPhaseIndex].duration;
          }
          return prev - 1;
        });
      }, 1000);
    }
    
    return () => clearInterval(intervalRef.current);
  }, [isRunning, currentPhaseIndex, currentCycle, technique, totalPhases, isCompleted, onComplete]);

  const handleStart = () => {
    if (isCompleted) {
      handleReset();
    }
    setIsRunning(true);
    if (timeLeft === 0) {
      setTimeLeft(currentPhase.duration);
    }
  };

  const handlePause = () => {
    setIsRunning(false);
  };

  const handleReset = () => {
    setIsRunning(false);
    setCurrentPhaseIndex(0);
    setCurrentCycle(1);
    setTimeLeft(0);
    setIsCompleted(false);
  };

  const handleTechniqueChange = (key) => {
    handleReset();
    setSelectedTechnique(key);
    setShowTechniqueDropdown(false);
  };

  return (
    <div className="flex flex-col items-center">
      {/* Technique Selector */}
      <div className="relative mb-6 w-full max-w-xs">
        <button
          onClick={() => setShowTechniqueDropdown(!showTechniqueDropdown)}
          className="w-full px-4 py-3 bg-white border border-gray-200 rounded-xl flex items-center justify-between hover:border-blue-300 transition-colors"
        >
          <span className="font-medium text-gray-800">{technique.name}</span>
          <ChevronDown className={`w-5 h-5 text-gray-500 transition-transform ${showTechniqueDropdown ? 'rotate-180' : ''}`} />
        </button>
        
        {showTechniqueDropdown && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-xl shadow-lg z-10 overflow-hidden">
            {Object.entries(BREATHING_TECHNIQUES).map(([key, tech]) => (
              <button
                key={key}
                onClick={() => handleTechniqueChange(key)}
                className={`w-full px-4 py-3 text-left hover:bg-blue-50 transition-colors ${
                  selectedTechnique === key ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
                }`}
              >
                <div className="font-medium">{tech.name}</div>
                <div className="text-xs text-gray-500">{tech.description}</div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Description */}
      <p className="text-sm text-gray-500 text-center mb-8 max-w-md">
        {technique.description}
      </p>

      {/* Breathing Circle Animation */}
      <div className="relative mb-8">
        <div 
          className="w-64 h-64 rounded-full flex items-center justify-center transition-all duration-1000 ease-in-out"
          style={{
            transform: `scale(${circleScale})`,
            background: `radial-gradient(circle, ${currentPhase?.color || '#3b82f6'}20 0%, ${currentPhase?.color || '#3b82f6'}40 100%)`,
            boxShadow: `0 0 60px ${currentPhase?.color || '#3b82f6'}40`
          }}
        >
          <div 
            className="w-48 h-48 rounded-full flex flex-col items-center justify-center bg-white shadow-lg"
          >
            <span 
              className="text-4xl font-bold transition-colors duration-500"
              style={{ color: currentPhase?.color || '#3b82f6' }}
            >
              {timeLeft || currentPhase?.duration || '-'}
            </span>
            <span 
              className="text-lg font-medium mt-1 transition-colors duration-500"
              style={{ color: currentPhase?.color || '#3b82f6' }}
            >
              {isCompleted ? 'Complete!' : (currentPhase?.name || 'Ready')}
            </span>
          </div>
        </div>
        
        {/* Phase indicators */}
        <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
          {technique.phases.map((phase, idx) => (
            <div
              key={idx}
              className="w-3 h-3 rounded-full transition-all duration-300"
              style={{
                backgroundColor: idx === currentPhaseIndex ? phase.color : '#e5e7eb',
                transform: idx === currentPhaseIndex ? 'scale(1.3)' : 'scale(1)'
              }}
            />
          ))}
        </div>
      </div>

      {/* Cycle Counter */}
      <div className="text-center mb-6">
        <span className="text-sm text-gray-500">
          Cycle {currentCycle} of {technique.cycles}
        </span>
        <div className="flex gap-1 justify-center mt-2">
          {Array.from({ length: technique.cycles }).map((_, idx) => (
            <div
              key={idx}
              className={`w-2 h-2 rounded-full transition-colors ${
                idx < currentCycle ? 'bg-green-500' : 'bg-gray-200'
              }`}
            />
          ))}
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
            {isCompleted ? 'Restart' : (timeLeft > 0 ? 'Resume' : 'Start')}
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

      {/* Completion Message */}
      {isCompleted && (
        <div className="mt-8 text-center">
          <div className="text-2xl mb-2">🎉</div>
          <p className="text-green-600 font-medium">Great job! You completed the exercise.</p>
          <p className="text-sm text-gray-500 mt-1">Take a moment to notice how you feel.</p>
        </div>
      )}
    </div>
  );
}

