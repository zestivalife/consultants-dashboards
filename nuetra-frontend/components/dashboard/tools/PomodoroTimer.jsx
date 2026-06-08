// apps/web/frontend/components/dashboard/tools/PomodoroTimer.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipForward, RotateCcw, Coffee, Briefcase } from 'lucide-react';

const POMODORO_SETTINGS = {
  work: { minutes: 25, label: 'Focus', color: '#ef4444', icon: Briefcase },
  shortBreak: { minutes: 5, label: 'Short Break', color: '#22c55e', icon: Coffee },
  longBreak: { minutes: 15, label: 'Long Break', color: '#3b82f6', icon: Coffee },
};

export default function PomodoroTimer({ onComplete }) {
  const [mode, setMode] = useState('work'); // work, shortBreak, longBreak
  const [isRunning, setIsRunning] = useState(false);
  const [timeLeft, setTimeLeft] = useState(POMODORO_SETTINGS.work.minutes * 60);
  const [completedPomodoros, setCompletedPomodoros] = useState(0);
  const [totalFocusTime, setTotalFocusTime] = useState(0);
  
  const intervalRef = useRef(null);
  const settings = POMODORO_SETTINGS[mode];
  const totalSeconds = settings.minutes * 60;
  const progress = ((totalSeconds - timeLeft) / totalSeconds) * 100;

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    if (isRunning && timeLeft > 0) {
      intervalRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (mode === 'work') {
            setTotalFocusTime(t => t + 1);
          }
          
          if (prev <= 1) {
            setIsRunning(false);
            
            // Handle completion
            if (mode === 'work') {
              setCompletedPomodoros(p => p + 1);
              // After 4 pomodoros, suggest long break
              const nextMode = (completedPomodoros + 1) % 4 === 0 ? 'longBreak' : 'shortBreak';
              setMode(nextMode);
              setTimeLeft(POMODORO_SETTINGS[nextMode].minutes * 60);
            } else {
              setMode('work');
              setTimeLeft(POMODORO_SETTINGS.work.minutes * 60);
            }
            
            onComplete?.();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    
    return () => clearInterval(intervalRef.current);
  }, [isRunning, timeLeft, mode, completedPomodoros, onComplete]);

  const handleStart = () => {
    setIsRunning(true);
  };

  const handlePause = () => {
    setIsRunning(false);
  };

  const handleReset = () => {
    setIsRunning(false);
    setTimeLeft(settings.minutes * 60);
  };

  const handleSkip = () => {
    setIsRunning(false);
    if (mode === 'work') {
      const nextMode = completedPomodoros % 4 === 3 ? 'longBreak' : 'shortBreak';
      setMode(nextMode);
      setTimeLeft(POMODORO_SETTINGS[nextMode].minutes * 60);
    } else {
      setMode('work');
      setTimeLeft(POMODORO_SETTINGS.work.minutes * 60);
    }
  };

  const handleModeChange = (newMode) => {
    setIsRunning(false);
    setMode(newMode);
    setTimeLeft(POMODORO_SETTINGS[newMode].minutes * 60);
  };

  const Icon = settings.icon;

  return (
    <div className="flex flex-col items-center">
      {/* Mode Selector */}
      <div className="flex gap-2 mb-8 bg-gray-100 p-1 rounded-full">
        {Object.entries(POMODORO_SETTINGS).map(([key, config]) => (
          <button
            key={key}
            onClick={() => handleModeChange(key)}
            className={`px-5 py-2.5 rounded-full font-medium text-sm transition-all ${
              mode === key
                ? 'bg-white shadow-md'
                : 'text-gray-600 hover:text-gray-800'
            }`}
            style={{ color: mode === key ? config.color : undefined }}
          >
            {config.label}
          </button>
        ))}
      </div>

      {/* Timer Circle */}
      <div className="relative mb-8">
        <svg width="300" height="300" className="transform -rotate-90">
          <circle
            cx="150"
            cy="150"
            r="130"
            fill="none"
            stroke="#f3f4f6"
            strokeWidth="12"
          />
          <circle
            cx="150"
            cy="150"
            r="130"
            fill="none"
            stroke={settings.color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={2 * Math.PI * 130}
            strokeDashoffset={2 * Math.PI * 130 * (1 - progress / 100)}
            className="transition-all duration-1000"
            style={{
              filter: `drop-shadow(0 0 10px ${settings.color}40)`
            }}
          />
        </svg>
        
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <Icon className="w-8 h-8 mb-2" style={{ color: settings.color }} />
          <span className="text-6xl font-bold text-gray-800">
            {formatTime(timeLeft)}
          </span>
          <span className="text-sm text-gray-500 mt-2 uppercase tracking-wider">
            {settings.label}
          </span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex gap-4 mb-8">
        {!isRunning ? (
          <button
            onClick={handleStart}
            className="flex items-center gap-2 px-10 py-4 text-white rounded-full font-medium transition-all shadow-lg"
            style={{ 
              backgroundColor: settings.color,
              boxShadow: `0 10px 30px ${settings.color}40`
            }}
          >
            <Play className="w-5 h-5" />
            Start
          </button>
        ) : (
          <button
            onClick={handlePause}
            className="flex items-center gap-2 px-10 py-4 bg-gray-800 text-white rounded-full font-medium transition-colors shadow-lg"
          >
            <Pause className="w-5 h-5" />
            Pause
          </button>
        )}
        
        <button
          onClick={handleReset}
          className="p-4 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
          title="Reset"
        >
          <RotateCcw className="w-5 h-5" />
        </button>
        
        <button
          onClick={handleSkip}
          className="p-4 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
          title="Skip to next"
        >
          <SkipForward className="w-5 h-5" />
        </button>
      </div>

      {/* Stats */}
      <div className="flex gap-8 p-6 bg-gray-50 rounded-2xl">
        <div className="text-center">
          <div className="flex items-center justify-center gap-1 mb-1">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className={`w-4 h-4 rounded-full transition-colors ${
                  i < completedPomodoros % 4 ? 'bg-red-500' : 'bg-gray-200'
                }`}
              />
            ))}
          </div>
          <div className="text-2xl font-bold text-gray-800">{completedPomodoros}</div>
          <div className="text-xs text-gray-500">Pomodoros</div>
        </div>
        
        <div className="w-px bg-gray-200" />
        
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-800">
            {Math.floor(totalFocusTime / 60)}
          </div>
          <div className="text-xs text-gray-500">Minutes Focused</div>
        </div>
        
        <div className="w-px bg-gray-200" />
        
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-800">
            {Math.round((completedPomodoros * 25) / 60 * 10) / 10}
          </div>
          <div className="text-xs text-gray-500">Hours Today</div>
        </div>
      </div>

      {/* Tip */}
      <p className="text-xs text-gray-400 mt-6 text-center max-w-md">
        💡 After 4 focus sessions, take a longer break to recharge your mental energy.
      </p>
    </div>
  );
}

