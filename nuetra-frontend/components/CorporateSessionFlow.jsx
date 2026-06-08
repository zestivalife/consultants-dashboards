import React, { useState, useEffect } from 'react';
import { Calendar, Users, MapPin, Clock, AlertCircle, CheckCircle, Loader, X, Plus } from 'lucide-react';
import { corporateAPI } from '../utils/api';

const CorporateSessionFlow = ({ isOpen, onClose, onComplete, userRole }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [sessionData, setSessionData] = useState({
    title: '',
    description: '',
    sessionType: 'WELLNESS_WORKSHOP',
    date: '',
    time: '',
    duration: 60,
    location: '',
    maxParticipants: 50,
    targetAudience: 'ALL_EMPLOYEES',
    facilitatorId: null,
    materials: []
  });

  const sessionTypes = [
    { value: 'WELLNESS_WORKSHOP', label: 'Wellness Workshop', description: 'Interactive wellness education session' },
    { value: 'NUTRITION_SEMINAR', label: 'Nutrition Seminar', description: 'Focused nutrition education and guidance' },
    { value: 'FITNESS_CLASS', label: 'Fitness Class', description: 'Group fitness and exercise session' },
    { value: 'STRESS_MANAGEMENT', label: 'Stress Management', description: 'Stress reduction and mindfulness training' },
    { value: 'HEALTH_SCREENING', label: 'Health Screening', description: 'Basic health assessments and checkups' }
  ];

  const targetAudiences = [
    { value: 'ALL_EMPLOYEES', label: 'All Employees' },
    { value: 'MANAGEMENT', label: 'Management Team' },
    { value: 'SPECIFIC_DEPARTMENT', label: 'Specific Department' },
    { value: 'HIGH_RISK_EMPLOYEES', label: 'High-Risk Employees' }
  ];

  const steps = [
    { id: 1, title: 'Session Details', description: 'Basic session information' },
    { id: 2, title: 'Schedule & Location', description: 'When and where' },
    { id: 3, title: 'Participants & Resources', description: 'Who and what' },
    { id: 4, title: 'Review & Create', description: 'Confirm details' }
  ];

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setCurrentStep(1);
      setErrors({});
      setSessionData({
        title: '',
        description: '',
        sessionType: 'WELLNESS_WORKSHOP',
        date: '',
        time: '',
        duration: 60,
        location: '',
        maxParticipants: 50,
        targetAudience: 'ALL_EMPLOYEES',
        facilitatorId: null,
        materials: []
      });
    }
  }, [isOpen]);

  const validateStep = (step) => {
    const newErrors = {};

    switch (step) {
      case 1:
        if (!sessionData.title.trim()) newErrors.title = 'Session title is required';
        if (!sessionData.description.trim()) newErrors.description = 'Description is required';
        if (!sessionData.sessionType) newErrors.sessionType = 'Session type is required';
        break;
      case 2:
        if (!sessionData.date) newErrors.date = 'Date is required';
        if (!sessionData.time) newErrors.time = 'Time is required';
        if (!sessionData.location.trim()) newErrors.location = 'Location is required';
        // Validate date is in the future
        const sessionDateTime = new Date(`${sessionData.date}T${sessionData.time}`);
        if (sessionDateTime <= new Date()) {
          newErrors.date = 'Session must be scheduled for a future date and time';
        }
        break;
      case 3:
        if (sessionData.maxParticipants < 1) newErrors.maxParticipants = 'Must allow at least 1 participant';
        if (sessionData.maxParticipants > 500) newErrors.maxParticipants = 'Maximum 500 participants allowed';
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, steps.length));
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    setIsLoading(true);
    setErrors({});

    try {
      const sessionDateTime = new Date(`${sessionData.date}T${sessionData.time}`);
      const endDateTime = new Date(sessionDateTime.getTime() + sessionData.duration * 60000);

      const sessionPayload = {
        ...sessionData,
        startAt: sessionDateTime.toISOString(),
        endAt: endDateTime.toISOString(),
        createdBy: userRole // Will be replaced with actual user ID on backend
      };

      const result = await corporateAPI.createSession(sessionPayload);
      
      onComplete({
        session: result.data || result,
        message: 'Corporate wellness session created successfully'
      });
      
      onClose();
    } catch (error) {
      console.error('Error creating session:', error);
      setErrors({ submit: error.message || 'Failed to create session. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Session Title *
              </label>
              <input
                type="text"
                value={sessionData.title}
                onChange={(e) => setSessionData(prev => ({ ...prev, title: e.target.value }))}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  errors.title ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="e.g., Monthly Wellness Workshop"
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600 flex items-center">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  {errors.title}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Session Type *
              </label>
              <div className="grid grid-cols-1 gap-3">
                {sessionTypes.map((type) => (
                  <label key={type.value} className="flex items-start space-x-3 cursor-pointer">
                    <input
                      type="radio"
                      name="sessionType"
                      value={type.value}
                      checked={sessionData.sessionType === type.value}
                      onChange={(e) => setSessionData(prev => ({ ...prev, sessionType: e.target.value }))}
                      className="mt-1"
                    />
                    <div>
                      <div className="font-medium text-gray-900">{type.label}</div>
                      <div className="text-sm text-gray-500">{type.description}</div>
                    </div>
                  </label>
                ))}
              </div>
              {errors.sessionType && (
                <p className="mt-1 text-sm text-red-600 flex items-center">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  {errors.sessionType}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description *
              </label>
              <textarea
                value={sessionData.description}
                onChange={(e) => setSessionData(prev => ({ ...prev, description: e.target.value }))}
                rows={4}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  errors.description ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Describe the session objectives, activities, and expected outcomes..."
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600 flex items-center">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  {errors.description}
                </p>
              )}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Date *
                </label>
                <input
                  type="date"
                  value={sessionData.date}
                  onChange={(e) => setSessionData(prev => ({ ...prev, date: e.target.value }))}
                  min={new Date().toISOString().split('T')[0]}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.date ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.date && (
                  <p className="mt-1 text-sm text-red-600 flex items-center">
                    <AlertCircle className="w-4 h-4 mr-1" />
                    {errors.date}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Time *
                </label>
                <input
                  type="time"
                  value={sessionData.time}
                  onChange={(e) => setSessionData(prev => ({ ...prev, time: e.target.value }))}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.time ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.time && (
                  <p className="mt-1 text-sm text-red-600 flex items-center">
                    <AlertCircle className="w-4 h-4 mr-1" />
                    {errors.time}
                  </p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Duration (minutes)
              </label>
              <select
                value={sessionData.duration}
                onChange={(e) => setSessionData(prev => ({ ...prev, duration: parseInt(e.target.value) }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={30}>30 minutes</option>
                <option value={45}>45 minutes</option>
                <option value={60}>1 hour</option>
                <option value={90}>1.5 hours</option>
                <option value={120}>2 hours</option>
                <option value={180}>3 hours</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Location *
              </label>
              <input
                type="text"
                value={sessionData.location}
                onChange={(e) => setSessionData(prev => ({ ...prev, location: e.target.value }))}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  errors.location ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="e.g., Conference Room A, Main Office Building"
              />
              {errors.location && (
                <p className="mt-1 text-sm text-red-600 flex items-center">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  {errors.location}
                </p>
              )}
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maximum Participants
              </label>
              <input
                type="number"
                value={sessionData.maxParticipants}
                onChange={(e) => setSessionData(prev => ({ ...prev, maxParticipants: parseInt(e.target.value) || 0 }))}
                min="1"
                max="500"
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  errors.maxParticipants ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.maxParticipants && (
                <p className="mt-1 text-sm text-red-600 flex items-center">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  {errors.maxParticipants}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Audience
              </label>
              <select
                value={sessionData.targetAudience}
                onChange={(e) => setSessionData(prev => ({ ...prev, targetAudience: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {targetAudiences.map((audience) => (
                  <option key={audience.value} value={audience.value}>
                    {audience.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Notes
              </label>
              <textarea
                value={sessionData.materials}
                onChange={(e) => setSessionData(prev => ({ ...prev, materials: e.target.value }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Any special requirements, materials needed, or additional information..."
              />
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3">Session Summary</h4>
              <div className="space-y-2 text-sm">
                <div><span className="font-medium">Title:</span> {sessionData.title}</div>
                <div><span className="font-medium">Type:</span> {sessionTypes.find(t => t.value === sessionData.sessionType)?.label}</div>
                <div><span className="font-medium">Date & Time:</span> {sessionData.date} at {sessionData.time}</div>
                <div><span className="font-medium">Duration:</span> {sessionData.duration} minutes</div>
                <div><span className="font-medium">Location:</span> {sessionData.location}</div>
                <div><span className="font-medium">Max Participants:</span> {sessionData.maxParticipants}</div>
                <div><span className="font-medium">Target Audience:</span> {targetAudiences.find(a => a.value === sessionData.targetAudience)?.label}</div>
              </div>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-start">
                <CheckCircle className="w-5 h-5 text-blue-600 mt-0.5 mr-2" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium">Ready to create session</p>
                  <p>Once created, invitations will be sent to eligible employees and the session will appear in the corporate wellness calendar.</p>
                </div>
              </div>
            </div>

            {errors.submit && (
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="flex items-start">
                  <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-2" />
                  <p className="text-sm text-red-800">{errors.submit}</p>
                </div>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Create Corporate Wellness Session</h2>
            <p className="text-sm text-gray-500 mt-1">Step {currentStep} of {steps.length}: {steps[currentStep - 1]?.title}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            {steps.map((step, index) => (
              <React.Fragment key={step.id}>
                <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                  currentStep > step.id 
                    ? 'bg-green-500 text-white' 
                    : currentStep === step.id 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {currentStep > step.id ? <CheckCircle className="w-4 h-4" /> : step.id}
                </div>
                {index < steps.length - 1 && (
                  <div className={`flex-1 h-1 rounded ${
                    currentStep > step.id ? 'bg-green-500' : 'bg-gray-200'
                  }`} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {renderStepContent()}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 1}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>

          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            
            {currentStep < steps.length ? (
              <button
                onClick={handleNext}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={isLoading}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
              >
                {isLoading ? (
                  <>
                    <Loader className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Session'
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CorporateSessionFlow;