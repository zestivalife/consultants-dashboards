# Diet Plan Flow - Complete Fix Documentation

## Overview
Fixed comprehensive validation errors and API mismatches in the pre-assessment flow. The flow now properly handles data validation, error recovery, and state persistence across all steps.

## Flow Architecture

```
Login 
  ↓
Take Diet Plan 
  ↓
[FLOW STARTS]
  ├─ Pre-Assessment Notes (ReadOnly)
  ├─ Pre-Assessment (Profile + Diet Plan Creation)
  │   ├─ Save profile data → profileAPI.submitOnboarding()
  │   └─ Create diet plan → dietPlanAPI.createDietPlan()
  ├─ File Upload (Health Reports - Optional)
  │   └─ Upload files → dietPlanAPI.uploadFiles()
  ├─ Health Questionnaire (External Google Form)
  │   └─ User confirms completion
  ├─ Stress Test Intro
  ├─ PSS-10 Form (Assessment - Secure)
  │   └─ Calculate score, store in backend only
  ├─ Consultation Booking (24hr+ future, 15-min slots)
  ├─ Payment
  └─ Success Screen
```

## Key Fixes Applied

### 1. **Schema Mismatch Resolution**

#### Problem
Frontend was sending complex `intakeForm` object to `/nutrition/diet-plan`, but backend expected simple fields.

#### Solution
- **PreAssessment.jsx**: Now makes two sequential API calls:
  1. `profileAPI.submitOnboarding()` - Saves health profile to profile-service
  2. `dietPlanAPI.createDietPlan()` - Creates diet plan with basic info

```javascript
// NEW FLOW in PreAssessment.jsx
const profileData = {
  profile: {
    age: parseInt(formData.age),
    sex: formData.gender,
    height: parseFloat(formData.height),
    weight: parseFloat(formData.currentWeight),
  },
  nutrition: { /* ... */ },
  lifestyle: { /* ... */ }
};
await profileAPI.submitOnboarding(profileData); // Non-blocking

const dietPlanData = {
  name: formData.title,
  description: "...",
  calorie_target: 2000,
  // ... other fields
};
const result = await dietPlanAPI.createDietPlan(dietPlanData);
```

### 2. **File Upload API Improvements**

#### Problem
- No file validation before upload
- FormData structure unclear
- Response handling inconsistent
- dietPlanId not properly associated

#### Solution
- **lib/api.js - nutritionAPI.uploadFiles()**:
  - Validates File objects
  - Properly appends to FormData
  - Consistent error messages
  - Validates at least one file provided

```javascript
uploadFiles(files) {
  const formData = new FormData();
  if (!files || files.length === 0) {
    throw new Error('At least one file must be provided');
  }
  
  files.forEach((file) => {
    if (!(file instanceof File)) {
      throw new Error('Invalid file object provided');
    }
    formData.append('file', file);
  });
  
  return apiRequest('/nutrition/upload-report', {
    method: 'POST',
    body: formData,
  });
}
```

- **utils/api.js - dietPlanAPI.uploadFiles()**:
  - Wraps nutritionAPI.uploadFiles()
  - Handles response format
  - Maintains dietPlanId reference for flow
  - Better error categorization

```javascript
async uploadFiles(dietPlanId, files) {
  try {
    if (!files || !Array.isArray(files) || files.length === 0) {
      throw new Error('No files provided for upload');
    }
    
    const response = await nutritionAPI.uploadFiles(files);
    return {
      ...response,
      dietPlanId: dietPlanId,
      files: response.files || [...]
    };
  } catch (error) {
    console.error('File upload error:', error);
    throw error;
  }
}
```

### 3. **File Upload Component Enhancements**

#### FileUploadWithPreview.jsx
```javascript
const handleUpload = async () => {
  if (files.length === 0) {
    setErrors({ general: 'Please select at least one file' });
    return;
  }

  try {
    // Validate File objects
    const fileArray = files.map(f => f.file);
    if (fileArray.some(f => !(f instanceof File))) {
      throw new Error('Invalid file format detected');
    }

    const result = await dietPlanAPI.uploadFiles(dietPlanId, fileArray);
    const planId = result?.dietPlanId || result?.id || dietPlanId;
    
    onComplete({
      dietPlanId: planId || dietPlanId,
      uploadedFiles: result?.files || [],
      message: 'Files uploaded successfully'
    });
  } catch (error) {
    // Categorized error handling
    let errorMessage = 'Upload failed';
    if (error.message?.includes('Invalid file')) {
      errorMessage = error.message;
    } else if (!navigator.onLine) {
      errorMessage = 'Network error. Check internet connection.';
    } else if (error.status === 413) {
      errorMessage = 'Files too large.';
    } else if (error.status === 401) {
      errorMessage = 'Session expired. Please refresh.';
    }
    
    setErrors({ general: errorMessage });
  }
};
```

