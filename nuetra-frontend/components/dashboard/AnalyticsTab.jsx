// apps/web/frontend/components/dashboard/AnalyticsTab.jsx
import React, { useState } from 'react';
import { ChevronDown, Filter, Plus, TrendingUp, Smile } from 'lucide-react';

// Performance Gauge Component
function PerformanceGauge({ value = 567, maxValue = 1000 }) {
  const percentage = (value / maxValue) * 100;

  return (
    <div className="relative w-[343px] h-[197px]">
      <svg viewBox="0 0 343 197" className="w-full h-full">
        <defs>
          <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#EC4899" />
            <stop offset="52.6%" stopColor="#A855F7" />
            <stop offset="100%" stopColor="#3B82F6" />
          </linearGradient>
        </defs>
        {/* Background arc segments */}
        {Array.from({ length: 20 }).map((_, i) => {
          const angle = 180 + (i * 9);
          const isActive = i < Math.floor(percentage / 5);
          const x1 = 171.5 + 140 * Math.cos((angle * Math.PI) / 180);
          const y1 = 180 + 140 * Math.sin((angle * Math.PI) / 180);
          const x2 = 171.5 + 100 * Math.cos((angle * Math.PI) / 180);
          const y2 = 180 + 100 * Math.sin((angle * Math.PI) / 180);

          return (
            <line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={isActive ? `url(#gaugeGradient)` : '#BABDC6'}
              strokeWidth="12"
              strokeLinecap="round"
              style={{
                opacity: isActive ? 1 : 0.5,
              }}
            />
          );
        })}
      </svg>
      {/* Center value */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-baseline gap-1">
        <span className="text-[32px] font-normal text-black">{value}</span>
        <span className="text-sm text-black">point</span>
      </div>
    </div>
  );
}

// Bar Chart Component
function CaloriesChart({ data, activeDay = 3 }) {
  const days = ['Mon', 'Wed', 'Tue', 'Thu', 'Fri', 'Sat', 'Sun'];
  const yLabels = [2000, 1000, 500, 100, 0];
  const maxValue = 2000;

  return (
    <div className="relative w-full h-[184px]">
      {/* Y-axis labels */}
      <div className="absolute left-0 top-0 bottom-[23px] w-[30px] flex flex-col justify-between py-5">
        {yLabels.map((label, i) => (
          <span key={i} className="text-xs text-black text-right">{label}</span>
        ))}
      </div>

      {/* Chart area */}
      <div className="ml-[40px] h-[150px] relative">
        {/* Dashed lines */}
        <div className="absolute inset-0 flex flex-col justify-between">
          {yLabels.map((_, i) => (
            <div
              key={i}
              className={`w-full h-0 border-t-2 border-dashed ${i === 1 ? 'border-black' : 'border-black/10'}`}
            />
          ))}
        </div>

        {/* Bars */}
        <div className="absolute inset-0 flex justify-between items-end px-2">
          {data.map((value, i) => {
            const height = (value / maxValue) * 150;
            const isHighlighted = i === 2 || i === 3; // Tue and Thu

            return (
              <div key={i} className="relative flex flex-col items-center">
                {/* Tooltip for active */}
                {i === activeDay && (
                  <div className="absolute -top-8 bg-black text-white text-xs px-2.5 py-1.5 rounded">
                    {value}
                  </div>
                )}
                <div
                  className={`w-[30px] rounded-t-[20px] transition-all ${isHighlighted
                      ? 'bg-gradient-to-b from-[#EC4899] via-[#A855F7] to-[#3B82F6]'
                      : 'bg-[#c4c4c4]/40'
                    }`}
                  style={{ height: `${height}px` }}
                />
              </div>
            );
          })}
        </div>
      </div>

      {/* X-axis labels */}
      <div className="ml-[40px] flex justify-between px-2 pt-2">
        {days.map((day, i) => (
          <span key={i} className="text-xs text-black w-[30px] text-center">{day}</span>
        ))}
      </div>
    </div>
  );
}

// Nutrient Card Component
function NutrientCard({ icon, label, value, unit, isDark = false }) {
  return (
    <div className={`flex-1 p-2.5 rounded-xl ${isDark ? 'bg-black' : 'bg-[#F1F1F1]'}`}>
      <div
        className={`w-11 h-11 rounded-[10px] flex items-center justify-center mb-2.5 ${isDark ? 'bg-[#F3F3F3]' : label === 'Protein' ? 'bg-[#8EC4C4]' : 'bg-[#BABDC6]'
          }`}
      >
        {icon}
      </div>
      <div className="flex flex-col gap-1">
        <span className={`text-xs ${isDark ? 'text-white/60' : 'text-black/60'}`}>{label}</span>
        <div className="flex items-end gap-1">
          <span className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-black'}`}>{value}</span>
          <span className={`text-xs ${isDark ? 'text-white/60' : 'text-black/60'}`}>{unit}</span>
        </div>
      </div>
    </div>
  );
}

// Wellness Insight Card
function WellnessCard({ title, value, score, unit, className }) {
  return (
    <div
      className={`px-4 py-3 rounded-2xl flex flex-col justify-center min-w-[130px] max-w-[160px] ${className || ''}`}
      style={{
        background: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        border: '0.5px solid rgba(255, 255, 255, 0.5)',
      }}
    >
      <span className="text-[10px] font-medium text-white/80 uppercase tracking-wide mb-1">{title}</span>
      <div className="flex items-baseline gap-2">
        <div className="text-xl font-bold text-white capitalize">{value}</div>
        {(score !== undefined || unit) && (
          <span className="text-xs font-medium text-white/70">{unit ? unit : `${score}%`}</span>
        )}
      </div>
    </div>
  );
}

// Toggle Button Component
function ToggleButton({ options, active, onChange, fullWidth, bgClass }) {
  return (
    <div className={`flex items-center ${bgClass || 'bg-[#F6F6F6]'} rounded-[20px] p-0 ${fullWidth ? 'w-full' : 'w-fit'}`}>
      {options.map((option, i) => (
        <button
          key={option.key}
          onClick={() => onChange(option.key)}
          className={`px-4 py-2.5 rounded-[20px] text-[11px] font-medium transition-all ${
            fullWidth ? 'flex-1 text-center' : ''
          } ${active === option.key
              ? 'bg-black text-white'
              : 'text-black hover:bg-black/5'
            }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

// Metric Tab Button
function MetricTab({ label, isActive, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2.5 rounded-[20px] text-[10px] transition-all ${isActive ? 'bg-black text-white' : 'text-black'
        }`}
    >
      {label}
    </button>
  );
}

// Biomarker Chart Component
function BiomarkerChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-[250px] flex items-center justify-center bg-gray-50 rounded-xl mt-4 border border-dashed border-gray-300">
        <p className="text-sm text-gray-500">Please upload your health records to view your biomarker snapshot.</p>
      </div>
    );
  }

  return (
    <div className="w-full h-[220px] relative mt-8 mb-4">
      {/* Grid Lines */}
      {[
        { label: 'Optimal (100)', bottom: '100%' },
        { label: 'Borderline (70)', bottom: '70%' },
        { label: 'Poor (40)', bottom: '40%' },
      ].map((line, i) => (
        <div key={i} className="absolute w-full flex items-center gap-2 pointer-events-none z-0" style={{ bottom: line.bottom, transform: 'translateY(50%)' }}>
          <span className="text-[10px] text-gray-400 w-24 text-right pr-2">{line.label}</span>
          <div className="flex-1 h-px border-t border-dashed border-gray-200" />
        </div>
      ))}
      
      {/* Bars Container */}
      <div className="absolute inset-0 left-[104px] bottom-0 flex justify-between items-end pb-0 z-10">
        {data.map((item, index) => {
          let color = '#EF4444'; // Red for Poor
          if (item.score >= 70) color = '#F59E0B'; // Orange for Borderline
          if (item.score >= 100) color = '#10B981'; // Green for Optimal
          if (item.score === 0) color = 'transparent';

          return (
            <div key={index} className="flex flex-col items-center flex-1 group h-full justify-end relative">
              <div 
                className="w-8 rounded-t-md transition-all duration-700 hover:opacity-80"
                style={{ height: `${item.score}%`, backgroundColor: color }}
              >
                {/* Tooltip on hover */}
                <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-black text-white text-[10px] px-2 py-1 rounded pointer-events-none whitespace-nowrap transition-opacity z-20">
                  {item.label}: {item.score}
                </div>
              </div>
              <div className="absolute -bottom-8 w-full text-center flex justify-center">
                <span className="text-[9px] text-black font-medium text-center leading-tight w-[50px] break-words">
                  {item.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function AnalyticsTab({ dashboardStats, currentUser }) {
  const [timeRange, setTimeRange] = useState('today');
  const [analyticsTime, setAnalyticsTime] = useState('week');
  console.log("AnalyticsTab currentUser", currentUser);
  const [activeMetric, setActiveMetric] = useState('calories');
  const [wellnessView,  setWellnessView] = useState('insight');

  // Macro Calculations
  const profile = currentUser?.profile || {};
  const weight = profile.weight || 70; // kg default
  const height = profile.height || 170; // cm default
  const age = profile.age || 30;
  const sexValue = profile.sex === 'female' ? 0 : 1; // 1 for male, 0 for female
  
  // 1. BMI
  const heightInMeters = height / 100;
  const bmi = weight / (heightInMeters * heightInMeters);
  
  // 2. Body Fat %
  const calculatedBodyFat = (1.20 * bmi) + (0.23 * age) - (10.8 * sexValue) - 5.4;
  const bodyFatPercent = profile.body_fat_percent || calculatedBodyFat;
  
  // 3. LBM
  const lbm = weight - ((bodyFatPercent / 100) * weight);
  
  // 4. Macros
  const protein = Math.round(lbm * 1.8);
  const fat = Math.round(0.8 * weight);
  
  // 5. Total Calories (TDEE)
  const bmr = sexValue === 1 
    ? (10 * weight) + (6.25 * height) - (5 * age) + 5
    : (10 * weight) + (6.25 * height) - (5 * age) - 161;
  
  const activityLevel = currentUser?.lifestyle?.activity_level;
  let multiplier = 1.375;
  if (activityLevel === 'sedentary') multiplier = 1.2;
  if (activityLevel === 'moderately_active') multiplier = 1.55;
  if (activityLevel === 'very_active') multiplier = 1.725;
  if (activityLevel === 'extremely_active') multiplier = 1.9;
  
  const totalCalories = bmr * multiplier;
  const remainingCalories = totalCalories - (protein * 4) - (fat * 9);
  const carbs = Math.max(0, Math.round(remainingCalories / 4));

  const chartData = [800, 900, 1500, 1900, 700, 600, 500];

  const metrics = [
    { key: 'calories', label: 'Calories' },
    { key: 'heart-rate', label: 'Heart Rate' },
    { key: 'glucose', label: 'Glucose' },
    { key: 'blood', label: 'Blood Count' },
  ];

  // Biomarker scoring logic
  const getBiomarkerScore = (key, value) => {
    if (!value) return 0;
    switch(key) {
      case 'vitamin_d': return value > 30 ? 100 : value >= 20 ? 70 : 40;
      case 'hba1c': return value < 5.7 ? 100 : value <= 6.4 ? 70 : 40;
      case 'tsh': return (value >= 0.4 && value <= 4.0) ? 100 : (value > 4.0 && value <= 5.0) ? 70 : 40;
      case 'b12': return value > 300 ? 100 : value >= 200 ? 70 : 40;
      case 'hdl': return value > 50 ? 100 : value >= 40 ? 70 : 40;
      case 'ldl': return value < 100 ? 100 : value <= 129 ? 70 : 40;
      case 'triglycerides': return value < 150 ? 100 : value <= 199 ? 70 : 40;
      case 'ferritin': return (value >= 30 && value <= 200) ? 100 : (value >= 15 && value <= 300) ? 70 : 40;
      case 'hemoglobin': return (value >= 12 && value <= 17) ? 100 : (value >= 10 && value < 12) ? 70 : 40;
      case 'crp': return value < 1 ? 100 : value <= 3 ? 70 : 40;
      default: return 0;
    }
  };

  const biomarkers = currentUser?.biomarkers || {};
  const hasBiomarkers = Object.values(biomarkers).some(v => v !== null && v !== undefined);
  
  const biomarkerData = hasBiomarkers ? [
    { label: 'Vitamin D', score: getBiomarkerScore('vitamin_d', biomarkers.vitamin_d) },
    { label: 'HbA1c', score: getBiomarkerScore('hba1c', biomarkers.hba1c) },
    { label: 'Thyroid', score: getBiomarkerScore('tsh', biomarkers.tsh) },
    { label: 'B12', score: getBiomarkerScore('b12', biomarkers.b12) },
    { label: 'Lipid Profile', score: Math.round((getBiomarkerScore('hdl', biomarkers.hdl) + getBiomarkerScore('ldl', biomarkers.ldl) + getBiomarkerScore('triglycerides', biomarkers.triglycerides)) / 3) || 0 },
    { label: 'Ferritin', score: getBiomarkerScore('ferritin', biomarkers.ferritin) },
    { label: 'Hemoglobin', score: getBiomarkerScore('hemoglobin', biomarkers.hemoglobin) },
    { label: 'CRP', score: getBiomarkerScore('crp', biomarkers.crp) },
  ] : [];

  const validScores = biomarkerData.filter(d => d.score > 0);
  const medicalIndex = validScores.length > 0 
    ? Math.round(validScores.reduce((acc, curr) => acc + curr.score, 0) / validScores.length)
    : 0;

  const fileInputRef = React.useRef(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleUploadReport = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsUploading(true);
    try {
      const { profileAPI } = await import('../../lib/api');
      await profileAPI.uploadReport(file);
      alert('Health report uploaded successfully. Please refresh to see the updated snapshot!');
      window.location.reload();
    } catch (err) {
      alert('Failed to upload report: ' + err.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex gap-4">
      {/* Left Column - Active Performance */}
      <div
        className="w-[407px] shrink-0 p-4 rounded-2xl flex flex-col gap-4"
        style={{
          background: 'linear-gradient(180deg, #FCFCFC 0%, #F2F2F7 100%)',
          border: '1px solid #E7E7E9',
          boxShadow: 'inset 0px 4px 4px -1px rgba(12, 12, 13, 0.05)',
        }}
      >
        {/* Time Toggle */}
        <ToggleButton
          options={[
            { key: 'today', label: 'Today' },
            { key: 'week', label: 'This Week' },
          ]}
          active={timeRange}
          onChange={setTimeRange}
        />

        {/* Performance Section */}
        <div className="flex flex-col items-center px-4 gap-4">
          <div className="flex justify-between items-center w-full">
            <h3 className="text-xl font-bold text-black">Active Performance</h3>
            <div className="flex items-center gap-1">
              <span className="text-sm text-black">+10%</span>
              <TrendingUp className="w-4 h-4 text-[#19AA41]" />
            </div>
          </div>

          <PerformanceGauge value={dashboardStats?.performanceScore ? Math.round(dashboardStats.performanceScore * 10) : 0} />

          {/* Health Message */}
          <div className="w-full flex items-center gap-2.5 p-1.5 bg-white border border-black/20 rounded-[20px]">
            <div className="w-[30px] h-[30px] bg-[#19AA41] rounded-full flex items-center justify-center">
              <Smile className="w-5 h-5 text-white" />
            </div>
            <span className="text-xs text-black flex-1">You're healthier than 85% people!</span>
          </div>
        </div>

        {/* Health Records Card */}
        <div
          className="flex-1 p-4 rounded-3xl flex flex-col justify-between"
          style={{
            background: '#000000',
            border: '1px solid rgba(216, 216, 216, 0.2)',
          }}
        >
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <div className="w-12 h-12 bg-white/80 rounded-full flex items-center justify-center">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                  <path d="M14 3L17 10H24L18 15L20 23L14 18L8 23L10 15L4 10H11L14 3Z" fill="#FF0000" />
                </svg>
              </div>
              <span className="text-xl font-bold text-white">Your Health Records</span>
            </div>
            <div className="px-2.5 py-1 border border-white rounded-[20px] w-fit">
              <span className="text-xs text-white">{hasBiomarkers ? "Report Available" : "No Report Found"}</span>
            </div>
          </div>

          <div className="flex justify-between items-center">
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept=".pdf,.png,.jpg,.jpeg" 
              onChange={handleUploadReport} 
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="w-[52px] h-[52px] bg-white/80 rounded-full flex items-center justify-center hover:bg-white transition-colors disabled:opacity-50"
            >
              <Plus className="w-8 h-8 text-black" />
            </button>
            <div className="flex gap-2.5">
              {[0, 1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className={`w-2.5 h-2.5 rounded-full ${i === 1 ? 'bg-red-500' : 'bg-gray-400'}`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Middle Column - Analytics */}
      <div
        className="w-[407px] shrink-0 p-4 rounded-2xl flex flex-col gap-10"
        style={{
          background: 'linear-gradient(180deg, #FCFCFC 0%, #F2F2F7 100%)',
          border: '1px solid #E7E7E9',
          boxShadow: 'inset 0px 4px 4px -1px rgba(12, 12, 13, 0.05)',
        }}
      >
        {/* Header */}
        <div className="flex flex-col gap-6">
          <div className="flex justify-between items-center">
            <div className="flex flex-col">
              <h3 className="text-xl font-bold text-black">Health Biomarker Snapshot</h3>
              {hasBiomarkers && (
                <span className="text-sm text-gray-500 mt-1">
                  Medical Index: <strong className="text-black">{medicalIndex}</strong> / 100
                </span>
              )}
            </div>
            <div className="flex items-center gap-1">
              <button className="flex items-center gap-1 px-4 py-2.5 bg-[#F6F6F6] rounded-[20px]">
                <span className="text-xs text-black">Latest Report</span>
                <ChevronDown className="w-5 h-5 text-black" />
              </button>
            </div>
          </div>
        </div>

        {/* Chart Section */}
        <div className="flex flex-col gap-6 w-full">
          <BiomarkerChart data={biomarkerData} />
        </div>

        {/* Nutrient Cards */}
        <div className="flex flex-col gap-2">
          <div className="flex gap-2.5">
            <NutrientCard
              icon={<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 2C13 4 16 6 16 10C16 14 13 16 12 16C11 16 8 14 8 10C8 6 11 4 12 2Z" fill="#1C1B1F" /></svg>}
              label="Protein"
              value={protein}
              unit="gram"
            />
            <NutrientCard
              icon={<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="8" fill="#1C1B1F" /></svg>}
              label="Fat"
              value={fat}
              unit="gram"
            />
            <NutrientCard
              icon={<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><rect x="4" y="4" width="16" height="16" rx="2" fill="#1C1B1F" /></svg>}
              label="Carbs"
              value={carbs}
              unit="gram"
              isDark
            />
          </div>
          <p className="text-[10px] text-gray-400 italic">
            * Body fat % is an estimated value based on available inputs.
          </p>
        </div>
      </div>

      {/* Right Column - Wellness Insight */}
      <div
        className="flex-1 rounded-[36px] relative overflow-hidden"
        style={{ minHeight: 668 }}
      >
        {/* Background with blur */}
        <div
          className="absolute inset-0"
          style={{
            background: 'linear-gradient(180deg, #1a2744 0%, #0f1829 50%, #1a3a5c 100%)',
          }}
        />
        <div
          className="absolute inset-0 opacity-20"
          style={{
            background: 'rgba(128, 128, 128, 0.2)',
            backdropFilter: 'blur(10px)',
          }}
        />

        {/* Content */}
        <div className="relative z-10 p-6 h-full flex flex-col">
          {/* Toggle */}
          <div className="mb-6 w-full flex justify-center">
            <ToggleButton
              options={[
                { key: 'insight', label: 'Wellness Insight' },
                { key: 'measurements', label: 'Measurements' },
              ]}
              active={wellnessView}
              onChange={setWellnessView}
              bgClass="bg-white"
            />
          </div>

          {/* Body Visualization Area */}
          <div className="flex-1 relative w-full flex items-center justify-center mt-2">
            
            {/* The Base Illustration */}
            <div className="absolute bottom-[20px] w-full flex justify-center">
              <img
                src="/baseIllustration.png"
                alt="Base platform"
                className="w-[240px] object-contain opacity-90"
              />
            </div>

            {/* The Person Model (Biomarker View) */}
            <div className="absolute bottom-[90px] w-full flex justify-center z-10 pointer-events-none">
              <img
                src="/freepik.png"
                alt="Body visualization"
                className="h-[420px] object-contain"
              />
            </div>
            
            {/* Left Side Cards */}
            <div className="absolute left-[10px] top-[160px] flex flex-col gap-[60px] z-20">
              {wellnessView === 'insight' ? (
                <>
                  <WellnessCard 
                    title="Energy Balance" 
                    value={dashboardStats?.energyBalance >= 80 ? 'Good' : dashboardStats?.energyBalance >= 60 ? 'Stable' : 'Needs attention'}
                    score={dashboardStats?.energyBalance || 82}
                  />
                  <WellnessCard 
                    title="Body Support Strength" 
                    value={dashboardStats?.bodySupport >= 80 ? 'Good' : dashboardStats?.bodySupport >= 60 ? 'Stable' : 'Needs attention'}
                    score={dashboardStats?.bodySupport || 65}
                  />
                </>
              ) : (
                <>
                  <WellnessCard 
                    title="Body Weight" 
                    value={profile?.weight ? profile.weight : '--'}
                    unit="kg"
                  />
                  <WellnessCard 
                    title="Mid-Upper Arm" 
                    value={currentUser?.measurements?.arm_circumference || '--'}
                    unit="cm"
                  />
                </>
              )}
            </div>

            {/* Right Side Cards */}
            <div className="absolute right-[10px] top-[160px] flex flex-col gap-[60px] z-20">
              {wellnessView === 'insight' ? (
                <>
                  <WellnessCard 
                    title="Nourishment Level" 
                    value={dashboardStats?.nourishmentScore >= 80 ? 'Good' : dashboardStats?.nourishmentScore >= 60 ? 'Stable' : 'Needs attention'}
                    score={dashboardStats?.nourishmentScore || 90}
                  />
                  <WellnessCard 
                    title="Recovery Readiness" 
                    value={dashboardStats?.recoveryScore >= 80 ? 'Good' : dashboardStats?.recoveryScore >= 60 ? 'Improving' : 'Needs attention'}
                    score={dashboardStats?.recoveryScore || 74}
                  />
                </>
              ) : (
                <>
                  <WellnessCard 
                    title="Body Fat" 
                    value={profile?.body_fat_percent ? profile.body_fat_percent : (profile?.weight ? bodyFatPercent.toFixed(1) : '--')}
                    unit="%"
                  />
                  <WellnessCard 
                    title="Thigh Size" 
                    value={currentUser?.measurements?.thigh_circumference || '--'}
                    unit="cm"
                  />
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

