import React, { useState, useEffect } from 'react';
import {
  User, Ruler, Heart, Activity, Moon, Apple, Target,
  ChevronRight, ChevronLeft, Check, X, Loader,
  Droplet, Dumbbell, Footprints, Brain, Flame
} from 'lucide-react';
import { profileAPI } from '../lib/api';

// ── Section Definitions ─────────────────────────────────────────────

const SECTIONS = [
  {
    id: 'basic_profile',
    title: 'Basic Profile',
    subtitle: 'Tell us about yourself',
    icon: User,
    gradient: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
  },
  {
    id: 'body_measurements',
    title: 'Body Measurements',
    subtitle: 'Optional body metrics',
    icon: Ruler,
    gradient: 'linear-gradient(135deg, #ec4899 0%, #f43f5e 100%)',
  },
  {
    id: 'body_fat',
    title: 'Body Fat Estimation',
    subtitle: 'Know your composition',
    icon: Flame,
    gradient: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
  },
  {
    id: 'biomarkers',
    title: 'Health Biomarkers',
    subtitle: 'Optional lab values',
    icon: Heart,
    gradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
  },
  {
    id: 'activity_lifestyle',
    title: 'Activity & Lifestyle',
    subtitle: 'Your movement habits',
    icon: Activity,
    gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
  },
  {
    id: 'sleep_stress',
    title: 'Sleep & Stress',
    subtitle: 'Recovery patterns',
    icon: Moon,
    gradient: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
  },
  {
    id: 'nutrition',
    title: 'Nutrition Baseline',
    subtitle: 'Your eating patterns',
    icon: Apple,
    gradient: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
  },
  {
    id: 'goals',
    title: 'Goal Setting',
    subtitle: 'What do you want to achieve?',
    icon: Target,
    gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
  },
];

// ── Stepper Progress Bar ────────────────────────────────────────────