### 4. **Health Questionnaire - External Form Handling**

#### HealthQuestionnaire.jsx
- External Google Form linked properly
- Optional notes field for user context
- Confirmation checkbox (user must confirm they completed form)
- Non-blocking API call for tracking
- Graceful degradation if API fails

```javascript
const handleFormSubmitted = async () => {
  if (!formSubmitted) {
    setError('Please confirm completion');
    return;
  }

  try {
    // Non-critical API call
    if (dietPlanId) {
      try {
        await apiRequest(`/nutrition/diet-plans/${dietPlanId}/questionnaire`, {
          method: 'POST',
          body: {
            completed: true,
            completedAt: new Date().toISOString(),
            responseNotes: responseNotes || '',
            source: 'google-form',
            skipped: false
          }
        });
      } catch (apiErr) {
        // Don't block if API fails
        console.warn('Could not save questionnaire status:', apiErr);
        if (apiErr.status === 401 || apiErr.status === 403) {
          throw apiErr; // Re-throw auth errors
        }
      }
    }
    
    // Always continue
    onComplete({
      healthQuestionnaireCompleted: true,
      questionnaireNotes: responseNotes,
      completedAt: new Date().toISOString()
    });
  } catch (err) {
    // Handle auth errors only
    if (err.status === 401 || err.status === 403) {
      setError('Session expired. Please refresh.');
      throw err;
    }
    // Otherwise continue anyway
    onComplete({ /* ... */ });
  }
};
```

### 5. **PSS-10 Assessment - Secure Score Handling**

#### PSS10Form.jsx - Key Change
**IMPORTANT**: Stress score is calculated but NEVER displayed to the user.

```javascript
const handleSubmit = async (e) => {
  // ... validation ...

  try {
    // Calculate score (for reference only)
    const reverseItems = [3, 4, 6, 7];
    let calculatedStressScore = 0;
    responses.forEach((val, idx) => {
      if (reverseItems.includes(idx)) {
        calculatedStressScore += (4 - val);
      } else {
        calculatedStressScore += val;
      }
    });

    // Log for backend only (non-critical)
    try {
      const { teamMemberAPI } = await import('../lib/api');
      await teamMemberAPI.logMetric({
        type: 'STRESS_LEVEL',
        value: calculatedStressScore,
        unit: '/40',
        notes: 'PSS-10 Assessment - For dietitian review only',
        timestamp: new Date().toISOString()
      });
    } catch (metricError) {
      console.warn('Could not log stress metric:', metricError);
      // Continue anyway
    }

    // Complete WITHOUT exposing score
    onComplete({
      pssResponses: responses,
      responseCount: responses.length,
      submittedAt: new Date().toISOString(),
      // NOTE: stressScore is NOT included
    });
  } catch (error) {
    // Handle error
  }
};
```

**Why this approach:**
- User sees responses stored, but no score displayed
- Dietitian reviews actual responses in admin panel
- Prevents premature conclusions about stress level
- Better UX - focuses on action (booking) not labeling

### 6. **Error Handling Improvements**

#### API Client (lib/api.js)
```javascript
export async function apiRequest(path, opts = {}) {
  try {
    const res = await fetch(url, { ...opts, headers });
  } catch (networkErr) {
    if (networkErr.name === 'AbortError') throw networkErr;
    const err = new Error('Network error: check if server is running.');
    err.status = 0;
    err.cause = networkErr;
    throw err;
  }

  if (!res.ok) {
    console.error(`[API ERROR] ${res.status}`, json);
    if (res.status === 401) {
      clearTokens(); // Clear invalid token
    }

    const err = new Error(json?.message || `Request failed (${res.status})`);
    err.status = res.status;
    err.data = json;
    throw err;
  }

  // Return data field from standard response wrapper
  if (json && typeof json === 'object' && 'success' in json) {
    return json.data;
  }
  return json;
}
```

#### Component Error Boundaries
Each component now has:
- **Pre-validation** before API calls
- **Categorized errors** (network, auth, validation, server)
- **User-friendly messages** (not raw error codes)
- **Non-blocking fallbacks** (continue if non-critical API fails)
- **Retry logic** where applicable

### 7. **State Persistence in DietPlanFlow**

#### DietPlanFlow.jsx
```javascript
const [flowData, setFlowData] = useState({
  dietPlanId: null,           // Key ID for all subsequent steps
  preAssessmentNotes: null,
  preAssessment: null,        // Full assessment data
  uploadedFiles: [],
  healthQuestionnaireCompleted: false,
  stressTestAcknowledged: false,
  pssResponses: null,         // Responses, not score
  appointment: null,
  payment: null
});

const handleStepComplete = (stepData) => {
  setFlowData(prev => ({ ...prev, ...stepData }));
  // Move to next step
};
```

