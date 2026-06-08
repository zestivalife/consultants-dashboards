import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import { profileAPI, authAPI, apiRequest } from '../lib/api';
import { getDashboardPathForRole } from '../lib/roleRoutes';
import ProtectedRoute from '../components/ProtectedRoute';
import DashboardHeader from '../components/DashboardHeader';
import Link from 'next/link';
import {
  User, Mail, Phone, Camera, Lock, Save, X,
  AlertCircle, CheckCircle, Loader2, ArrowLeft, Info,
  Heart, Ruler, Activity, Moon, Apple, Target, Flame
} from 'lucide-react';

function SectionCard({ title, icon: Icon, children }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm mb-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center border border-blue-100">
          <Icon className="w-5 h-5 text-[#237afc]" />
        </div>
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function InputField({ label, name, value, onChange, type = "text", placeholder, unit, disabled }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <div className="relative">
        <input
          type={type}
          name={name}
          value={value === null ? '' : value}
          onChange={onChange}
          disabled={disabled}
          placeholder={placeholder}
          className={`w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#237afc] focus:border-transparent transition-all ${disabled ? 'opacity-50 cursor-not-allowed bg-gray-50' : ''}`}
        />
        {unit && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm font-medium">
            {unit}
          </span>
        )}
      </div>
    </div>
  );
}

function SelectField({ label, name, value, onChange, options }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <select
        name={name}
        value={value || ''}
        onChange={onChange}
        className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#237afc] focus:border-transparent transition-all appearance-none"
        style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3E%3C/svg%3E")`, backgroundPosition: 'right 0.5rem center', backgroundRepeat: 'no-repeat', backgroundSize: '1.25rem' }}
      >
        <option value="" className="bg-white text-gray-900">Select...</option>
        {options.map(opt => (
          <option key={opt.value} value={opt.value} className="bg-white text-gray-900">{opt.label}</option>
        ))}
      </select>
    </div>
  );
}

