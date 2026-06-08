// apps/web/frontend/components/dashboard/FocusModeResult.jsx
import React from 'react';
import { X, Zap, AlertTriangle, Battery, Brain, Scale, RefreshCw, ArrowRight } from 'lucide-react';

// Result bucket configurations
const resultBuckets = {
  highFocus: {
    id: 'highFocus',
    name: 'High Focus Mode',
    icon: Zap,
    color: 'from-emerald-500 to-teal-500',
    bgColor: 'bg-emerald-500/20',
    borderColor: 'border-emerald-500/30',
    iconColor: 'text-emerald-400',
    description: 'You\'re operating at peak performance with excellent energy and focus levels.',
    recommendations: [
      'Maintain your current routines - they\'re working well',
      'Consider mentoring others on your productivity strategies',
      'Take on challenging deep work projects',
      'Schedule strategic breaks to sustain this momentum',
    ],
  },
  overloaded: {
    id: 'overloaded',
    name: 'Overloaded Mode',
    icon: AlertTriangle,
    color: 'from-red-500 to-orange-500',
    bgColor: 'bg-red-500/20',
    borderColor: 'border-red-500/30',
    iconColor: 'text-red-400',
    description: 'You\'re experiencing high stress and poor work-life balance. It\'s time to recalibrate.',
    recommendations: [
      'Prioritize tasks ruthlessly - delegate or defer non-essential work',
      'Set firm boundaries for work hours',
      'Schedule mandatory breaks every 90 minutes',
      'Consider discussing workload with your manager',
    ],
  },
  lowEnergy: {
    id: 'lowEnergy',
    name: 'Low Energy Mode',
    icon: Battery,
    color: 'from-amber-500 to-yellow-500',
    bgColor: 'bg-amber-500/20',
    borderColor: 'border-amber-500/30',
    iconColor: 'text-amber-400',
    description: 'Your energy and focus levels are depleted. Focus on restoration and recovery.',
    recommendations: [
      'Prioritize sleep - aim for 7-8 hours consistently',
      'Take short walks or movement breaks during the day',
      'Review your nutrition and hydration habits',
      'Schedule your most important work during your peak energy time',
    ],
  },
  stressDriven: {
    id: 'stressDriven',
    name: 'Stress-Driven Mode',
    icon: Brain,
    color: 'from-purple-500 to-pink-500',
    bgColor: 'bg-purple-500/20',
    borderColor: 'border-purple-500/30',
    iconColor: 'text-purple-400',
    description: 'Stress is impacting your mood and ability to disconnect. Mental wellness needs attention.',
    recommendations: [
      'Practice mindfulness or meditation for 10 minutes daily',
      'Create a clear end-of-day ritual to disconnect',
      'Limit work notifications outside office hours',
      'Consider speaking with a wellness professional',
    ],
  },
  balanceSeeking: {
    id: 'balanceSeeking',
    name: 'Balance-Seeking Mode',
    icon: Scale,
    color: 'from-blue-500 to-indigo-500',
    bgColor: 'bg-blue-500/20',
    borderColor: 'border-blue-500/30',
    iconColor: 'text-blue-400',
    description: 'You have mixed signals - some areas are good, others need attention. Let\'s find balance.',
    recommendations: [
      'Identify your biggest pain point and address it first',
      'Create a consistent daily routine',
      'Set aside dedicated personal time each day',
      'Track your energy levels to find patterns',
    ],
  },
};

