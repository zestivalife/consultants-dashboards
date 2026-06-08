import React, { useState } from 'react';
import { X, ArrowLeft, ArrowRight, CheckCircle } from 'lucide-react';
import PreAssessmentNotes from './PreAssessmentNotes';
import PreAssessment from './PreAssessment';
import FileUploadWithPreview from './FileUploadWithPreview';
import HealthQuestionnaire from './HealthQuestionnaire';
import StressTestIntro from './StressTestIntro';
import PSS10Form from './PSS10Form';
import BookingModal from './BookingModal';
import PaymentSummary from './PaymentSummary';

const FLOW_STEPS = {
  PRE_ASSESSMENT_NOTES: 'pre_assessment_notes',
  PRE_ASSESSMENT: 'pre_assessment',
  FILE_UPLOAD: 'file_upload',
  HEALTH_QUESTIONNAIRE: 'health_questionnaire',
  STRESS_TEST_INTRO: 'stress_test_intro',
  PSS10_FORM: 'pss10_form',
  BOOKING: 'booking',
  PAYMENT: 'payment',
  COMPLETE: 'complete'
};

const STEP_TITLES = {
  [FLOW_STEPS.PRE_ASSESSMENT_NOTES]: 'Before You Begin',
  [FLOW_STEPS.PRE_ASSESSMENT]: 'Health Information',
  [FLOW_STEPS.FILE_UPLOAD]: 'Upload Health Reports',
  [FLOW_STEPS.HEALTH_QUESTIONNAIRE]: 'Health Questionnaire',
  [FLOW_STEPS.STRESS_TEST_INTRO]: 'Stress Assessment Intro',
  [FLOW_STEPS.PSS10_FORM]: 'Stress Assessment',
  [FLOW_STEPS.BOOKING]: 'Book Consultation',
  [FLOW_STEPS.PAYMENT]: 'Payment',
  [FLOW_STEPS.COMPLETE]: 'All Set!'
};

const DietPlanFlow = ({ isOpen, onClose, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(FLOW_STEPS.PRE_ASSESSMENT_NOTES);
  const [flowData, setFlowData] = useState({
    dietPlanId: null,
    preAssessmentNotes: null,
    preAssessment: null,
    uploadedFiles: [],
    healthQuestionnaireCompleted: false,
    stressTestAcknowledged: false,
    pssResponses: null,
    appointment: null,
    payment: null
  });
  const [isLoading, setIsLoading] = useState(false);

  const stepOrder = [
    FLOW_STEPS.PRE_ASSESSMENT_NOTES,
    FLOW_STEPS.PRE_ASSESSMENT,
    FLOW_STEPS.FILE_UPLOAD,
    FLOW_STEPS.HEALTH_QUESTIONNAIRE,
    FLOW_STEPS.STRESS_TEST_INTRO,
    FLOW_STEPS.PSS10_FORM,
    FLOW_STEPS.BOOKING,
    FLOW_STEPS.PAYMENT,
    FLOW_STEPS.COMPLETE
  ];

  const currentStepIndex = stepOrder.indexOf(currentStep);
  const canGoBack = currentStepIndex > 0;
  const isLastStep = currentStep === FLOW_STEPS.COMPLETE;

  const handleStepComplete = (stepData) => {
    setFlowData(prev => ({ ...prev, ...stepData }));
    
    if (currentStep === FLOW_STEPS.PAYMENT) {
      setCurrentStep(FLOW_STEPS.COMPLETE);
    } else {
      const nextStepIndex = currentStepIndex + 1;
      if (nextStepIndex < stepOrder.length) {
        setCurrentStep(stepOrder[nextStepIndex]);
      }
    }
  };

  const handleBack = () => {
    if (canGoBack) {
      const prevStepIndex = currentStepIndex - 1;
      setCurrentStep(stepOrder[prevStepIndex]);
    }
  };

  const handleClose = () => {
    if (currentStep === FLOW_STEPS.COMPLETE) {
      onComplete?.(flowData);
    }
    onClose();
  };

  const renderCurrentStep = () => {
    switch (currentStep) {
      case FLOW_STEPS.PRE_ASSESSMENT_NOTES:
        return (
          <PreAssessmentNotes
            onComplete={handleStepComplete}
            initialData={flowData.preAssessmentNotes}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        );
      case FLOW_STEPS.PRE_ASSESSMENT:
        return (
          <PreAssessment
            onComplete={handleStepComplete}
            initialData={flowData.preAssessment}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        );
      case FLOW_STEPS.FILE_UPLOAD:
        return (
          <FileUploadWithPreview
            dietPlanId={flowData.dietPlanId}
            onComplete={handleStepComplete}
            initialFiles={flowData.uploadedFiles}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />  
        );
      case FLOW_STEPS.HEALTH_QUESTIONNAIRE:
        return (
          <HealthQuestionnaire
            dietPlanId={flowData.dietPlanId}
            onComplete={handleStepComplete}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        );
      case FLOW_STEPS.STRESS_TEST_INTRO:
        return (
          <StressTestIntro
            onComplete={handleStepComplete}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        );
      case FLOW_STEPS.PSS10_FORM:
        return (
          <PSS10Form
            dietPlanId={flowData.dietPlanId}
            onComplete={handleStepComplete}
            initialData={flowData.pssResponses}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        );
      case FLOW_STEPS.BOOKING:
        return (
          <BookingModal
            dietPlanId={flowData.dietPlanId}
            onComplete={handleStepComplete}
            initialData={flowData.appointment}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        );
      case FLOW_STEPS.PAYMENT:
        return (
          <PaymentSummary
            dietPlan={flowData.preAssessment}
            appointment={flowData.appointment}
            onComplete={handleStepComplete}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
          />
        );
      case FLOW_STEPS.COMPLETE:
        return (
          <div className="text-center py-8">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              You're All Set!
            </h3>
            <p className="text-gray-600 mb-6 max-w-lg mx-auto">
              Thanks! Your consultation with our dietitian is scheduled for{' '}
              <span className="font-semibold">
                {flowData.appointment?.startAt ? new Date(flowData.appointment.startAt).toLocaleString() : 'your selected time'}
              </span>
              . We've saved your health questionnaire and stress-test responses — your dietitian will review them and discuss the results during your session.
            </p>
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => {
                  onComplete?.(flowData);
                  onClose();
                }}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                View My Appointments
              </button>
              <button
                onClick={handleClose}
                className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            {canGoBack && currentStep !== FLOW_STEPS.COMPLETE && (
              <button
                onClick={handleBack}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                disabled={isLoading}
              >
                <ArrowLeft className="h-5 w-5 text-gray-600" />
              </button>
            )}
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {STEP_TITLES[currentStep]}
              </h2>
              <p className="text-sm text-gray-600">
                Step {currentStepIndex + 1} of {stepOrder.length}
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            disabled={isLoading}
          >
            <X className="h-5 w-5 text-gray-600" />
          </button>
        </div>

        {/* Progress Bar */}
        {currentStep !== FLOW_STEPS.COMPLETE && (
          <div className="px-6 py-4 bg-gray-50">
            <div className="flex items-center space-x-2">
              {stepOrder.slice(0, -1).map((step, index) => (
                <React.Fragment key={step}>
                  <div
                    className={`h-2 flex-1 rounded-full ${
                      index <= currentStepIndex
                        ? 'bg-green-500'
                        : 'bg-gray-200'
                    }`}
                  />
                  {index < stepOrder.length - 2 && (
                    <div className="w-2 h-2 rounded-full bg-gray-300" />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        )}

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {renderCurrentStep()}
        </div>
      </div>
    </div>
  );
};

export default DietPlanFlow;