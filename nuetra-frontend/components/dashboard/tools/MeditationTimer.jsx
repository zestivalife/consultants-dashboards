// apps/web/frontend/components/dashboard/tools/MeditationTimer.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, Volume2, VolumeX } from 'lucide-react';

const MEDITATION_PRESETS = [
  { minutes: 2, label: '2 min', description: 'Quick reset' },
  { minutes: 5, label: '5 min', description: 'Short break' },
  { minutes: 10, label: '10 min', description: 'Deep focus' },
  { minutes: 15, label: '15 min', description: 'Full session' },
  { minutes: 20, label: '20 min', description: 'Extended' },
];

const AMBIENT_SOUNDS = [
  { id: 'none', name: 'Silence', icon: '🔇' },
  { id: 'rain', name: 'Rain', icon: '🌧️' },
  { id: 'forest', name: 'Forest', icon: '🌲' },
  { id: 'waves', name: 'Waves', icon: '🌊' },
  { id: 'fire', name: 'Fireplace', icon: '🔥' },
];

export default function MeditationTimer({ onComplete }) {
  const [selectedMinutes, setSelectedMinutes] = useState(5);
  const [selectedSound, setSelectedSound] = useState('none');
  const [isRunning, setIsRunning] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  
  const intervalRef = useRef(null);
  const totalSeconds = selectedMinutes * 60;
  const progress = timeLeft > 0 ? ((totalSeconds - timeLeft) / totalSeconds) * 100 : 0;

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    if (isRunning && timeLeft > 0) {
      intervalRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            setIsRunning(false);
            setIsCompleted(true);
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
    if (timeLeft === 0) {
      setTimeLeft(totalSeconds);
    }
  };

  const handlePause = () => {
    setIsRunning(false);
  };

  const handleReset = () => {
    setIsRunning(false);
    setTimeLeft(0);
    setIsCompleted(false);
  };

  const handlePresetChange = (minutes) => {
    handleReset();
    setSelectedMinutes(minutes);
  };

  // Breathing animation sync (8 second cycle)
  const breathingPhase = Math.floor((Date.now() / 1000) % 8);
  const isInhaling = breathingPhase < 4;

  return (
    <div className="flex flex-col items-center">
      {/* Time Presets */}
      <div className="flex gap-2 mb-6 flex-wrap justify-center">
        {MEDITATION_PRESETS.map((preset) => (
          <button
            key={preset.minutes}
            onClick={() => handlePresetChange(preset.minutes)}
            disabled={isRunning}
            className={`px-4 py-3 rounded-xl transition-all ${
              selectedMinutes === preset.minutes
                ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/30'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50'
            }`}
          >
            <div className="font-bold">{preset.label}</div>
            <div className="text-xs opacity-80">{preset.description}</div>
          </button>
        ))}
      </div>

      {/* Ambient Sound Selector */}
      <div className="flex gap-2 mb-8">
        {AMBIENT_SOUNDS.map((sound) => (
          <button
            key={sound.id}
            onClick={() => setSelectedSound(sound.id)}
            className={`p-3 rounded-full transition-all ${
              selectedSound === sound.id
                ? 'bg-purple-100 ring-2 ring-purple-500'
                : 'bg-gray-100 hover:bg-gray-200'
            }`}
            title={sound.name}
          >
            <span className="text-xl">{sound.icon}</span>
          </button>
        ))}
        <button
          onClick={() => setIsMuted(!isMuted)}
          className={`p-3 rounded-full transition-all ${
            isMuted ? 'bg-red-100 text-red-500' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
          }`}
        >
          {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
        </button>
      </div>

      {/* Meditation Circle */}
      <div className="relative mb-8">
        {/* Outer breathing ring */}
        <div 
          className={`absolute inset-0 rounded-full transition-all duration-[4000ms] ease-in-out ${
            isRunning ? (isInhaling ? 'scale-110 opacity-40' : 'scale-100 opacity-20') : 'scale-100 opacity-0'
          }`}
          style={{
            background: 'radial-gradient(circle, rgba(147, 51, 234, 0.3) 0%, transparent 70%)',
          }}
        />
        
        <svg width="300" height="300" className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx="150"
            cy="150"
            r="130"
            fill="none"
            stroke="#f3e8ff"
            strokeWidth="16"
          />
          {/* Progress circle */}
          <circle
            cx="150"
            cy="150"
            r="130"
            fill="none"
            stroke="url(#meditationGradient)"
            strokeWidth="16"
            strokeLinecap="round"
            strokeDasharray={2 * Math.PI * 130}
            strokeDashoffset={2 * Math.PI * 130 * (1 - progress / 100)}
            className="transition-all duration-1000"
          />
          <defs>
            <linearGradient id="meditationGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#9333ea" />
              <stop offset="50%" stopColor="#a855f7" />
              <stop offset="100%" stopColor="#c084fc" />
            </linearGradient>
          </defs>
        </svg>
        
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-6xl font-light text-gray-800">
            {formatTime(timeLeft || totalSeconds)}
          </span>
          <span className="text-sm text-gray-500 mt-2">
            {isRunning ? (isInhaling ? 'Breathe in...' : 'Breathe out...') : 
             isCompleted ? 'Namaste 🙏' : 'Find your peace'}
          </span>
        </div>
      </div>

      {/* Breathing Guide */}
      {isRunning && (
        <div className="mb-6 text-center">
          <div className="flex items-center gap-4 justify-center">
            <div 
              className={`w-4 h-4 rounded-full transition-all duration-[4000ms] ${
                isInhaling ? 'bg-purple-500 scale-150' : 'bg-purple-300 scale-100'
              }`}
            />
            <span className="text-sm text-gray-500">
              {isInhaling ? 'Expanding...' : 'Releasing...'}
            </span>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="flex gap-4">
        {!isRunning ? (
          <button
            onClick={handleStart}
            className="flex items-center gap-2 px-10 py-4 bg-purple-500 text-white rounded-full font-medium hover:bg-purple-600 transition-colors shadow-lg shadow-purple-500/30"
          >
            <Play className="w-5 h-5" />
            {isCompleted ? 'Meditate Again' : (timeLeft > 0 ? 'Resume' : 'Begin')}
          </button>
        ) : (
          <button
            onClick={handlePause}
            className="flex items-center gap-2 px-10 py-4 bg-orange-500 text-white rounded-full font-medium hover:bg-orange-600 transition-colors shadow-lg shadow-orange-500/30"
          >
            <Pause className="w-5 h-5" />
            Pause
          </button>
        )}
        
        {(isRunning || timeLeft > 0) && (
          <button
            onClick={handleReset}
            className="flex items-center gap-2 px-6 py-4 bg-gray-100 text-gray-700 rounded-full font-medium hover:bg-gray-200 transition-colors"
          >
            <RotateCcw className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Completion */}
      {isCompleted && (
        <div className="mt-8 text-center">
          <div className="text-4xl mb-3">🧘</div>
          <p className="text-purple-600 font-medium text-lg">Session Complete</p>
          <p className="text-sm text-gray-500 mt-1">
            You meditated for {selectedMinutes} minutes. Well done!
          </p>
        </div>
      )}
    </div>
  );
}

