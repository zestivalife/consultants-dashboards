import React, { useState, useEffect } from 'react';
import { User, Target, Activity, AlertCircle, Loader } from 'lucide-react';
import { dietPlanAPI } from '../utils/api';
import { profileAPI } from '../lib/api';

const PreAssessment = ({ onComplete, initialData, isLoading, setIsLoading }) => {
  const [formData, setFormData] = useState({
    title: '',
    goals: '',
    currentWeight: '',
    targetWeight: '',
    height: '',
    hipSize: '',
    waistSize: '',
    muscleMassPercent: '',
    age: '',
    gender: 'OTHER',
    activityLevel: '',
    dietaryRestrictions: '',
    medicalConditions: '',
    preferredMealTypes: [],
    timeframe: '',
    serviceId: 'DIET-PLAN-SERVICE-ID-12345678', // Matches length requirement (min: 20, max: 30)
    ...initialData
  });

  const [errors, setErrors] = useState({});

  const activityLevels = [
    { value: 'sedentary', label: 'Sedentary (little/no exercise)' },
    { value: 'light', label: 'Light (light exercise 1-3 days/week)' },
    { value: 'moderate', label: 'Moderate (moderate exercise 3-5 days/week)' },
    { value: 'active', label: 'Active (hard exercise 6-7 days/week)' },
    { value: 'very_active', label: 'Very Active (very hard exercise, physical job)' }
  ];

  const mealTypes = [
    { value: 'vegetarian', label: 'Vegetarian' },
    { value: 'vegan', label: 'Vegan' },
    { value: 'keto', label: 'Ketogenic' },
    { value: 'paleo', label: 'Paleo' },
    { value: 'mediterranean', label: 'Mediterranean' },
    { value: 'low_carb', label: 'Low Carb' },
    { value: 'balanced', label: 'Balanced' }
  ];

  const timeframes = [
    { value: '1_month', label: '1 Month' },
    { value: '3_months', label: '3 Months' },
    { value: '6_months', label: '6 Months' },
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handleMealTypeToggle = (mealType) => {
    setFormData(prev => ({
      ...prev,
      preferredMealTypes: prev.preferredMealTypes.includes(mealType)
        ? prev.preferredMealTypes.filter(type => type !== mealType)
        : [...prev.preferredMealTypes, mealType]
    }));
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.title.trim()) newErrors.title = 'Diet plan title is required';
    if (!formData.goals.trim()) newErrors.goals = 'Goals are required';
    if (!formData.currentWeight) newErrors.currentWeight = 'Current weight is required';
    if (!formData.height) newErrors.height = 'Height is required';
    if (!formData.age) newErrors.age = 'Age is required';
    if (!formData.activityLevel) newErrors.activityLevel = 'Activity level is required';
    if (!formData.timeframe) newErrors.timeframe = 'Timeframe is required';

    // Validate numeric fields (only if provided for optional ones)
    if (formData.currentWeight && (isNaN(formData.currentWeight) || Number(formData.currentWeight) <= 0)) {
      newErrors.currentWeight = 'Please enter a valid weight';
    }
    if (formData.targetWeight && (isNaN(formData.targetWeight) || Number(formData.targetWeight) <= 0)) {
      newErrors.targetWeight = 'Please enter a valid target weight';
    }
    if (formData.height && (isNaN(formData.height) || Number(formData.height) <= 0)) {
      newErrors.height = 'Please enter a valid height';
    }
    if (formData.age && (isNaN(formData.age) || Number(formData.age) < 16 || Number(formData.age) > 120)) {
      newErrors.age = 'Please enter a valid age (16-120)';
    }
    // Optional hip & waist numeric validation (only if user entered a value)
    if (formData.hipSize && (isNaN(formData.hipSize) || Number(formData.hipSize) <= 0)) {
      newErrors.hipSize = 'Please enter a valid hip size';
    }
    if (formData.waistSize && (isNaN(formData.waistSize) || Number(formData.waistSize) <= 0)) {
      newErrors.waistSize = 'Please enter a valid waist size';
    }
    // Optional muscle mass validation (0-100%)
    if (formData.muscleMassPercent && (isNaN(formData.muscleMassPercent) || Number(formData.muscleMassPercent) < 0 || Number(formData.muscleMassPercent) > 100)) {
      newErrors.muscleMassPercent = 'Please enter a valid muscle mass percentage (0-100)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsLoading(true);
    setErrors({});
    
    try {
      // Step 1: Save user profile with health information
      console.log('Step 1: Creating/updating user profile...');
      const profileData = {
        profile: {
          age: parseInt(formData.age),
          sex: formData.gender,
          height: parseFloat(formData.height),
          weight: parseFloat(formData.currentWeight),
        },
        ...(formData.targetWeight && {
          goals: [
            {
              goal_type: `Weight loss to ${formData.targetWeight}kg`,
              is_primary: true
            }
          ]
        }),
        nutrition: {
          target_calories: 2000, // Default - can be calculated later
          protein_intake: 'moderate',
          food_source: formData.preferredMealTypes.join(',') || 'balanced'
        },
        lifestyle: {
          activity_level: formData.activityLevel,
          food_type: formData.preferredMealTypes.join(',') || 'balanced'
        }
      };

      try {
        await profileAPI.submitOnboarding(profileData);
        console.log('Profile saved successfully');
      } catch (profileError) {
        // Non-critical error - log but continue
        console.warn('Could not save profile data:', profileError);
      }

      // Step 2: Create diet plan
      console.log('Step 2: Creating diet plan...');
      const dietPlanData = {
        name: formData.title,
        description: `${formData.goals} | Activity: ${formData.activityLevel} | Dietary: ${formData.dietaryRestrictions || 'None'}`,
        calorie_target: 2000, // To be determined by dietitian
        protein_target: 150,
        fat_target: 65,
        carb_target: 250,
        meals: []
      };

      const dietPlanResult = await dietPlanAPI.createDietPlan(dietPlanData);
      const planId = dietPlanResult?.id || dietPlanResult?.data?.id;

      if (!planId) {
        throw new Error('Failed to create diet plan: No ID returned');
      }

      console.log('Diet plan created with ID:', planId);

      // Step 3: Complete the step with the diet plan ID
      onComplete({
        dietPlanId: planId,
        preAssessment: {
          ...formData,
          profileSaved: true,
          assessmentData: {
            age: parseInt(formData.age),
            gender: formData.gender,
            height: parseFloat(formData.height),
            weight: parseFloat(formData.currentWeight),
            targetWeight: formData.targetWeight ? parseFloat(formData.targetWeight) : null,
            activityLevel: formData.activityLevel,
            dietaryRestrictions: formData.dietaryRestrictions ? formData.dietaryRestrictions.split(',').map(item => item.trim()) : [],
            healthConditions: formData.medicalConditions ? formData.medicalConditions.split(',').map(item => item.trim()) : [],
            goals: [formData.goals],
            timeframe: formData.timeframe,
            preferredMealTypes: formData.preferredMealTypes,
            hipSize: formData.hipSize ? parseFloat(formData.hipSize) : null,
            waistSize: formData.waistSize ? parseFloat(formData.waistSize) : null,
            muscleMassPercent: formData.muscleMassPercent ? parseFloat(formData.muscleMassPercent) : null
          }
        }
      });
    } catch (error) {
      console.error('Error in pre-assessment flow:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Failed to create diet plan. Please try again.';
      setErrors({ submit: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Information */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <User className="h-5 w-5 mr-2 text-blue-600" />
          Basic Information
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Diet Plan Title *
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.title ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="e.g., Weight Loss Plan 2024"
            />
            {errors.title && <p className="text-red-500 text-xs mt-1">{errors.title}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Gender *
            </label>
            <select
              value={formData.gender}
              onChange={(e) => handleInputChange('gender', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="MALE">Male</option>
              <option value="FEMALE">Female</option>
              <option value="OTHER">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Age *
            </label>
            <input
              type="number"
              value={formData.age}
              onChange={(e) => handleInputChange('age', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.age ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="25"
              min="16"
              max="120"
            />
            {errors.age && <p className="text-red-500 text-xs mt-1">{errors.age}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Current Weight (kg) *
            </label>
            <input
              type="number"
              value={formData.currentWeight}
              onChange={(e) => handleInputChange('currentWeight', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.currentWeight ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="70"
              step="0.1"
            />
            {errors.currentWeight && <p className="text-red-500 text-xs mt-1">{errors.currentWeight}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Target Weight (kg)
            </label>
            <input
              type="number"
              value={formData.targetWeight}
              onChange={(e) => handleInputChange('targetWeight', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.targetWeight ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="65"
              step="0.1"
            />
            {errors.targetWeight && <p className="text-red-500 text-xs mt-1">{errors.targetWeight}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Height (cm) *
            </label>
            <input
              type="number"
              value={formData.height}
              onChange={(e) => handleInputChange('height', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.height ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="170"
            />
            {errors.height && <p className="text-red-500 text-xs mt-1">{errors.height}</p>}
          </div>

          {/* New optional fields: Hip Size & Waist Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Hip Size (cm)
            </label>
            <input
              type="number"
              value={formData.hipSize}
              onChange={(e) => handleInputChange('hipSize', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.hipSize ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="90"
              step="0.1"
            />
            {errors.hipSize && <p className="text-red-500 text-xs mt-1">{errors.hipSize}</p>}
            <p className="text-xs text-gray-500 mt-1">Optional — saved only if provided</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Waist Size (cm)
            </label>
            <input
              type="number"
              value={formData.waistSize}
              onChange={(e) => handleInputChange('waistSize', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.waistSize ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="75"
              step="0.1"
            />
            {errors.waistSize && <p className="text-red-500 text-xs mt-1">{errors.waistSize}</p>}
            <p className="text-xs text-gray-500 mt-1">Optional — saved only if provided</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Muscle Mass (%)
            </label>
            <input
              type="number"
              value={formData.muscleMassPercent}
              onChange={(e) => handleInputChange('muscleMassPercent', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.muscleMassPercent ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="35"
              step="0.1"
              min="0"
              max="100"
            />
            {errors.muscleMassPercent && <p className="text-red-500 text-xs mt-1">{errors.muscleMassPercent}</p>}
            <p className="text-xs text-gray-500 mt-1">Optional — baseline muscle mass percentage</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Activity Level *
            </label>
            <select
              value={formData.activityLevel}
              onChange={(e) => handleInputChange('activityLevel', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.activityLevel ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="">Select activity level</option>
              {activityLevels.map(level => (
                <option key={level.value} value={level.value}>
                  {level.label}
                </option>
              ))}
            </select>
            {errors.activityLevel && <p className="text-red-500 text-xs mt-1">{errors.activityLevel}</p>}
          </div>
        </div>
      </div>

      {/* Goals and Preferences */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Target className="h-5 w-5 mr-2 text-green-600" />
          Goals & Preferences
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Goals & Objectives *
            </label>
            <textarea
              value={formData.goals}
              onChange={(e) => handleInputChange('goals', e.target.value)}
              rows={3}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.goals ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Describe your health and fitness goals..."
            />
            {errors.goals && <p className="text-red-500 text-xs mt-1">{errors.goals}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Preferred Meal Types
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {mealTypes.map(type => (
                <label key={type.value} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.preferredMealTypes.includes(type.value)}
                    onChange={() => handleMealTypeToggle(type.value)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">{type.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Timeframe *
            </label>
            <select
              value={formData.timeframe}
              onChange={(e) => handleInputChange('timeframe', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.timeframe ? 'border-red-500' : 'border-gray-300'
              }`}
            >
              <option value="">Select timeframe</option>
              {timeframes.map(time => (
                <option key={time.value} value={time.value}>
                  {time.label}
                </option>
              ))}
            </select>
            {errors.timeframe && <p className="text-red-500 text-xs mt-1">{errors.timeframe}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dietary Restrictions
            </label>
            <textarea
              value={formData.dietaryRestrictions}
              onChange={(e) => handleInputChange('dietaryRestrictions', e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Any allergies, intolerances, or dietary restrictions..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Medical Conditions
            </label>
            <textarea
              value={formData.medicalConditions}
              onChange={(e) => handleInputChange('medicalConditions', e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Any medical conditions that might affect your diet..."
            />
          </div>
        </div>
      </div>

      {/* Error Message */}
      {errors.submit && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
          <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
          <p className="text-red-700">{errors.submit}</p>
        </div>
      )}

      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isLoading}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
          Continue to File Upload
        </button>
      </div>
    </form>
  );
};

export default PreAssessment;