function StepperProgress({ currentStep, totalSteps, sections }) {
  return (
    <div className="w-full mb-8">
      {/* Step counter */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-white/60">
          Step {currentStep + 1} of {totalSteps}
        </span>
        <span className="text-sm font-semibold text-white/90">
          {sections[currentStep]?.title}
        </span>
      </div>
      {/* Progress bar */}
      <div className="relative h-2 bg-white/10 rounded-full overflow-hidden">
        <div
          className="absolute left-0 top-0 h-full rounded-full transition-all duration-500 ease-out"
          style={{
            width: `${((currentStep + 1) / totalSteps) * 100}%`,
            background: sections[currentStep]?.gradient || 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          }}
        />
      </div>
      {/* Step dots */}
      <div className="flex justify-between mt-3">
        {sections.map((section, i) => {
          const Icon = section.icon;
          const isCompleted = i < currentStep;
          const isCurrent = i === currentStep;
          return (
            <div
              key={section.id}
              className={`flex flex-col items-center transition-all duration-300 ${
                isCurrent ? 'scale-110' : ''
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                  isCompleted
                    ? 'bg-emerald-500/80'
                    : isCurrent
                    ? 'bg-white/20 ring-2 ring-white/40'
                    : 'bg-white/5'
                }`}
              >
                {isCompleted ? (
                  <Check className="w-4 h-4 text-white" />
                ) : (
                  <Icon className={`w-3.5 h-3.5 ${isCurrent ? 'text-white' : 'text-white/30'}`} />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Input Components ────────────────────────────────────────────────

function FloatingInput({ label, value, onChange, type = 'text', placeholder, unit, optional }) {
  return (
    <div className="relative group">
      <label className="block text-sm font-medium text-white/70 mb-1.5">
        {label}
        {optional && <span className="text-white/30 ml-1 text-xs">(optional)</span>}
      </label>
      <div className="relative">
        <input
          type={type}
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/25 
                     focus:outline-none focus:border-white/30 focus:bg-white/8 focus:ring-1 focus:ring-white/20
                     transition-all duration-200 text-sm"
        />
        {unit && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 text-sm">{unit}</span>
        )}
      </div>
    </div>
  );
}

function SelectInput({ label, value, onChange, options, optional }) {
  return (
    <div>
      <label className="block text-sm font-medium text-white/70 mb-1.5">
        {label}
        {optional && <span className="text-white/30 ml-1 text-xs">(optional)</span>}
      </label>
      <select
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white
                   focus:outline-none focus:border-white/30 focus:ring-1 focus:ring-white/20
                   transition-all duration-200 text-sm appearance-none cursor-pointer"
        style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%23ffffff50' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3E%3C/svg%3E")`, backgroundPosition: 'right 0.75rem center', backgroundRepeat: 'no-repeat', backgroundSize: '1.25rem' }}
      >
        <option value="" className="bg-[#0f1d32]">Select...</option>
        {options.map(opt => (
          <option key={opt.value} value={opt.value} className="bg-[#0f1d32]">{opt.label}</option>
        ))}
      </select>
    </div>
  );
}

function SliderInput({ label, value, onChange, min = 1, max = 10, labels }) {
  const val = value || Math.ceil((max - min) / 2) + min;
  return (
    <div>
      <label className="block text-sm font-medium text-white/70 mb-1.5">{label}</label>
      <div className="relative pt-1">
        <input
          type="range"
          min={min}
          max={max}
          value={val}
          onChange={(e) => onChange(parseInt(e.target.value))}
          className="w-full h-2 rounded-full appearance-none cursor-pointer accent-[#6366f1]"
          style={{
            background: `linear-gradient(to right, #6366f1 0%, #6366f1 ${((val - min) / (max - min)) * 100}%, rgba(255,255,255,0.1) ${((val - min) / (max - min)) * 100}%, rgba(255,255,255,0.1) 100%)`,
          }}
        />
        <div className="flex justify-between mt-1.5">
          <span className="text-xs text-white/30">{labels?.[0] || min}</span>
          <span className="text-sm font-semibold text-white/90">{val}</span>
          <span className="text-xs text-white/30">{labels?.[1] || max}</span>
        </div>
      </div>
    </div>
  );
}

function ToggleChip({ label, selected, onClick, icon: Icon }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 border ${
        selected
          ? 'bg-[#6366f1]/20 border-[#6366f1]/50 text-white shadow-lg shadow-[#6366f1]/10'
          : 'bg-white/5 border-white/10 text-white/60 hover:bg-white/8 hover:border-white/20'
      }`}
    >
      {Icon && <Icon className={`w-4 h-4 ${selected ? 'text-[#6366f1]' : 'text-white/40'}`} />}
      {label}
    </button>
  );
}

// ── Section Forms ───────────────────────────────────────────────────

function BasicProfileSection({ data, onChange }) {
  const update = (field, value) => onChange({ ...data, [field]: value });
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <FloatingInput label="Age" value={data.age} onChange={(v) => update('age', v ? parseInt(v) : null)} type="number" placeholder="e.g. 28" unit="years" />
        <SelectInput 
          label="Sex" value={data.sex} onChange={(v) => update('sex', v)}
          options={[
            { value: 'male', label: 'Male' },
            { value: 'female', label: 'Female' },
            { value: 'other', label: 'Other' },
          ]}
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <FloatingInput label="Height" value={data.height} onChange={(v) => update('height', v ? parseFloat(v) : null)} type="number" placeholder="e.g. 175" unit="cm" />
        <FloatingInput label="Weight" value={data.weight} onChange={(v) => update('weight', v ? parseFloat(v) : null)} type="number" placeholder="e.g. 70" unit="kg" />
      </div>
    </div>
  );
}

function BodyMeasurementsSection({ data, onChange }) {
  const update = (field, value) => onChange({ ...data, [field]: value });
  return (
    <div className="space-y-5">
      <p className="text-sm text-white/40 -mt-1">These are optional but help us provide better body composition insights.</p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <FloatingInput label="Mid-Upper Arm" value={data.arm_circumference} onChange={(v) => update('arm_circumference', v ? parseFloat(v) : null)} type="number" placeholder="e.g. 30" unit="cm" optional />
        <FloatingInput label="Thigh" value={data.thigh_circumference} onChange={(v) => update('thigh_circumference', v ? parseFloat(v) : null)} type="number" placeholder="e.g. 55" unit="cm" optional />
        <FloatingInput label="Calf" value={data.calf_circumference} onChange={(v) => update('calf_circumference', v ? parseFloat(v) : null)} type="number" placeholder="e.g. 38" unit="cm" optional />
      </div>
    </div>
  );
}

function BodyFatSection({ data, onChange }) {
  return (
    <div className="space-y-5">
      <p className="text-sm text-white/40 -mt-1">If you know your body fat %, enter it below. Otherwise, select an estimate.</p>
      <FloatingInput label="Body Fat Percentage" value={data.body_fat_percent} onChange={(v) => onChange({ ...data, body_fat_percent: v ? parseFloat(v) : null })} type="number" placeholder="e.g. 18" unit="%" optional />
      <div>
        <label className="block text-sm font-medium text-white/70 mb-2">Or estimate your range</label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Athletic (8-15%)', value: 12 },
            { label: 'Fit (16-22%)', value: 19 },
            { label: 'Average (23-30%)', value: 26 },
            { label: 'Above Avg (30%+)', value: 33 },
          ].map((opt) => (
            <ToggleChip
              key={opt.value}
              label={opt.label}
              selected={data.body_fat_percent === opt.value}
              onClick={() => onChange({ ...data, body_fat_percent: opt.value })}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function BiomarkersSection({ data, onChange }) {
  const update = (field, value) => onChange({ ...data, [field]: value });
  const fields = [
    { key: 'vitamin_d', label: 'Vitamin D', placeholder: '30-100', unit: 'ng/mL' },
    { key: 'hba1c', label: 'HbA1c', placeholder: '4.0-5.6', unit: '%' },
    { key: 'tsh', label: 'Thyroid (TSH)', placeholder: '0.4-4.0', unit: 'mIU/L' },
    { key: 'b12', label: 'Vitamin B12', placeholder: '200-900', unit: 'pg/mL' },
    { key: 'hdl', label: 'HDL Cholesterol', placeholder: '40-60', unit: 'mg/dL' },
    { key: 'ldl', label: 'LDL Cholesterol', placeholder: '<100', unit: 'mg/dL' },
    { key: 'triglycerides', label: 'Triglycerides', placeholder: '<150', unit: 'mg/dL' },
    { key: 'ferritin', label: 'Ferritin', placeholder: '12-300', unit: 'ng/mL' },
    { key: 'hemoglobin', label: 'Hemoglobin', placeholder: '12-17', unit: 'g/dL' },
    { key: 'crp', label: 'CRP', placeholder: '<3.0', unit: 'mg/L' },
  ];
  return (
    <div className="space-y-5">
      <p className="text-sm text-white/40 -mt-1">If you have recent lab results, enter them here. All fields are optional.</p>
      <div className="grid grid-cols-2 gap-4">
        {fields.map((f) => (
          <FloatingInput key={f.key} label={f.label} value={data[f.key]} onChange={(v) => update(f.key, v ? parseFloat(v) : null)} type="number" placeholder={f.placeholder} unit={f.unit} optional />
        ))}
      </div>
    </div>
  );
}

function ActivityLifestyleSection({ data, onChange }) {
  const update = (field, value) => onChange({ ...data, [field]: value });
  return (
    <div className="space-y-5">
      <SelectInput
        label="Weekly Activity Level"
        value={data.activity_level}
        onChange={(v) => update('activity_level', v)}
        options={[
          { value: 'sedentary', label: 'Sedentary – Little to no exercise' },
          { value: 'lightly_active', label: 'Lightly Active – 1-2 days/week' },
          { value: 'moderately_active', label: 'Moderately Active – 3-5 days/week' },
          { value: 'very_active', label: 'Very Active – 6-7 days/week' },
          { value: 'extremely_active', label: 'Extremely Active – Intense daily training' },
        ]}
      />
      <SliderInput label="Exercise Frequency (days/week)" value={data.exercise_frequency} onChange={(v) => update('exercise_frequency', v)} min={0} max={7} labels={['0 days', '7 days']} />
      <FloatingInput label="Average Daily Steps" value={data.daily_steps} onChange={(v) => update('daily_steps', v ? parseInt(v) : null)} type="number" placeholder="e.g. 8000" unit="steps" />
    </div>
  );
}

function SleepStressSection({ data, onChange }) {
  const update = (field, value) => onChange({ ...data, [field]: value });
  return (
    <div className="space-y-5">
      <FloatingInput label="Average Sleep Duration" value={data.sleep_duration} onChange={(v) => update('sleep_duration', v ? parseFloat(v) : null)} type="number" placeholder="e.g. 7.5" unit="hours" />
      <SliderInput label="Sleep Consistency" value={data.sleep_consistency} onChange={(v) => update('sleep_consistency', v)} min={1} max={10} labels={['Very irregular', 'Very consistent']} />
      <SliderInput label="Perceived Stress Level" value={data.stress_level} onChange={(v) => update('stress_level', v)} min={1} max={10} labels={['Very low', 'Very high']} />
    </div>
  );
}

function NutritionSection({ data, onChange }) {
  const update = (field, value) => onChange({ ...data, [field]: value });
  return (
    <div className="space-y-5">
      <SliderInput label="Daily Meals" value={data.meal_frequency} onChange={(v) => update('meal_frequency', v)} min={1} max={6} labels={['1 meal', '6 meals']} />
      <SelectInput
        label="Daily Protein Intake"
        value={data.protein_intake}
        onChange={(v) => update('protein_intake', v)}
        options={[
          { value: 'low', label: 'Low – Rarely eat protein-rich foods' },
          { value: 'moderate', label: 'Moderate – Some protein in most meals' },
          { value: 'high', label: 'High – Protein in every meal' },
        ]}
      />
      <FloatingInput label="Daily Water Intake" value={data.water_intake} onChange={(v) => update('water_intake', v ? parseFloat(v) : null)} type="number" placeholder="e.g. 3" unit="litres" />
      <SelectInput
        label="Food Sourcing"
        value={data.food_source}
        onChange={(v) => update('food_source', v)}
        options={[
          { value: 'home_cooked', label: 'Mostly Home-Cooked' },
          { value: 'outside', label: 'Mostly Outside / Ordered' },
          { value: 'mixed', label: 'Mix of Both' },
        ]}
      />
    </div>
  );
}

function GoalSettingSection({ data, onChange }) {
  const goalOptions = [
    { type: 'improve_energy', label: 'Improve Energy', icon: Flame },
    { type: 'lose_fat', label: 'Lose Fat', icon: Activity },
    { type: 'build_muscle', label: 'Build Muscle', icon: Dumbbell },
    { type: 'improve_markers', label: 'Improve Health Markers', icon: Heart },
    { type: 'reduce_stress', label: 'Reduce Stress', icon: Brain },
    { type: 'better_sleep', label: 'Better Sleep', icon: Moon },
    { type: 'increase_steps', label: 'Increase Daily Steps', icon: Footprints },
    { type: 'hydration', label: 'Stay Hydrated', icon: Droplet },
  ];

  const selectedGoals = data.goals || [];

  const toggleGoal = (goalType) => {
    const exists = selectedGoals.find(g => g.goal_type === goalType);
    let newGoals;
    if (exists) {
      newGoals = selectedGoals.filter(g => g.goal_type !== goalType);
    } else {
      newGoals = [...selectedGoals, { goal_type: goalType, is_primary: selectedGoals.length === 0 }];
    }
    onChange({ ...data, goals: newGoals });
  };

  const setPrimary = (goalType) => {
    const updated = selectedGoals.map(g => ({
      ...g,
      is_primary: g.goal_type === goalType,
    }));
    onChange({ ...data, goals: updated });
  };

  return (
    <div className="space-y-5">
      <p className="text-sm text-white/40 -mt-1">Select your health goals. Click the ★ to set your primary objective.</p>
      <div className="grid grid-cols-2 gap-3">
        {goalOptions.map((opt) => {
          const selected = selectedGoals.find(g => g.goal_type === opt.type);
          const isPrimary = selected?.is_primary;
          return (
            <div
              key={opt.type}
              className={`relative flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 border cursor-pointer ${
                selected
                  ? 'bg-[#6366f1]/20 border-[#6366f1]/50 text-white'
                  : 'bg-white/5 border-white/10 text-white/60 hover:bg-white/8 hover:border-white/20'
              }`}
              onClick={() => toggleGoal(opt.type)}
            >
              <opt.icon className={`w-5 h-5 shrink-0 ${selected ? 'text-[#6366f1]' : 'text-white/30'}`} />
              <span className="flex-1">{opt.label}</span>
              {selected && (
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setPrimary(opt.type); }}
                  className={`text-lg transition-colors ${isPrimary ? 'text-amber-400' : 'text-white/20 hover:text-amber-300'}`}
                  title="Set as primary goal"
                >
                  ★
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Main Onboarding Questionnaire ───────────────────────────────────

export default function OnboardingQuestionnaire({ onComplete, onSkip }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  // Form data state
  const [profileData, setProfileData] = useState({ age: null, sex: '', height: null, weight: null });
  const [measurementData, setMeasurementData] = useState({ arm_circumference: null, thigh_circumference: null, calf_circumference: null });
  const [bodyFatData, setBodyFatData] = useState({ body_fat_percent: null });
  const [biomarkerData, setBiomarkerData] = useState({});
  const [activityData, setActivityData] = useState({ activity_level: '', exercise_frequency: 3, daily_steps: null });
  const [sleepStressData, setSleepStressData] = useState({ sleep_duration: null, sleep_consistency: 5, stress_level: 5 });
  const [nutritionData, setNutritionData] = useState({ meal_frequency: 3, protein_intake: '', water_intake: null, food_source: '' });
  const [goalData, setGoalData] = useState({ goals: [] });

  const totalSteps = SECTIONS.length;
  const isLastStep = currentStep === totalSteps - 1;

  const canProceed = () => {
    if (currentStep === 0) {
      // Basic Profile - require age, sex, height, weight
      return profileData.age && profileData.sex && profileData.height && profileData.weight;
    }
    // All other sections are optional
    return true;
  };

  const handleNext = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setSubmitError(null);

    // Assemble the payload
    const payload = {
      profile: {
        age: profileData.age,
        sex: profileData.sex || null,
        height: profileData.height,
        weight: profileData.weight,
        body_fat_percent: bodyFatData.body_fat_percent,
      },
      measurements: {
        arm_circumference: measurementData.arm_circumference,
        thigh_circumference: measurementData.thigh_circumference,
        calf_circumference: measurementData.calf_circumference,
      },
      biomarkers: Object.keys(biomarkerData).length > 0 ? biomarkerData : null,
      lifestyle: {
        activity_level: activityData.activity_level || null,
        exercise_frequency: activityData.exercise_frequency,
        daily_steps: activityData.daily_steps,
        sleep_duration: sleepStressData.sleep_duration,
        sleep_consistency: sleepStressData.sleep_consistency,
        stress_level: sleepStressData.stress_level,
        water_intake: nutritionData.water_intake,
        food_type: nutritionData.food_source || null,
      },
      nutrition: {
        meal_frequency: nutritionData.meal_frequency,
        protein_intake: nutritionData.protein_intake || null,
        water_intake: nutritionData.water_intake,
        food_source: nutritionData.food_source || null,
      },
      goals: goalData.goals.length > 0 ? goalData.goals : null,
    };

    try {
      await profileAPI.submitOnboarding(payload);
      onComplete?.();
    } catch (err) {
      console.error('Onboarding submission error:', err);
      setSubmitError(err.message || 'Failed to save your profile. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Render current section
  const renderSection = () => {
    switch (currentStep) {
      case 0: return <BasicProfileSection data={profileData} onChange={setProfileData} />;
      case 1: return <BodyMeasurementsSection data={measurementData} onChange={setMeasurementData} />;
      case 2: return <BodyFatSection data={bodyFatData} onChange={setBodyFatData} />;
      case 3: return <BiomarkersSection data={biomarkerData} onChange={setBiomarkerData} />;
      case 4: return <ActivityLifestyleSection data={activityData} onChange={setActivityData} />;
      case 5: return <SleepStressSection data={sleepStressData} onChange={setSleepStressData} />;
      case 6: return <NutritionSection data={nutritionData} onChange={setNutritionData} />;
      case 7: return <GoalSettingSection data={goalData} onChange={setGoalData} />;
      default: return null;
    }
  };

  const currentSection = SECTIONS[currentStep];
  const SectionIcon = currentSection.icon;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center overflow-hidden">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-[#050d1a]">
        {/* Animated gradient blobs */}
        <div
          className="absolute top-[-20%] left-[-10%] w-[700px] h-[700px] rounded-full opacity-30 animate-pulse"
          style={{
            background: 'radial-gradient(circle, rgba(99, 102, 241, 0.5) 0%, transparent 70%)',
            filter: 'blur(100px)',
            animationDuration: '4s',
          }}
        />
        <div
          className="absolute bottom-[-20%] right-[-10%] w-[600px] h-[600px] rounded-full opacity-25"
          style={{
            background: 'radial-gradient(circle, rgba(139, 92, 246, 0.4) 0%, transparent 70%)',
            filter: 'blur(80px)',
            animation: 'pulse 5s ease-in-out infinite',
          }}
        />
        <div
          className="absolute top-[40%] right-[20%] w-[500px] h-[500px] rounded-full opacity-20"
          style={{
            background: 'radial-gradient(circle, rgba(236, 72, 153, 0.3) 0%, transparent 70%)',
            filter: 'blur(90px)',
            animation: 'pulse 6s ease-in-out infinite reverse',
          }}
        />
        {/* DNA Helix */}
        <div className="absolute left-[50%] top-[-50px] w-[1000px] h-[900px] flex items-center justify-center pointer-events-none">
          <img
            src="/dna-helix.svg"
            alt=""
            className="w-[900px] h-[600px] opacity-[0.04] rotate-[27deg] object-contain"
          />
        </div>
      </div>

      {/* Content */}
      <div className="relative z-10 w-full max-w-[680px] mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 mb-4">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-medium text-white/60">Let's personalize your experience</span>
          </div>
          <h1 className="text-2xl font-bold text-white mb-1">
            Welcome to Nuetra
          </h1>
          <p className="text-sm text-white/50">
            Complete this quick questionnaire to unlock your personalized health dashboard
          </p>
        </div>

        {/* Stepper */}
        <StepperProgress currentStep={currentStep} totalSteps={totalSteps} sections={SECTIONS} />

        {/* Card */}
        <div
          className="rounded-2xl p-6 flex-1 overflow-y-auto"
          style={{
            background: 'linear-gradient(180deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%)',
            border: '1px solid rgba(71, 85, 105, 0.25)',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255,255,255,0.05)',
            maxHeight: '55vh',
          }}
        >
          {/* Section Header */}
          <div className="flex items-center gap-3 mb-6">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: currentSection.gradient }}
            >
              <SectionIcon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">{currentSection.title}</h2>
              <p className="text-xs text-white/50">{currentSection.subtitle}</p>
            </div>
          </div>

          {/* Section Content */}
          <div key={currentStep} className="animate-fadeIn">
            {renderSection()}
          </div>

          {/* Error */}
          {submitError && (
            <div className="mt-4 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20">
              <p className="text-sm text-red-400">{submitError}</p>
            </div>
          )}
        </div>

        {/* Footer Navigation */}
        <div className="flex items-center justify-between mt-6">
          <div className="flex gap-3">
            {currentStep > 0 && (
              <button
                onClick={handleBack}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium text-white/70 bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-200"
              >
                <ChevronLeft className="w-4 h-4" />
                Back
              </button>
            )}
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => {
                if (isLastStep) {
                  handleSubmit();
                } else {
                  handleNext();
                }
              }}
              className="px-5 py-2.5 rounded-xl text-sm font-medium text-white/40 hover:text-white/60 transition-colors"
              title="Skip this section and proceed"
            >
              Skip this section
            </button>

            {isLastStep ? (
              <button
                onClick={handleSubmit}
                disabled={isSubmitting || !canProceed()}
                className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
                  isSubmitting || !canProceed()
                    ? 'bg-[#6366f1]/40 text-white/50 cursor-not-allowed'
                    : 'bg-[#6366f1] text-white hover:bg-[#4f46e5] shadow-lg shadow-[#6366f1]/25'
                }`}
              >
                {isSubmitting ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    Complete Setup
                    <Check className="w-4 h-4" />
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={handleNext}
                disabled={!canProceed()}
                className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
                  !canProceed()
                    ? 'bg-[#6366f1]/40 text-white/50 cursor-not-allowed'
                    : 'bg-[#6366f1] text-white hover:bg-[#4f46e5] shadow-lg shadow-[#6366f1]/25'
                }`}
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Animated fade in keyframes via style */}
      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}
