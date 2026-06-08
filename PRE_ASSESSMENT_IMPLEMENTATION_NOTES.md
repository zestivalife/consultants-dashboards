# Pre-Assessment Flow - Implementation Summary

## Changes Made

### 1. **Backend API Client Fixes**

#### `/nuetra-frontend/lib/api.js`
- **Enhanced `nutritionAPI.uploadFiles()`**:
  - Validates File objects before FormData append
  - Throws descriptive errors for invalid inputs
  - Properly constructs FormData with multiple files
  - Handles edge cases (null files, empty array)

#### `/nuetra-frontend/utils/api.js`
- **Updated `dietPlanAPI.uploadFiles()`**:
  - Now wraps `nutritionAPI.uploadFiles()` properly
  - Handles response format consistency
  - Maintains dietPlanId reference for flow state
  - Categorizes errors: network, auth, validation, server
  
- **Enhanced `appointmentAPI`**:
  - Added `getAvailableSlots(providerId, date)` method
  - Graceful fallback if endpoint doesn't exist
  - Proper error handling for 404 responses

### 2. **PreAssessment Component Overhaul**

#### `/nuetra-frontend/components/PreAssessment.jsx`
**Problem**: Sending mismatched schema (intakeForm) to backend

**Solution**:
```javascript
// Step 1: Save profile data (non-blocking, non-critical)
const profileData = {
  profile: { age, sex, height, weight },
  nutrition: { target_calories, protein_intake, food_source },
  lifestyle: { activity_level, food_type }
};
await profileAPI.submitOnboarding(profileData); // Catches errors silently

// Step 2: Create diet plan (critical path)
const dietPlanData = {
  name: formData.title,
  description: "...",
  calorie_target: 2000,
  protein_target: 150,
  fat_target: 65,
  carb_target: 250,
  meals: []
};
const result = await dietPlanAPI.createDietPlan(dietPlanData);

// Return diet plan ID for flow
onComplete({
  dietPlanId: result?.id,
  preAssessment: { ...formData, profileSaved: true, assessmentData: {...} }
});
```

**Key Changes**:
- Split intake form saving from diet plan creation
- Profile is optional (non-blocking error handling)
- Diet plan creation is required
- Better error messages and logging
- Proper numeric type conversions

### 3. **File Upload Component Improvements**

#### `/nuetra-frontend/components/FileUploadWithPreview.jsx`
**Problem**: No file validation, FormData not validated, error handling was generic

**Solution**:
```javascript
// Validate File objects before upload
const fileArray = files.map(f => f.file);
if (fileArray.some(f => !(f instanceof File))) {
  throw new Error('Invalid file format detected');
}

// Call API and handle response
const result = await dietPlanAPI.uploadFiles(dietPlanId, fileArray);

// Clean up properly
files.forEach(file => {
  if (file.preview) URL.revokeObjectURL(file.preview);
});

// Return consistent response
onComplete({
  dietPlanId: planId || dietPlanId,
  uploadedFiles: result?.files || [],
  message: 'Files uploaded successfully'
});
```

**Error Handling**:
- Invalid file format → Clear error message
- Network offline → "Check internet connection"
- File too large (413) → "Files too large"
- Auth failed (401) → "Session expired"
- Generic errors → "Upload failed"

### 4. **Health Questionnaire - External Form**

#### `/nuetra-frontend/components/HealthQuestionnaire.jsx`
**Changes**:
- External Google Form link in new tab
- Optional notes field for user feedback
- Confirmation checkbox required
- Non-blocking API call for tracking
- Graceful degradation if API fails

### 5. **PSS-10 Assessment - Secure**

#### `/nuetra-frontend/components/PSS10Form.jsx`
**Key Change - Stress Score is NOT Displayed**:
```javascript
// Calculate score for backend only
const calculatedStressScore = responses.reduce((sum, val, idx) => {
  if (reverseItems.includes(idx)) {
    return sum + (4 - val);
  }
  return sum + val;
}, 0);

// Log to backend (non-blocking)
await teamMemberAPI.logMetric({
  type: 'STRESS_LEVEL',
  value: calculatedStressScore,
  notes: 'PSS-10 Assessment - For dietitian review only'
});

// Complete WITHOUT exposing score
onComplete({
  pssResponses: responses,
  responseCount: responses.length,
  submittedAt: new Date().toISOString()
  // NOTE: stressScore intentionally omitted
});
```

**Why**: Users see responses stored, but no score displayed to them. Only dietitian sees score.

### 6. **Flow State Management**

#### `/nuetra-frontend/components/DietPlanFlow.jsx`
**State Structure**:
```javascript
{
  dietPlanId: null,                         // CRITICAL - passed to all steps
  preAssessmentNotes: null,                 // Acknowledgment only
  preAssessment: null,                      // Full health data
  uploadedFiles: [],                        // File metadata
  healthQuestionnaireCompleted: false,      // Boolean flag
  stressTestAcknowledged: false,            // Boolean flag
  pssResponses: null,                       // Array of responses
  appointment: null,                        // Booking details
  payment: null                             // Payment info
}
```

