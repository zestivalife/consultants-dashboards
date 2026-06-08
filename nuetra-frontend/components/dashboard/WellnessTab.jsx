// apps/web/frontend/components/dashboard/WellnessTab.jsx
import React, { useState } from 'react';
import { Heart, Flame, Moon, Droplet, Sun, Brain, Activity, X } from 'lucide-react';
import PSS10Form from '../PSS10Form';
import PhysicalEaseForm from '../PhysicalEaseForm';
import SleepForm from '../SleepForm';
import HydrationForm from '../HydrationForm';
import CaloriesForm from '../CaloriesForm';
import StepsForm from '../StepsForm';
import HeartRateForm from '../HeartRateForm';
import SunlightForm from '../SunlightForm';

// Stress Level Gauge with gradient arc
function StressGauge({ value }) {
  if (value === null || value === undefined) {
    return (
      <div className="flex items-center justify-center h-[90px]">
        <span className="text-sm font-medium text-gray-400 italic">No data found</span>
      </div>
    );
  }

  const getCategory = (score) => {
    if (score <= 13) return { label: 'Low', color: '#22c55e' };
    if (score <= 26) return { label: 'Moderate', color: '#eab308' };
    return { label: 'High', color: '#ef4444' };
  };

  const category = getCategory(value);
  const percentage = Math.min((value / 40) * 100, 100);

  // Circumference of half circle with r=65 is approx 204.2
  const circumference = 204.2;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative w-[160px] h-[90px]">
      <svg viewBox="0 0 160 90" className="w-full h-full">
        <defs>
          <linearGradient id="stressGaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22c55e" />
            <stop offset="50%" stopColor="#eab308" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
        </defs>
        {/* Arc background */}
        <path
          d="M 15 80 A 65 65 0 0 1 145 80"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="10"
          strokeLinecap="round"
        />
        {/* Filled arc */}
        <path
          d="M 15 80 A 65 65 0 0 1 145 80"
          fill="none"
          stroke="url(#stressGaugeGradient)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
        />
      </svg>
      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center pt-2">
        <span className="text-4xl font-bold text-[#1a1a1a] leading-none mb-1">{value}</span>
        <span className="text-sm font-semibold leading-none" style={{ color: category.color }}>{category.label}</span>
      </div>
    </div>
  );
}