// Calculate which bucket the user falls into
function calculateResultBucket(answers, questions) {
  // Calculate category scores
  const categoryScores = {
    energyFocus: 0,      // Q1-3
    moodEmotional: 0,    // Q4-5
    stressMental: 0,     // Q6-7
    workLifeBalance: 0,  // Q8-9
    lifestyle: 0,        // Q10-11
  };

  // Map question IDs to categories
  questions.forEach(q => {
    const answer = answers[q.id] || 0;
    
    if (q.id >= 1 && q.id <= 3) {
      categoryScores.energyFocus += answer;
    } else if (q.id >= 4 && q.id <= 5) {
      categoryScores.moodEmotional += answer;
    } else if (q.id >= 6 && q.id <= 7) {
      categoryScores.stressMental += answer;
    } else if (q.id >= 8 && q.id <= 9) {
      categoryScores.workLifeBalance += answer;
    } else if (q.id >= 10 && q.id <= 11) {
      categoryScores.lifestyle += answer;
    }
  });

  // Normalize scores (max possible for each category)
  const maxScores = {
    energyFocus: 12,      // 3 questions × 4 points
    moodEmotional: 8,     // 2 questions × 4 points
    stressMental: 8,      // 2 questions × 4 points
    workLifeBalance: 8,   // 2 questions × 4 points
    lifestyle: 8,         // 2 questions × 4 points
  };

  const normalizedScores = {
    energyFocus: categoryScores.energyFocus / maxScores.energyFocus,
    moodEmotional: categoryScores.moodEmotional / maxScores.moodEmotional,
    stressMental: categoryScores.stressMental / maxScores.stressMental,
    workLifeBalance: categoryScores.workLifeBalance / maxScores.workLifeBalance,
    lifestyle: categoryScores.lifestyle / maxScores.lifestyle,
  };

  const totalScore = Object.values(answers).reduce((sum, val) => sum + val, 0);
  const maxTotal = 44; // 11 questions × 4 points
  const overallPercentage = totalScore / maxTotal;

  // Decision logic for bucket assignment
  // High Focus Mode: High scores in energy/focus AND balanced elsewhere
  if (normalizedScores.energyFocus >= 0.75 && overallPercentage >= 0.7) {
    return 'highFocus';
  }
  
  // Overloaded Mode: Low work-life balance AND low stress/mental scores
  if (normalizedScores.workLifeBalance <= 0.4 && normalizedScores.stressMental <= 0.4) {
    return 'overloaded';
  }
  
  // Low Energy Mode: Low energy/focus AND poor lifestyle (sleep/fatigue)
  if (normalizedScores.energyFocus <= 0.5 && normalizedScores.lifestyle <= 0.5) {
    return 'lowEnergy';
  }
  
  // Stress-Driven Mode: Low mood AND can't disconnect (stress/mental)
  if (normalizedScores.moodEmotional <= 0.5 && normalizedScores.stressMental <= 0.5) {
    return 'stressDriven';
  }
  
  // Balance-Seeking Mode: Mixed scores, default bucket
  return 'balanceSeeking';
}