function SliderField({ label, name, value, onChange, min, max, labels }) {
  const val = value || Math.ceil((max - min) / 2) + min;
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <div className="relative pt-2">
        <input
          type="range"
          min={min}
          max={max}
          name={name}
          value={val}
          onChange={(e) => onChange({ target: { name, value: parseInt(e.target.value) } })}
          className="w-full h-2 bg-gray-200 rounded-full appearance-none accent-[#237afc] cursor-pointer"
        />
        <div className="flex justify-between mt-2">
          <span className="text-xs text-gray-500">{labels?.[0] || min}</span>
          <span className="text-sm font-semibold text-gray-900">{val}</span>
          <span className="text-xs text-gray-500">{labels?.[1] || max}</span>
        </div>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const router = useRouter();
  const { user: authUser } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // States
  const [identity, setIdentity] = useState({ firstName: '', lastName: '', email: '', phone: '', avatar: '' });
  const [profile, setProfile] = useState({ age: '', sex: '', height: '', weight: '', body_fat_percent: '' });
  const [measurements, setMeasurements] = useState({ arm_circumference: '', thigh_circumference: '', calf_circumference: '' });
  const [biomarkers, setBiomarkers] = useState({ vitamin_d: '', hba1c: '', tsh: '', b12: '', hdl: '', ldl: '', triglycerides: '', ferritin: '', hemoglobin: '', crp: '' });
  const [lifestyle, setLifestyle] = useState({ activity_level: '', exercise_frequency: '', daily_steps: '', sleep_duration: '', sleep_consistency: '', stress_level: '' });
  const [nutrition, setNutrition] = useState({ meal_frequency: '', protein_intake: '', water_intake: '', food_source: '' });
  const [goals, setGoals] = useState([]);
  const [hasProfile, setHasProfile] = useState(true);

  useEffect(() => {
    fetchData();
  }, [authUser]);

  const fetchData = async () => {
    if (!authUser) return;
    try {
      setLoading(true);
      
      // Fetch auth identity
      let authInfo = authUser;
      try {
        authInfo = await authAPI.me();
      } catch (e) {
        console.warn('Could not fetch rich auth info, using context data');
      }
      setIdentity({
        firstName: authInfo.first_name || authInfo.firstName || '',
        lastName: authInfo.last_name || authInfo.lastName || '',
        email: authInfo.email || '',
        phone: authInfo.phone || '',
        avatar: authInfo.avatar || ''
      });

      // Fetch health profile
      try {
        const pData = await profileAPI.me();
        setHasProfile(true);
        if (pData.profile) setProfile(pData.profile);
        if (pData.measurements) setMeasurements(pData.measurements);
        if (pData.biomarkers) setBiomarkers(pData.biomarkers);
        if (pData.lifestyle) setLifestyle(pData.lifestyle);
        if (pData.nutrition) setNutrition(pData.nutrition);
        if (pData.goals) setGoals(pData.goals);
      } catch (err) {
        if (err.status === 404) {
          setHasProfile(false);
          setError('We could not find your health profile. Please fill it out below to complete your setup.');
        } else {
          setError('Failed to load health profile metrics.');
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (setter) => (e) => {
    const { name, value } = e.target;
    setter(prev => ({ ...prev, [name]: value === '' ? null : value }));
  };

  const handleGoalToggle = (goalType) => {
    setGoals(prev => {
      const exists = prev.find(g => g.goal_type === goalType);
      if (exists) return prev.filter(g => g.goal_type !== goalType);
      return [...prev, { goal_type: goalType, is_primary: prev.length === 0 }];
    });
  };

  const handleGoalPrimary = (e, goalType) => {
    e.stopPropagation();
    setGoals(prev => prev.map(g => ({ ...g, is_primary: g.goal_type === goalType })));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      // Macro calculations
      const weight = parseFloat(profile.weight) || 70;
      const height = parseFloat(profile.height) || 170;
      const age = parseInt(profile.age) || 30;
      const sexValue = profile.sex === 'female' ? 0 : 1;
      
      const heightInMeters = height / 100;
      const bmi = weight / (heightInMeters * heightInMeters);
      const calculatedBodyFat = (1.20 * bmi) + (0.23 * age) - (10.8 * sexValue) - 5.4;
      
      const bodyFatPercent = parseFloat(profile.body_fat_percent) || calculatedBodyFat;
      const lbm = weight - ((bodyFatPercent / 100) * weight);
      
      const targetProtein = Math.round(lbm * 1.8);
      const targetFat = Math.round(0.8 * weight);
      
      const bmr = sexValue === 1 
        ? (10 * weight) + (6.25 * height) - (5 * age) + 5
        : (10 * weight) + (6.25 * height) - (5 * age) - 161;
      
      const activityLevel = lifestyle.activity_level;
      let multiplier = 1.375;
      if (activityLevel === 'sedentary') multiplier = 1.2;
      if (activityLevel === 'moderately_active') multiplier = 1.55;
      if (activityLevel === 'very_active') multiplier = 1.725;
      if (activityLevel === 'extremely_active') multiplier = 1.9;
      
      const totalCalories = Math.round(bmr * multiplier);
      const remainingCalories = totalCalories - (targetProtein * 4) - (targetFat * 9);
      const targetCarbs = Math.max(0, Math.round(remainingCalories / 4));

      const payload = {
        profile: {
          age: parseInt(profile.age) || null,
          sex: profile.sex || null,
          height: parseFloat(profile.height) || null,
          weight: parseFloat(profile.weight) || null,
          body_fat_percent: parseFloat(profile.body_fat_percent) || null,
          calculated_body_fat: calculatedBodyFat,
        },
        measurements: {
          arm_circumference: parseFloat(measurements.arm_circumference) || null,
          thigh_circumference: parseFloat(measurements.thigh_circumference) || null,
          calf_circumference: parseFloat(measurements.calf_circumference) || null,
        },
        biomarkers: Object.keys(biomarkers).reduce((acc, k) => {
          if (biomarkers[k] !== null && biomarkers[k] !== '') {
            acc[k] = parseFloat(biomarkers[k]);
          }
          return acc;
        }, {}),
        lifestyle: {
          activity_level: lifestyle.activity_level || null,
          exercise_frequency: parseInt(lifestyle.exercise_frequency) || null,
          daily_steps: parseInt(lifestyle.daily_steps) || null,
          sleep_duration: parseFloat(lifestyle.sleep_duration) || null,
          sleep_consistency: parseInt(lifestyle.sleep_consistency) || null,
          stress_level: parseInt(lifestyle.stress_level) || null,
        },
        nutrition: {
          meal_frequency: parseInt(nutrition.meal_frequency) || null,
          protein_intake: nutrition.protein_intake || null,
          water_intake: parseFloat(nutrition.water_intake) || null,
          food_source: nutrition.food_source || null,
          target_protein: targetProtein,
          target_fat: targetFat,
          target_carbs: targetCarbs,
          target_calories: totalCalories,
        },
        goals: goals.length > 0 ? goals : null,
      };

      // Ensure object is not empty for biomarkers, etc
      if (Object.keys(payload.biomarkers).length === 0) payload.biomarkers = null;

      if (!hasProfile) {
        await profileAPI.create(payload);
        setHasProfile(true);
      } else {
        await profileAPI.update(payload);
      }
      
      setSuccess('Profile successfully updated!');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(err.message || 'An error occurred while saving.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-[#237afc]" />
      </div>
    );
  }

  const goalOptions = [
    { type: 'improve_energy', label: 'Improve Energy' },
    { type: 'lose_fat', label: 'Lose Fat' },
    { type: 'build_muscle', label: 'Build Muscle' },
    { type: 'improve_markers', label: 'Improve Health Markers' },
    { type: 'reduce_stress', label: 'Reduce Stress' },
    { type: 'better_sleep', label: 'Better Sleep' },
    { type: 'increase_steps', label: 'Increase Daily Steps' },
    { type: 'hydration', label: 'Stay Hydrated' },
  ];

  return (
    <ProtectedRoute>
      <div className="min-h-screen relative overflow-hidden">
        {/* Background Gradient Pack - matching dashboard design */}
        <div className="absolute inset-0 bg-[#f4faff]">
          {/* Pink gradient blob - top left */}
          <div
            className="absolute -left-[400px] -top-[400px] w-[1000px] h-[1000px] rounded-full"
            style={{
              background: 'radial-gradient(circle, rgba(255, 208, 208, 0.8) 0%, rgba(255, 220, 220, 0.4) 40%, transparent 70%)',
              filter: 'blur(80px)'
            }}
          />
          {/* Pink gradient blob - right side */}
          <div
            className="absolute -right-[100px] top-[50px] w-[800px] h-[800px] rounded-full"
            style={{
              background: 'radial-gradient(circle, rgba(255, 208, 208, 0.7) 0%, rgba(255, 200, 200, 0.3) 50%, transparent 70%)',
              filter: 'blur(80px)'
            }}
          />
        </div>

        {/* Header */}
        <div className="relative z-[100]">
          <DashboardHeader
            searchPlaceholder="Search"
            notificationCount={0}
            showNavLinks={false}
          />
        </div>

        {/* Main Content */}
        <div className="relative z-10 max-w-[1600px] mx-auto px-8 py-8">
          {/* Breadcrumb */}
          <Link
            href={authUser ? getDashboardPathForRole(authUser.role, '/dashboard/team-member') : '#'}
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Dashboard
          </Link>

          {/* Page Title */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Your Profile</h1>
              <p className="text-gray-600 mt-2">Manage your health metrics and personal information</p>
            </div>
            <div className="flex bg-white border border-gray-200 rounded-full p-2 shadow-sm">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#237afc] to-[#1a5fc7] flex items-center justify-center text-xl font-bold uppercase shadow-md border-2 border-white">
                {identity.firstName?.[0] || ''}{identity.lastName?.[0] || ''}
              </div>
            </div>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <p className="text-red-700 text-sm">{error}</p>
              </motion.div>
            )}
            {success && (
              <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="mb-6 p-4 rounded-lg bg-green-50 border border-green-200 flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <p className="text-green-700 text-sm">{success}</p>
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} className="space-y-6">

            {/* Profile Form Card */}
            <div className="bg-white border border-[#f2f2f7] rounded-2xl p-6 shadow-[0px_4px_4px_-1px_rgba(12,12,13,0.1),0px_4px_4px_-1px_rgba(12,12,13,0.05)]">
            
            {/* Identity Info (Read-only since auth service update is separate) */}
            <SectionCard title="Contact Information" icon={User}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <InputField label="First Name" name="firstName" value={identity.firstName} disabled />
                <InputField label="Last Name" name="lastName" value={identity.lastName} disabled />
                <InputField label="Email Address" name="email" value={identity.email} disabled />
                <InputField label="Phone Number" name="phone" value={identity.phone} disabled />
              </div>
              <p className="mt-4 text-xs text-gray-500 flex items-center gap-1">
                <Info className="w-3 h-3" /> Note: Identity fields are managed by Corporate/HR.
              </p>
            </SectionCard>

            <SectionCard title="Basic Health Metrics" icon={Activity}>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <InputField label="Age" name="age" type="number" unit="yrs" value={profile.age} onChange={handleChange(setProfile)} />
                <SelectField label="Sex" name="sex" options={[{value:'male',label:'Male'}, {value:'female',label:'Female'}, {value:'other',label:'Other'}]} value={profile.sex} onChange={handleChange(setProfile)} />
                <InputField label="Height" name="height" type="number" unit="cm" value={profile.height} onChange={handleChange(setProfile)} />
                <InputField label="Weight" name="weight" type="number" unit="kg" value={profile.weight} onChange={handleChange(setProfile)} />
              </div>
              <div className="mt-6 border-t border-gray-200 pt-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2"><Flame className="w-4 h-4 text-red-600" /> Composition</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <InputField label="Body Fat %" name="body_fat_percent" type="number" unit="%" value={profile.body_fat_percent} onChange={handleChange(setProfile)} />
                </div>
              </div>
            </SectionCard>

            <SectionCard title="Measurements" icon={Ruler}>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <InputField label="Mid-Upper Arm" name="arm_circumference" type="number" unit="cm" value={measurements.arm_circumference} onChange={handleChange(setMeasurements)} />
                <InputField label="Thigh" name="thigh_circumference" type="number" unit="cm" value={measurements.thigh_circumference} onChange={handleChange(setMeasurements)} />
                <InputField label="Calf" name="calf_circumference" type="number" unit="cm" value={measurements.calf_circumference} onChange={handleChange(setMeasurements)} />
              </div>
            </SectionCard>

            <SectionCard title="Lifestyle & Stress" icon={Moon}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-6">
                  <SelectField
                    label="Weekly Activity Level" name="activity_level" value={lifestyle.activity_level} onChange={handleChange(setLifestyle)}
                    options={[
                      { value: 'sedentary', label: 'Sedentary' },
                      { value: 'lightly_active', label: 'Lightly Active' },
                      { value: 'moderately_active', label: 'Moderately Active' },
                      { value: 'very_active', label: 'Very Active' },
                      { value: 'extremely_active', label: 'Extremely Active' },
                    ]}
                  />
                  <InputField label="Daily Steps" name="daily_steps" type="number" unit="steps" value={lifestyle.daily_steps} onChange={handleChange(setLifestyle)} />
                  <InputField label="Sleep Duration" name="sleep_duration" type="number" unit="hrs" value={lifestyle.sleep_duration} onChange={handleChange(setLifestyle)} />
                </div>
                <div className="space-y-6 bg-blue-50 p-5 rounded-lg border border-blue-100">
                  <SliderField label="Exercise Frequency (days)" name="exercise_frequency" min={0} max={7} value={lifestyle.exercise_frequency} onChange={handleChange(setLifestyle)} />
                  <SliderField label="Sleep Consistency (1-10)" name="sleep_consistency" min={1} max={10} value={lifestyle.sleep_consistency} onChange={handleChange(setLifestyle)} />
                  <SliderField label="Stress Level (1-10)" name="stress_level" min={1} max={10} value={lifestyle.stress_level} onChange={handleChange(setLifestyle)} />
                </div>
              </div>
            </SectionCard>

            <SectionCard title="Nutrition & Diet" icon={Apple}>
               <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-6">
                  <SliderField label="Daily Meals" name="meal_frequency" min={1} max={6} value={nutrition.meal_frequency} onChange={handleChange(setNutrition)} />
                  <InputField label="Water Intake" name="water_intake" type="number" unit="litres" value={nutrition.water_intake} onChange={handleChange(setNutrition)} />
                </div>
                <div className="space-y-6">
                  <SelectField
                    label="Protein Intake" name="protein_intake" value={nutrition.protein_intake} onChange={handleChange(setNutrition)}
                    options={[{ value: 'low', label: 'Low' }, { value: 'moderate', label: 'Moderate' }, { value: 'high', label: 'High' }]}
                  />
                  <SelectField
                    label="Food Sourcing" name="food_source" value={nutrition.food_source} onChange={handleChange(setNutrition)}
                    options={[{ value: 'home_cooked', label: 'Home-Cooked' }, { value: 'outside', label: 'Outside / Ordered' }, { value: 'mixed', label: 'Mixed' }]}
                  />
                </div>
              </div>
            </SectionCard>

            <SectionCard title="Goals & Objectives" icon={Target}>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {goalOptions.map(opt => {
                  const isActive = goals.find(g => g.goal_type === opt.type);
                  const isPrimary = isActive?.is_primary;
                  return (
                    <div
                      key={opt.type}
                      onClick={() => handleGoalToggle(opt.type)}
                      className={`relative flex items-center p-4 rounded-lg cursor-pointer border transition-all duration-200 ${isActive ? 'bg-blue-50 border-[#237afc]/50 shadow-sm' : 'bg-gray-50 border-gray-200 hover:bg-gray-100'}`}
                    >
                      <span className={`text-sm font-medium flex-1 ${isActive ? 'text-gray-900' : 'text-gray-600'}`}>{opt.label}</span>
                      {isActive && (
                        <button
                          type="button"
                          onClick={(e) => handleGoalPrimary(e, opt.type)}
                          title="Set as primary goal"
                          className="ml-2 p-1 hover:scale-125 transition-transform"
                        >
                          <span className={`text-xl ${isPrimary ? 'text-amber-500' : 'text-gray-300'}`}>★</span>
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </SectionCard>

            <SectionCard title="Biomarkers & Lab Results" icon={Heart}>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { key: 'vitamin_d', label: 'Vitamin D', unit: 'ng/mL' },
                  { key: 'hba1c', label: 'HbA1c', unit: '%' },
                  { key: 'tsh', label: 'TSH', unit: 'mIU/L' },
                  { key: 'b12', label: 'Vit B12', unit: 'pg/mL' },
                  { key: 'hdl', label: 'HDL', unit: 'mg/dL' },
                  { key: 'ldl', label: 'LDL', unit: 'mg/dL' },
                  { key: 'triglycerides', label: 'Triglycerides', unit: 'mg/dL' },
                  { key: 'ferritin', label: 'Ferritin', unit: 'ng/mL' },
                  { key: 'hemoglobin', label: 'Hemoglobin', unit: 'g/dL' },
                  { key: 'crp', label: 'CRP', unit: 'mg/L' },
                ].map(meta => (
                  <InputField key={meta.key} label={meta.label} name={meta.key} type="number" unit={meta.unit} value={biomarkers[meta.key]} onChange={handleChange(setBiomarkers)} />
                ))}
              </div>
            </SectionCard>
            </div>

            {/* Sticky Save Button */}
            <div className="sticky bottom-6 flex justify-end mt-12 bg-white border border-gray-200 rounded-lg p-4 shadow-lg">
              <button
                type="submit"
                disabled={saving}
                className="flex items-center gap-2 px-6 py-2 bg-[#237afc] text-white rounded-lg font-semibold hover:bg-[#1a5fc7] transition-all outline-none focus:ring-2 focus:ring-[#237afc]/50 disabled:opacity-50"
              >
                {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
                {saving ? 'Saving...' : 'Save Profile'}
              </button>
            </div>

          </form>
      </div>
      </div>
    </ProtectedRoute>
  );
}