**State Flow:**
1. Pre-Assessment Notes → ✓ (no data needed)
2. Pre-Assessment → `dietPlanId`, `preAssessment`
3. File Upload → `uploadedFiles` (dietPlanId preserved)
4. Health Questionnaire → `healthQuestionnaireCompleted`
5. Stress Test Intro → `stressTestAcknowledged`
6. PSS-10 Form → `pssResponses`
7. Booking → `appointment`
8. Payment → `payment`
9. Complete → Call `onComplete(flowData)`

## Testing Checklist

### Pre-Assessment Form
- [ ] Fill out all required fields
- [ ] Verify age validation (16-120)
- [ ] Verify weight/height are positive numbers
- [ ] Submit form
- [ ] Check that dietPlanId is returned
- [ ] Go back and edit - data persists

### File Upload
- [ ] Skip upload - continues to next step
- [ ] Upload valid PDF - shows preview
- [ ] Upload valid image - shows thumbnail
- [ ] Upload too large file - shows error
- [ ] Upload invalid format - shows error
- [ ] Upload 5+ files - shows max error
- [ ] Remove file - frees slot
- [ ] Submit files - uploads and continues

### Health Questionnaire
- [ ] External link opens in new tab
- [ ] Optional notes field accepts input
- [ ] Checkbox required before continue
- [ ] Skip option available
- [ ] Continue moves to next step

### PSS-10 Form
- [ ] All 10 questions displayed
- [ ] Radio buttons work correctly
- [ ] Progress bar updates
- [ ] Can go back and edit responses
- [ ] Submit disabled until all answered
- [ ] After submit: NO SCORE displayed
- [ ] Metric logged in backend (admin only)

### Booking
- [ ] Select provider/dietician
- [ ] Select date (must be 24+ hours future)
- [ ] Select time (15-min slots)
- [ ] Validation errors show clearly
- [ ] Submit creates appointment

### Payment & Complete
- [ ] Payment form works
- [ ] Success screen shows appointment time
- [ ] "View Appointments" button works
- [ ] "Go to Dashboard" button works

### Error Scenarios
- [ ] Network offline - shows network error
- [ ] API returns 401 - shows session expired
- [ ] API returns 500 - shows server error
- [ ] Partial failures (e.g., profile save fails) - flow continues
- [ ] Go back from error and retry - works

## Database Considerations

### Data Stored
1. **profile-service**: User profile with health metrics
2. **nutrition-service**: Diet plan, health reports
3. **assessment-service**: PSS-10 responses (not score)
4. **consultation-service**: Appointment booking

### Backend Endpoints Expected

```
POST /profile                           → Create/update profile
POST /nutrition/diet-plan              → Create diet plan
POST /nutrition/upload-report          → Upload health files
POST /nutrition/diet-plans/{id}/questionnaire → Mark questionnaire done
POST /assessments/pss10                → Store PSS-10 responses
POST /consultations/appointments       → Book appointment
GET  /consultations/providers          → List dieticians
GET  /consultations/providers/{id}/available-slots → Get free slots
```

## Important Notes

### ✅ What's Fixed
- ✓ Schema mismatches between frontend and backend
- ✓ File upload validation and FormData handling
- ✓ Error categorization and user-friendly messages
- ✓ State persistence across flow steps
- ✓ Non-blocking API calls for optional steps
- ✓ Secure PSS-10 score handling (backend only)
- ✓ Better logging for debugging

### ⚠️ Still Needs Backend Implementation
These endpoints should be implemented in backend if not already:
- POST `/nutrition/diet-plans/{id}/questionnaire` - Track questionnaire completion
- GET `/consultations/providers` - List dieticians
- GET `/consultations/providers/{id}/available-slots` - Get available booking slots
- POST `/consultations/appointments` - Create appointment

### 📝 Usage Notes
1. **Profile API is non-blocking**: If profile save fails, diet plan still creates
2. **File upload is optional**: Users can skip and continue
3. **Questionnaire is external**: We just track that they confirmed completion
4. **Stress score is hidden**: Only stored in backend for dietitian review
5. **All data flows through to success**: Even if intermediate steps have issues

## Deployment Checklist
- [ ] Update backend schemas if needed
- [ ] Deploy backend services
- [ ] Test full flow in staging
- [ ] Monitor error logs in production
- [ ] Set up dietician review process for PSS-10
- [ ] Verify appointment confirmation emails
- [ ] Test payment gateway integration
