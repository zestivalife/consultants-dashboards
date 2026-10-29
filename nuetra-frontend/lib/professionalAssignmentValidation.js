const POSTGRES_UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const PROFESSIONAL_ID_PATTERN = /^(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|ext_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$/i;

export function validateProfessionalAssignmentPayload(payload, batch = false) {
  const fieldErrors = {};
  const validUuid = (value) => typeof value === 'string' && POSTGRES_UUID_PATTERN.test(value.trim());
  const clientIds = batch ? payload?.clientUserIds : [payload?.clientUserId];

  if (!Array.isArray(clientIds) || clientIds.length < 1 || clientIds.length > 100) {
    fieldErrors[batch ? 'clientUserIds' : 'clientUserId'] = 'Select between 1 and 100 clients.';
  } else if (clientIds.some((value) => !validUuid(value))) {
    fieldErrors[batch ? 'clientUserIds' : 'clientUserId'] = 'A selected client does not have a canonical assignable identity.';
  }
  if (typeof payload?.professionalUserId !== 'string' || !PROFESSIONAL_ID_PATTERN.test(payload.professionalUserId.trim())) {
    fieldErrors.professionalUserId = 'The selected consultant does not have a canonical professional identity.';
  }
  if (!['CONSULTANT', 'PRACTITIONER', 'MENTOR'].includes(payload?.professionalType)) {
    fieldErrors.professionalType = 'Select a supported professional type.';
  }
  if (typeof payload?.relationshipType !== 'string' || payload.relationshipType.trim().length < 2 || payload.relationshipType.trim().length > 80) {
    fieldErrors.relationshipType = 'Select a valid relationship type.';
  }
  if (payload?.reason !== undefined && (typeof payload.reason !== 'string' || payload.reason.trim().length > 240)) {
    fieldErrors.reason = 'The assignment reason must be 240 characters or fewer.';
  }
  if (typeof payload?.allowReassignment !== 'boolean') {
    fieldErrors.allowReassignment = 'Reassignment confirmation must be explicitly provided.';
  }

  const firstError = Object.entries(fieldErrors)[0];
  if (firstError) {
    const error = new Error(firstError[1]);
    error.code = 'INVALID_ASSIGNMENT_PAYLOAD';
    error.fieldErrors = fieldErrors;
    throw error;
  }
  return payload;
}
