// components/dashboard/tools/ToolsTab.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Wind, Activity, Eye, Brain, Timer, Flame, ChevronRight, Star, Clock, Trophy } from 'lucide-react';
import BreathingExercise from './BreathingExercise';
import LungsExercise from './LungsExercise';
import EyeRestExercise from './EyeRestExercise';
import MeditationTimer from './MeditationTimer';
import PomodoroTimer from './PomodoroTimer';
import { teamMemberAPI } from '../../../lib/api';

const TOOLS_CATALOGUE = [
  {
    id: 'breathing',
    name: 'Breathing Exercise',
    description: 'Calm your mind with guided breathing techniques',
    icon: Wind,
    color: '#3b82f6',
    bgColor: '#eff6ff',
    component: BreathingExercise,
    popular: true,
    defaultDuration: 120, // seconds
  },
  {
    id: 'lungs',
    name: 'Lungs Exercise',
    description: 'Strengthen respiratory muscles and lung capacity',
    icon: Activity,
    color: '#ec4899',
    bgColor: '#fdf2f8',
    component: LungsExercise,
    isNew: true,
    defaultDuration: 180,
  },
  {
    id: 'eye-rest',
    name: 'Eye Rest',
    description: 'Reduce eye strain with the 20-20-20 rule',
    icon: Eye,
    color: '#6366f1',
    bgColor: '#eef2ff',
    component: EyeRestExercise,
    defaultDuration: 120,
  },
  {
    id: 'meditation',
    name: 'Meditation Timer',
    description: 'Find inner peace with guided meditation sessions',
    icon: Brain,
    color: '#8b5cf6',
    bgColor: '#f5f3ff',
    component: MeditationTimer,
    popular: true,
    defaultDuration: 300,
  },
  {
    id: 'pomodoro',
    name: 'Pomodoro Timer',
    description: 'Boost productivity with focused work intervals',
    icon: Timer,
    color: '#ef4444',
    bgColor: '#fef2f2',
    component: PomodoroTimer,
    defaultDuration: 1500,
  },
];

// Tool Card
function ToolCard({ tool, isActive, onClick, userAvatar }) {
  const Icon = tool.icon;
  return (
    <button
      onClick={onClick}
      className={`w-full p-4 rounded-xl text-left transition-all duration-200 ${
        isActive
          ? 'bg-gradient-to-r from-orange-50 to-pink-50 border-2 border-orange-200 shadow-md'
          : 'bg-white hover:bg-gray-50 border border-gray-100'
      }`}
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: tool.bgColor }}>
          <Icon className="w-5 h-5" style={{ color: tool.color }} />
        </div>

        <div className="relative">
          <img
            src={userAvatar || 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop&crop=face'}
            alt="User"
            className="w-10 h-10 rounded-full object-cover border-2 border-white shadow-sm"
          />
          {tool.streak > 0 && (
            <div className="absolute -top-1 -right-1 w-5 h-5 bg-orange-500 rounded-full flex items-center justify-center">
              <Flame className="w-3 h-3 text-white" />
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-800 truncate">{tool.name}</span>
            {tool.isNew && (
              <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full">New</span>
            )}
            {tool.popular && <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />}
          </div>
          <div className="flex items-center gap-1 text-sm text-orange-500">
            <Flame className="w-3 h-3" />
            <span>{tool.streak} days</span>
          </div>
        </div>

        <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${isActive ? 'rotate-90' : ''}`} />
      </div>
    </button>
  );
}

// Stats Card
function StatsCard({ icon: Icon, value, label, color }) {
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-100">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${color}15` }}>
          <Icon className="w-5 h-5" style={{ color }} />
        </div>
        <div>
          <div className="text-2xl font-bold text-gray-800">{value}</div>
          <div className="text-xs text-gray-500">{label}</div>
        </div>
      </div>
    </div>
  );
}

export default function ToolsTab({ userAvatar }) {
  const [activeTool, setActiveTool] = useState('breathing');
  const [stats, setStats] = useState({ completedToday: 0, weekMinutes: 0, bestStreak: 0, toolStreaks: {} });
  const [sessionStart, setSessionStart] = useState(null);

  // Merge DB streaks into the tools list
  const tools = TOOLS_CATALOGUE.map(t => ({
    ...t,
    streak: stats.toolStreaks[t.id] ?? 0,
  }));

  const currentTool = tools.find(t => t.id === activeTool);
  const ActiveComponent = currentTool?.component;

  const loadStats = useCallback(async () => {
    try {
      const data = await teamMemberAPI.getToolStats();
      setStats(data);
    } catch (err) {
      console.warn('Could not load tool stats', err);
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  // Track when user opens a tool
  const handleSelectTool = (id) => {
    setActiveTool(id);
    setSessionStart(Date.now());
  };

  // Called by each exercise component when it finishes
  const handleComplete = async (subType) => {
    const durationSeconds = sessionStart ? Math.round((Date.now() - sessionStart) / 1000) : currentTool?.defaultDuration ?? 60;
    setSessionStart(null);

    try {
      await teamMemberAPI.logToolUsage({
        toolId: currentTool.id,
        toolName: currentTool.name,
        subType: subType || null,
        durationSeconds,
      });
      // Refresh stats from server
      await loadStats();
    } catch (err) {
      console.warn('Failed to log tool usage', err);
      // Optimistic update fallback
      setStats(prev => ({
        ...prev,
        completedToday: prev.completedToday + 1,
      }));
    }
  };

  const weekLabel = stats.weekMinutes >= 60
    ? `${Math.floor(stats.weekMinutes / 60)}h ${stats.weekMinutes % 60}m`
    : `${stats.weekMinutes}m`;

  return (
    <div className="flex gap-6">
      {/* Left Sidebar */}
      <div className="w-[380px] shrink-0">
        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <StatsCard icon={Trophy} value={stats.completedToday} label="Today" color="#f59e0b" />
          <StatsCard icon={Flame} value={stats.bestStreak || '—'} label="Day Streak" color="#ef4444" />
          <StatsCard icon={Clock} value={weekLabel || '0m'} label="This Week" color="#3b82f6" />
        </div>

        {/* Tool List */}
        <div className="space-y-3">
          {tools.map((tool) => (
            <ToolCard
              key={tool.id}
              tool={tool}
              isActive={activeTool === tool.id}
              onClick={() => handleSelectTool(tool.id)}
              userAvatar={userAvatar}
            />
          ))}
        </div>

        {/* Partner Apps */}
        <div className="mt-6 p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border border-gray-200">
          <p className="text-sm font-medium text-gray-600 mb-2">Partner Apps</p>
          <div className="space-y-2">
            <a href="#" className="block text-sm text-blue-600 hover:underline">Fiteatsy Ads</a>
            <a href="#" className="block text-sm text-blue-600 hover:underline">Humjoli Ads</a>
          </div>
        </div>
      </div>

      {/* Right Content */}
      <div className="flex-1 bg-white rounded-2xl border border-gray-100 p-8">
        {currentTool && (
          <>
            <div className="flex items-center gap-4 mb-8 pb-6 border-b border-gray-100">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ backgroundColor: currentTool.bgColor }}>
                <currentTool.icon className="w-7 h-7" style={{ color: currentTool.color }} />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-800">{currentTool.name}</h2>
                <p className="text-gray-500">{currentTool.description}</p>
              </div>
            </div>

            {ActiveComponent && (
              <ActiveComponent onComplete={handleComplete} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