export default function FocusModeResult({ answers, questions, onClose, onRetake, isContained = false }) {
  const bucketId = calculateResultBucket(answers, questions);
  const result = resultBuckets[bucketId];
  const Icon = result.icon;

  // Calculate overall score for display
  const totalScore = Object.values(answers).reduce((sum, val) => sum + val, 0);
  const maxTotal = 44;
  const scorePercentage = Math.round((totalScore / maxTotal) * 100);

  // Contained version (within a card)
  if (isContained) {
    return (
      <div 
        className="relative rounded-2xl overflow-hidden"
        style={{
          background: 'linear-gradient(180deg, #050d1a 0%, #0a1628 50%, #0f1d32 100%)',
          minHeight: '600px',
        }}
      >
        {/* Glow effects */}
        <div 
          className="absolute top-1/4 left-1/3 w-[400px] h-[400px] rounded-full opacity-20 pointer-events-none"
          style={{
            background: `radial-gradient(circle, rgba(99, 102, 241, 0.4) 0%, transparent 70%)`,
            filter: 'blur(60px)',
          }}
        />

        {/* Close button */}
        <div className="flex justify-center pt-6">
          <button
            onClick={onClose}
            className="w-10 h-10 rounded-full bg-[#1e293b] border border-[#334155] flex items-center justify-center hover:bg-[#334155] transition-colors"
          >
            <X className="w-4 h-4 text-white/70" />
          </button>
        </div>

        {/* Result content */}
        <div className="relative z-10 px-8 py-6">
          <div 
            className="rounded-2xl p-6 max-w-xl mx-auto"
            style={{
              background: 'linear-gradient(180deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)',
              border: '1px solid rgba(71, 85, 105, 0.3)',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
            }}
          >
            {/* Header with icon */}
            <div className="flex items-center gap-4 mb-5">
              <div className={`w-14 h-14 rounded-xl ${result.bgColor} ${result.borderColor} border flex items-center justify-center`}>
                <Icon className={`w-7 h-7 ${result.iconColor}`} />
              </div>
              <div>
                <p className="text-white/50 text-xs mb-1">Your Focus Mode</p>
                <h2 className={`text-xl font-bold bg-gradient-to-r ${result.color} bg-clip-text text-transparent`}>
                  {result.name}
                </h2>
              </div>
            </div>

            {/* Score indicator */}
            <div className="flex items-center gap-4 mb-5 p-3 bg-white/5 rounded-xl border border-white/10">
              <div className="flex-1">
                <p className="text-white/50 text-xs mb-1">Wellness Score</p>
                <p className="text-xl font-bold text-white">{scorePercentage}%</p>
              </div>
              <div className="w-28 h-2 bg-white/10 rounded-full overflow-hidden">
                <div 
                  className={`h-full bg-gradient-to-r ${result.color} rounded-full transition-all duration-1000`}
                  style={{ width: `${scorePercentage}%` }}
                />
              </div>
            </div>

            {/* Description */}
            <p className="text-white/70 text-sm leading-relaxed mb-5">
              {result.description}
            </p>

            {/* Recommendations */}
            <div className="mb-5">
              <h3 className="text-white font-semibold text-sm mb-3 flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center text-[10px]">✨</span>
                Recommended Actions
              </h3>
              <div className="space-y-2">
                {result.recommendations.slice(0, 3).map((rec, index) => (
                  <div 
                    key={index}
                    className="flex items-start gap-2 p-2.5 bg-white/5 rounded-lg border border-white/5"
                  >
                    <ArrowRight className="w-3.5 h-3.5 text-[#6366f1] mt-0.5 shrink-0" />
                    <span className="text-white/70 text-xs">{rec}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex gap-3">
              <button
                onClick={onRetake}
                className="flex-1 py-2.5 px-4 rounded-xl font-medium text-sm bg-[#1e293b] text-white border border-[#475569] hover:bg-[#334155] transition-all duration-200 flex items-center justify-center gap-2"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Retake Quiz
              </button>
              <button
                onClick={onClose}
                className="flex-1 py-2.5 px-4 rounded-xl font-medium text-sm bg-[#6366f1] text-white hover:bg-[#4f46e5] shadow-lg shadow-[#6366f1]/25 transition-all duration-200"
              >
                Start Focus Session
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Full-screen version (original)
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto py-8">
      {/* Dark gradient background */}
      <div 
        className="absolute inset-0"
        style={{
          background: 'linear-gradient(135deg, #0a1628 0%, #1a2744 50%, #0f1d32 100%)',
        }}
      />
      
      {/* Glow effects matching result color */}
      <div 
        className="absolute top-1/4 left-1/3 w-[500px] h-[500px] rounded-full opacity-30"
        style={{
          background: `radial-gradient(circle, rgba(99, 102, 241, 0.4) 0%, transparent 70%)`,
          filter: 'blur(80px)',
        }}
      />

      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-8 left-1/2 -translate-x-1/2 z-10 w-12 h-12 rounded-full bg-[#1a2744] border border-white/10 flex items-center justify-center hover:bg-[#243656] transition-colors"
      >
        <X className="w-5 h-5 text-white/70" />
      </button>

      {/* Result content */}
      <div className="relative z-10 w-full max-w-2xl mx-auto px-6">
        <div className="bg-[#1a2744]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
          {/* Header with icon */}
          <div className="flex items-center gap-4 mb-6">
            <div className={`w-16 h-16 rounded-2xl ${result.bgColor} ${result.borderColor} border flex items-center justify-center`}>
              <Icon className={`w-8 h-8 ${result.iconColor}`} />
            </div>
            <div>
              <p className="text-white/50 text-sm mb-1">Your Focus Mode</p>
              <h2 className={`text-2xl font-bold bg-gradient-to-r ${result.color} bg-clip-text text-transparent`}>
                {result.name}
              </h2>
            </div>
          </div>

          {/* Score indicator */}
          <div className="flex items-center gap-4 mb-6 p-4 bg-white/5 rounded-xl border border-white/10">
            <div className="flex-1">
              <p className="text-white/50 text-sm mb-1">Wellness Score</p>
              <p className="text-2xl font-bold text-white">{scorePercentage}%</p>
            </div>
            <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
              <div 
                className={`h-full bg-gradient-to-r ${result.color} rounded-full transition-all duration-1000`}
                style={{ width: `${scorePercentage}%` }}
              />
            </div>
          </div>

          {/* Description */}
          <p className="text-white/70 text-lg leading-relaxed mb-8">
            {result.description}
          </p>

          {/* Recommendations */}
          <div className="mb-8">
            <h3 className="text-white font-semibold text-lg mb-4 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-xs">✨</span>
              Recommended Actions
            </h3>
            <div className="space-y-3">
              {result.recommendations.map((rec, index) => (
                <div 
                  key={index}
                  className="flex items-start gap-3 p-3 bg-white/5 rounded-xl border border-white/5 hover:border-white/10 transition-colors"
                >
                  <ArrowRight className="w-4 h-4 text-indigo-400 mt-0.5 shrink-0" />
                  <span className="text-white/70 text-sm">{rec}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex gap-4">
            <button
              onClick={onRetake}
              className="flex-1 py-3 px-6 rounded-xl font-medium bg-[#2a3a5c] text-white hover:bg-[#354766] transition-all duration-200 flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Retake Quiz
            </button>
            <button
              onClick={onClose}
              className="flex-1 py-3 px-6 rounded-xl font-medium bg-gradient-to-r from-indigo-500 to-purple-500 text-white hover:from-indigo-600 hover:to-purple-600 shadow-lg shadow-indigo-500/25 transition-all duration-200"
            >
              Start Focus Session
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