// Active Calories Speedometer Gauge
function CaloriesGauge({ value, goal = 600 }) {
  if (value === null || value === undefined) {
    return (
      <div className="flex items-center justify-center h-[80px]">
        <span className="text-sm font-medium text-gray-400 italic">No data found</span>
      </div>
    );
  }
  const percentage = Math.min((value / goal) * 100, 100);
  const angle = (percentage / 100) * 180;

  return (
    <div className="relative w-[120px] h-[80px]">
      <svg viewBox="0 0 120 80" className="w-full h-full">
        <defs>
          <linearGradient id="caloriesArcGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22c55e" />
            <stop offset="50%" stopColor="#eab308" />
            <stop offset="100%" stopColor="#f97316" />
          </linearGradient>
        </defs>
        {/* Background arc */}
        <path
          d="M 15 70 A 45 45 0 0 1 105 70"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="8"
          strokeLinecap="round"
        />
        {/* Colored arc */}
        <path
          d="M 15 70 A 45 45 0 0 1 105 70"
          fill="none"
          stroke="url(#caloriesArcGradient)"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${percentage * 1.41} 141`}
        />
        {/* Needle */}
        <g transform={`rotate(${angle - 90}, 60, 70)`}>
          <line x1="60" y1="70" x2="60" y2="30" stroke="#1a1a1a" strokeWidth="2" strokeLinecap="round" />
        </g>
        {/* Center dot */}
        <circle cx="60" cy="70" r="4" fill="#1a1a1a" />
      </svg>
      {/* Value badge */}
      <div className="absolute -top-1 right-2 bg-[#f97316] text-white text-xs font-bold px-2 py-0.5 rounded-full">
        {value}
      </div>
    </div>
  );
}

// Steps Arc Component
function StepsArc({ value, goal = 10000 }) {
  if (value === null || value === undefined) {
    return (
      <div className="flex items-center justify-center h-[70px]">
        <span className="text-sm font-medium text-gray-400 italic">No data found</span>
      </div>
    );
  }
  const percentage = Math.min((value / goal) * 100, 100);

  return (
    <div className="relative w-[100px] h-[70px]">
      <svg viewBox="0 0 100 70" className="w-full h-full">
        {/* Background arc */}
        <path
          d="M 10 60 A 40 40 0 0 1 90 60"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="12"
          strokeLinecap="round"
        />
        {/* Progress arc */}
        <path
          d="M 10 60 A 40 40 0 0 1 90 60"
          fill="none"
          stroke="#3b82f6"
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={`${percentage * 1.26} 126`}
        />
      </svg>
      {/* Footprint icons */}
      <div className="absolute top-1 left-1/2 -translate-x-1/2 flex gap-0.5">
        <svg width="18" height="22" viewBox="0 0 18 22" fill="none" className="text-blue-400">
          <path d="M5 7C5 4.5 6.5 2 9 2C11.5 2 13 4.5 13 7C13 9.5 11.5 12 9 12C6.5 12 5 9.5 5 7Z" fill="currentColor" opacity="0.6" />
          <path d="M4 16C4 14.5 5.5 13 7.5 13C8.5 13 9.5 13.5 10 14C10.5 14.5 11 15.5 11 16.5C11 18 10 19 9 19.5C8 20 6.5 20 5.5 19C4.5 18 4 17 4 16Z" fill="currentColor" />
        </svg>
        <svg width="18" height="22" viewBox="0 0 18 22" fill="none" className="text-blue-500 -mt-1">
          <path d="M5 7C5 4.5 6.5 2 9 2C11.5 2 13 4.5 13 7C13 9.5 11.5 12 9 12C6.5 12 5 9.5 5 7Z" fill="currentColor" opacity="0.6" />
          <path d="M4 16C4 14.5 5.5 13 7.5 13C8.5 13 9.5 13.5 10 14C10.5 14.5 11 15.5 11 16.5C11 18 10 19 9 19.5C8 20 6.5 20 5.5 19C4.5 18 4 17 4 16Z" fill="currentColor" />
        </svg>
      </div>
    </div>
  );
}

// Heart Rate Chart Component with gradient
function HeartRateChart() {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const values = [55, 65, 70, 85, 95, 80, 60];
  const dateNumbers = [13, 14, 15, 16, 17, 18, 19];
  const maxVal = 100;

  return (
    <div className="relative h-[120px] w-full rounded-xl overflow-hidden">
      <div
        className="absolute inset-0"
        style={{
          background: 'linear-gradient(180deg, #3b82f6 0%, #8b5cf6 40%, #ec4899 80%, #f43f5e 100%)',
        }}
      />
      <div className="relative flex items-end justify-around h-full px-3 pb-6 pt-3">
        {values.map((val, i) => (
          <div key={i} className="flex flex-col items-center gap-1 relative">
            <div
              className="w-3 bg-white/90 rounded-sm"
              style={{ height: `${(val / maxVal) * 60}px` }}
            />
            {i === 4 && (
              <div className="absolute -top-1 w-4 h-4 bg-white rounded-full border-2 border-pink-400 shadow-lg" style={{ top: `-${(val / maxVal) * 60 + 8}px` }} />
            )}
            <div className="absolute bottom-0 translate-y-full pt-1">
              <span className="text-[9px] text-white/90 font-medium">{dateNumbers[i]}</span>
            </div>
          </div>
        ))}
      </div>
      {/* Day labels */}
      <div className="absolute bottom-0 left-0 right-0 flex justify-around px-3 pb-1">
        {days.map((day, i) => (
          <span key={i} className="text-[8px] text-white/70">{day}</span>
        ))}
      </div>
    </div>
  );
}

// Water Circular Progress
function WaterProgress({ value, goal = 2.8 }) {
  if (value === null || value === undefined) {
    return (
      <div className="flex items-center justify-center h-[100px] w-[100px]">
        <span className="text-sm font-medium text-gray-400 italic">No data found</span>
      </div>
    );
  }
  const size = 100;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const percentage = Math.min((value / goal) * 100, 100);
  const strokeDashoffset = circumference * (1 - percentage / 100);
  const center = size / 2;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="#06b6d4"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold text-[#1a1a1a]">{value}</span>
        <span className="text-xs text-gray-500">Liters</span>
      </div>
    </div>
  );
}

// Wellness Score Ring with Person Image
function WellnessScoreRing({ score = 80 }) {
  const size = 320;
  const strokeWidth = 22;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const percentage = score / 100;
  const strokeDashoffset = circumference * (1 - percentage);
  const center = size / 2;

  return (
    <div className="relative" style={{ width: 460, height: 645 }}>
      {/* Progress ring - positioned to wrap around person */}
      <div className="absolute" style={{ width: size, height: size, top: 30, left: 30 }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <defs>
            <linearGradient id="wellnessRingGradient" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#06b6d4" />
              <stop offset="25%" stopColor="#3b82f6" />
              <stop offset="50%" stopColor="#8b5cf6" />
              <stop offset="75%" stopColor="#ec4899" />
              <stop offset="100%" stopColor="#f97316" />
            </linearGradient>
          </defs>
          {/* Background track */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={strokeWidth}
          />
          {/* Progress arc */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="url(#wellnessRingGradient)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-1000"
          />
        </svg>
      </div>

      {/* Person image - positioned inside ring */}
      <div className="absolute bottom-0 left-0" style={{ width: 380, height: 580 }}>
        <img
          src="/wellness-person.png"
          alt="User wellness"
          className="w-full h-full object-cover object-top"
          onError={(e) => {
            // Fallback to placeholder if image fails to load
            e.target.style.display = 'none';
          }}
        />
      </div>

      {/* Score display - positioned on right side of ring */}
      <div className="absolute text-right" style={{ right: 20, top: 180 }}>
        <div className="text-6xl font-bold text-[#1a1a1a]">{score}</div>
        <div className="text-2xl font-semibold text-[#1a1a1a]">Physical</div>
        <div className="text-base text-gray-500">Wellness Index</div>
      </div>
    </div>
  );
}

// Metric Card Component with Figma styling
function MetricCard({ children, className = '', onClick, style }) {
  return (
    <div
      className={`bg-white rounded-2xl p-4 ${className} ${onClick ? 'cursor-pointer hover:bg-gray-50 transition-colors' : ''}`}
      onClick={onClick}
      style={{
        border: '1px solid #E7E7E9',
        borderRadius: '16px',
        boxShadow: 'inset 0px 4px 4px -1px rgba(12, 12, 13, 0.05)',
        ...style
      }}
    >
      {children}
    </div>
  );
}

export default function WellnessTab({ dashboardStats, onRefresh }) {
  const [isPssModalOpen, setIsPssModalOpen] = useState(false);
  const [isSubmittingPss, setIsSubmittingPss] = useState(false);

  const [isPhysicalEaseModalOpen, setIsPhysicalEaseModalOpen] = useState(false);
  const [isSubmittingPhysicalEase, setIsSubmittingPhysicalEase] = useState(false);

  const [isSleepModalOpen, setIsSleepModalOpen] = useState(false);
  const [isSubmittingSleep, setIsSubmittingSleep] = useState(false);

  const [isHydrationModalOpen, setIsHydrationModalOpen] = useState(false);
  const [isSubmittingHydration, setIsSubmittingHydration] = useState(false);

  const [isCaloriesModalOpen, setIsCaloriesModalOpen] = useState(false);
  const [isSubmittingCalories, setIsSubmittingCalories] = useState(false);

  const [isStepsModalOpen, setIsStepsModalOpen] = useState(false);
  const [isSubmittingSteps, setIsSubmittingSteps] = useState(false);

  const [isHeartRateModalOpen, setIsHeartRateModalOpen] = useState(false);
  const [isSubmittingHeartRate, setIsSubmittingHeartRate] = useState(false);

  const [isSunlightModalOpen, setIsSunlightModalOpen] = useState(false);
  const [isSubmittingSunlight, setIsSubmittingSunlight] = useState(false);

  const wellnessData = {
    wellnessScore: dashboardStats?.wellnessScore || 0,
    stressLevel: dashboardStats?.stressLevel,
    activeCalories: dashboardStats?.activeCalories,
    caloriesGoal: 600,
    heartRate: dashboardStats?.heartRate,
    steps: dashboardStats?.stepsToday,
    stepsGoal: 10000,
    sleepHours: dashboardStats?.sleepHours,
    sleepGoal: 8,
    waterLiters: dashboardStats?.waterLiters,
    waterGoal: 2.8,
    sunlightToday: dashboardStats?.sunlightToday,
    sunlightYesterday: 2, // Static for now as not tracked
    physicalEase: dashboardStats?.physicalEase
  };

  return (
    <div className="flex gap-6 items-start">
      {/* Left Side - Wellness Score with Person Image (460x645 as per Figma) */}
      <div className="shrink-0" style={{ width: 460, height: 645 }}>
        <WellnessScoreRing score={wellnessData.wellnessScore} />
      </div>

      {/* Right Side - Metrics Grid */}
      <div className="flex-1 flex flex-col gap-4">
        {/* Row 1: Stress Level + Active Calories */}
        <div className="flex gap-4" style={{ height: 180 }}>
          {/* Stress Level - larger card (344x100 ratio from Figma) */}
          <MetricCard className="flex-1" onClick={() => setIsPssModalOpen(true)}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-7 h-7 rounded-full bg-red-100 flex items-center justify-center">
                <Brain className="w-4 h-4 text-red-500" />
              </div>
              <span className="font-semibold text-[#1a1a1a]">Stress Level</span>
            </div>
            <div className="flex justify-center my-1">
              <StressGauge value={wellnessData.stressLevel} />
            </div>
            <div className="flex justify-around mt-2 border-t border-gray-100">
              <div className="flex flex-col items-center">
                <div className="w-2.5 h-2.5 rounded-full bg-green-500 mb-1" />
                <span className="text-[10px] text-gray-500 whitespace-nowrap">Low (0-13)</span>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500 mb-1" />
                <span className="text-[10px] text-gray-500 whitespace-nowrap">Moderate (14-26)</span>
              </div>
              <div className="flex flex-col items-center">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500 mb-1" />
                <span className="text-[10px] text-gray-500 whitespace-nowrap">High (27-40)</span>
              </div>
            </div>
          </MetricCard>

          {/* Active Calories */}
          <MetricCard style={{ width: 200 }} onClick={() => setIsCaloriesModalOpen(true)}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-7 h-7 rounded-full bg-orange-100 flex items-center justify-center">
                <Flame className="w-4 h-4 text-orange-500" />
              </div>
              <span className="font-semibold text-[#1a1a1a] text-sm">Active Calories</span>
            </div>
            <div className="flex justify-center my-1">
              <CaloriesGauge value={wellnessData.activeCalories} goal={wellnessData.caloriesGoal} />
            </div>
            <div className="flex justify-between items-center text-sm mt-1">
              <span className="text-gray-500 text-xs">Goal {wellnessData.caloriesGoal}</span>
              <span className="text-orange-500 font-medium text-xs">Under</span>
            </div>
          </MetricCard>
        </div>

        {/* Row 2: Heart Rate + Steps + Sleep (573x199 for heart rate as per Figma) */}
        <div className="flex gap-4" style={{ height: 199 }}>
          {/* Heart Rate */}
          <MetricCard className="flex-1" onClick={() => setIsHeartRateModalOpen(true)}>
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-pink-100 flex items-center justify-center">
                  <Heart className="w-4 h-4 text-pink-500" />
                </div>
                <span className="font-semibold text-[#1a1a1a]">Heart Rate</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="text-lg font-bold text-[#1a1a1a]">{wellnessData.heartRate !== null && wellnessData.heartRate !== undefined ? `${wellnessData.heartRate} BPM` : 'No data'}</span>
                {wellnessData.heartRate && <span className="text-green-500">↑</span>}
              </div>
            </div>
            <span className="text-xs text-gray-500 block mb-2 ml-9">Current</span>
            <HeartRateChart />
          </MetricCard>

          {/* Steps Today */}
          <MetricCard style={{ width: 180 }} onClick={() => setIsStepsModalOpen(true)}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="text-blue-500">
                  <path d="M12 2C10.5 2 9 3.5 9 5.5C9 7.5 10.5 9 12 9C13.5 9 15 7.5 15 5.5C15 3.5 13.5 2 12 2Z" fill="currentColor" />
                  <path d="M8 14C8 12 9.5 10 12 10C14.5 10 16 12 16 14C16 16 14.5 18 12 18C9.5 18 8 16 8 14Z" fill="currentColor" opacity="0.6" />
                  <path d="M10 22C10 20 11 19 12 19C13 19 14 20 14 22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </div>
              <span className="font-semibold text-[#1a1a1a] text-sm">Steps Today</span>
            </div>
            <div className="flex justify-center my-1">
              <StepsArc value={wellnessData.steps} goal={wellnessData.stepsGoal} />
            </div>
            <div className="text-center mt-1">
              <div className="text-xl font-bold text-[#1a1a1a]">{wellnessData.steps !== null && wellnessData.steps !== undefined ? wellnessData.steps.toLocaleString() : 'No data'}</div>
              <div className="text-xs text-gray-500">Goal  {wellnessData.stepsGoal.toLocaleString()} Steps</div>
            </div>
          </MetricCard>

          {/* Sleep Last Night */}
          <MetricCard style={{ width: 180 }} onClick={() => setIsSleepModalOpen(true)}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-6 h-6 rounded-full bg-indigo-100 flex items-center justify-center">
                <Moon className="w-3.5 h-3.5 text-indigo-500" />
              </div>
              <span className="font-semibold text-[#1a1a1a] text-sm">Sleep Last Night</span>
            </div>
            <div className="flex justify-center items-baseline gap-1 my-4">
              <span className="text-4xl font-bold text-[#1a1a1a]">{wellnessData.sleepHours !== null && wellnessData.sleepHours !== undefined ? wellnessData.sleepHours : '—'}</span>
              <span className="text-xl text-gray-400">h</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500 text-xs">Goal</span>
              <span className="text-gray-700 font-medium text-xs">{wellnessData.sleepGoal} h</span>
            </div>
          </MetricCard>
        </div>

        {/* Row 3: Water + Sunlight */}
        <div className="flex gap-4" style={{ height: 180 }}>
          {/* Water */}
          <MetricCard style={{ width: 180 }} onClick={() => setIsHydrationModalOpen(true)}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-6 h-6 rounded-full bg-cyan-100 flex items-center justify-center">
                <Droplet className="w-3.5 h-3.5 text-cyan-500" />
              </div>
              <span className="font-semibold text-[#1a1a1a] text-sm">Water</span>
            </div>
            <div className="flex justify-center my-2">
              <WaterProgress value={wellnessData.waterLiters} goal={wellnessData.waterGoal} />
            </div>
            <div className="flex justify-between items-center text-sm mt-1">
              <span className="text-gray-500 text-xs">Goal</span>
              <span className="text-gray-700 font-medium text-xs">{wellnessData.waterGoal} L</span>
            </div>
          </MetricCard>

          {/* Sunlight Exposure */}
          <MetricCard className="flex-1" onClick={() => setIsSunlightModalOpen(true)}>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-6 h-6 rounded-full bg-yellow-100 flex items-center justify-center">
                <Sun className="w-3.5 h-3.5 text-yellow-500" />
              </div>
              <div>
                <span className="font-semibold text-[#1a1a1a] text-sm">Sunlight Exposure</span>
                <span className="text-xs text-gray-500 ml-1">(Recommended)</span>
              </div>
            </div>
            <div className="flex gap-8 justify-center my-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-[#1a1a1a]">{wellnessData.sunlightToday !== null && wellnessData.sunlightToday !== undefined ? `${wellnessData.sunlightToday}min` : 'No data'}</div>
                <div className="text-sm text-gray-500 mt-1">Today</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-400">{wellnessData.sunlightYesterday}min</div>
                <div className="text-sm text-gray-500 mt-1">Yesterday</div>
              </div>
            </div>
          </MetricCard>

          {/* Physical Ease Score */}
          <MetricCard className="flex-1" onClick={() => setIsPhysicalEaseModalOpen(true)}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center">
                <Activity className="w-4 h-4 text-indigo-500" />
              </div>
              <span className="font-semibold text-[#1a1a1a]">Physical Ease</span>
            </div>
            <div className="flex items-center justify-center my-3 gap-6">
              <div className="relative inline-flex items-center justify-center w-[72px] h-[72px] rounded-full border-8 border-indigo-500">
                <span className="text-2xl font-bold text-[#1a1a1a]">{wellnessData.physicalEase !== null && wellnessData.physicalEase !== undefined ? wellnessData.physicalEase : '—'}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-gray-800">
                  {wellnessData.physicalEase !== null && wellnessData.physicalEase !== undefined 
                    ? (wellnessData.physicalEase >= 75 ? 'Comfortable & Ready' : wellnessData.physicalEase >= 55 ? 'Mild Strain' : 'Recovery Needed')
                    : 'No assessment'}
                </span>
                <span className="text-xs text-gray-500 mt-1">Score / 100</span>
              </div>
            </div>
          </MetricCard>
        </div>
      </div>

      {/* Physical Ease Modal */}
      {isPhysicalEaseModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6 relative shadow-xl">
            <button
              onClick={() => setIsPhysicalEaseModalOpen(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full p-1 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <PhysicalEaseForm
              isLoading={isSubmittingPhysicalEase}
              setIsLoading={setIsSubmittingPhysicalEase}
              onComplete={({ score, interpretation }) => {
                setIsPhysicalEaseModalOpen(false);
                onRefresh?.();
              }}
            />
          </div>
        </div>
      )}

      {/* Hydration Modal */}
      {isHydrationModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto p-6 relative shadow-xl">
            <button
              onClick={() => setIsHydrationModalOpen(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full p-1 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <HydrationForm
              isLoading={isSubmittingHydration}
              setIsLoading={setIsSubmittingHydration}
              onComplete={({ litersValue }) => {
                setIsHydrationModalOpen(false);
                onRefresh?.();
              }}
            />
          </div>
        </div>
      )}

      {/* Sleep Modal */}
      {isSleepModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto p-6 relative shadow-xl">
            <button
              onClick={() => setIsSleepModalOpen(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full p-1 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <SleepForm
              isLoading={isSubmittingSleep}
              setIsLoading={setIsSubmittingSleep}
              onComplete={({ hours }) => {
                setIsSleepModalOpen(false);
                onRefresh?.();
              }}
            />
          </div>
        </div>
      )}

      {/* PSS-10 Modal */}
      {isPssModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6 relative shadow-xl">
            <button
              onClick={() => setIsPssModalOpen(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full p-1 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <PSS10Form
              isLoading={isSubmittingPss}
              setIsLoading={setIsSubmittingPss}
              submitText="Submit Assessment"
              onComplete={() => {
                setIsPssModalOpen(false);
                onRefresh?.();
              }}
            />
          </div>
        </div>
      )}

      {/* Calories Modal */}
      {isCaloriesModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto p-6 relative shadow-xl">
            <button
              onClick={() => setIsCaloriesModalOpen(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full p-1 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <CaloriesForm
              isLoading={isSubmittingCalories}
              setIsLoading={setIsSubmittingCalories}
              onComplete={() => {
                setIsCaloriesModalOpen(false);
                onRefresh?.();
              }}
            />
          </div>
        </div>
      )}

      {/* Steps Modal */}
      {isStepsModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto p-6 relative shadow-xl">
            <button
              onClick={() => setIsStepsModalOpen(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full p-1 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <StepsForm
              isLoading={isSubmittingSteps}
              setIsLoading={setIsSubmittingSteps}
              onComplete={() => {
                setIsStepsModalOpen(false);
                onRefresh?.();
              }}
            />
          </div>
        </div>
      )}

      {/* Heart Rate Modal */}
      {isHeartRateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto p-6 relative shadow-xl">
            <button
              onClick={() => setIsHeartRateModalOpen(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full p-1 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <HeartRateForm
              isLoading={isSubmittingHeartRate}
              setIsLoading={setIsSubmittingHeartRate}
              onComplete={() => {
                setIsHeartRateModalOpen(false);
                onRefresh?.();
              }}
            />
          </div>
        </div>
      )}

      {/* Sunlight Modal */}
      {isSunlightModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto p-6 relative shadow-xl">
            <button
              onClick={() => setIsSunlightModalOpen(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full p-1 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
            <SunlightForm
              isLoading={isSubmittingSunlight}
              setIsLoading={setIsSubmittingSunlight}
              onComplete={() => {
                setIsSunlightModalOpen(false);
                onRefresh?.();
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