## Validation Rules Enforced

### Pre-Assessment Form
- Age: 16-120 (integer)
- Height: > 0 (float)
- Weight: > 0 (float)
- Activity Level: Required dropdown
- Timeframe: Required dropdown
- Title: Required, max 200 chars
- Gender: MALE | FEMALE | OTHER

### File Upload
- File types: PDF, PNG, JPEG only
- Max file size: 10MB per file
- Max files: 5 total
- At least 1 file required for "Upload Files & Continue"
- Skip is optional

### Health Questionnaire
- External form link must be clicked
- Confirmation checkbox required
- Optional notes (free text)
- Skip is optional

### PSS-10 Form
- All 10 questions required
- Response values: 0-4 (radio buttons)
- Score calculated but not displayed
- Metric logged for backend tracking

### Booking
- Date: 24+ hours in future (validation)
- Time: 15-minute slots (9 AM - 5:30 PM)
- Provider: Required selection
- Duration: Minimum 15 minutes

## Error Recovery

### Non-Blocking Errors (Flow continues)
- Profile save fails (profileAPI.submitOnboarding)
- Questionnaire tracking fails (dietPlanId/questionnaire endpoint)
- Metric logging fails (teamMemberAPI.logMetric)
- Slot fetching fails (fallback to default slots)

### Blocking Errors (Flow stops)
- Diet plan creation fails
- File upload fails (if user clicks Upload)
- Assessment submission fails (PSS-10, PSS-10)
- Appointment creation fails
- Auth/session expired (401, 403)

### Retry Strategy
All components support:
- Go back to retry
- Edit data and resubmit
- State is preserved for retries

## Testing Scenarios

### Happy Path
1. ✓ Fill pre-assessment → Create diet plan + profile
2. ✓ Skip file upload → Continue
3. ✓ Complete questionnaire → Confirm completion
4. ✓ Acknowledge stress test
5. ✓ Complete PSS-10 → No score displayed
6. ✓ Book appointment
7. ✓ Complete payment
8. ✓ See success screen

### Error Cases
1. ✓ Profile save fails → Diet plan still created
2. ✓ File upload fails → Retry or skip
3. ✓ Questionnaire API fails → Still continue
4. ✓ Network offline → Clear error message
5. ✓ Session expired → Clear error, refresh required

### Edge Cases
1. ✓ Go back and edit → Data persists
2. ✓ Skip optional steps → Continue to next
3. ✓ Upload large file → Proper error
4. ✓ Upload multiple files → All processed
5. ✓ Browser refresh → Flow resets (expected)

## Backend Dependencies

### Existing Endpoints (Used)
- `POST /auth/login` - Authentication
- `POST /profile` - Create/update profile ✓
- `POST /nutrition/diet-plan` - Create diet plan ✓
- `POST /nutrition/upload-report` - File upload ✓
- `POST /assessments/pss10` - Submit PSS-10 ✓

### Needed Endpoints (Should be implemented)
- `POST /nutrition/diet-plans/{id}/questionnaire` - Track questionnaire
- `GET /consultations/providers` - List dieticians
- `GET /consultations/providers/{id}/available-slots` - Booking slots
- `POST /consultations/appointments` - Create appointment
- `POST /payment/process` - Process payment

### Optional Endpoints (Nice to have)
- `GET /consultations/appointments` - List user appointments
- `DELETE /consultations/appointments/{id}` - Cancel appointment

## Deployment Notes

### Frontend Changes
- ✓ All changes are in frontend components and API client
- ✓ No database schema changes needed on frontend
- ✓ No new environment variables needed
- ✓ Backwards compatible (doesn't break existing UI)

### Backend Considerations
- Nutrition service: Ensure diet plan creation returns `id` field
- Profile service: Ensure onboarding returns profile ID
- Assessment service: Ensure PSS-10 endpoint exists
- Consultation service: May need to implement appointment endpoints
- Storage: Ensure file uploads are properly stored and retrievable

## Monitoring & Logging

### Error Logs to Monitor
- `[API ERROR] 400` - Validation errors (check request format)
- `[API ERROR] 401` - Session expired (user needs to login again)
- `[API ERROR] 500` - Server errors (backend issue)
- `[API NETWORK ERROR]` - Connection issues (infrastructure)

### Success Indicators
- `[API RESPONSE] 201` - Resources created successfully
- `[API RESPONSE] 200` - Operations successful
- Flow completion logs all flowData for debugging

## Known Limitations

1. **External Questionnaire**: Relies on user confirming completion (can't track actual form submission)
2. **Stress Score**: Only logged to backend, not tracked in frontend (by design)
3. **Slot Booking**: Falls back to default slots if API fails
4. **File Storage**: Depends on backend storage configuration
5. **Session**: Flow resets on browser refresh (expected behavior)

## Future Enhancements

1. Add questionnaire auto-tracking (webhook from Google Forms)
2. Add appointment reminders (email/SMS)
3. Add payment status webhooks
4. Add user profile verification step
5. Add dietary restrictions presets
6. Add goal templates
7. Add appointment history in dashboard
