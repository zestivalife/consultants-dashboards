export function buildWorkflowSteps({ stepDefinitions = {}, orderedStepIds = [] }) {
  return orderedStepIds
    .map((stepId) => stepDefinitions[stepId])
    .filter(Boolean)
    .map((step) => ({ ...step }));
}

export function getWorkflowStepIndex(steps = [], stepId) {
  if (!stepId) return -1;
  return steps.findIndex((step) => step.id === stepId);
}

export function getWorkflowStepId(steps = [], index = 0, fallback = '') {
  return steps[index]?.id || steps[0]?.id || fallback;
}

export function getWorkflowLastStepIndex(steps = [], preferredLastStepId) {
  const preferredIndex = getWorkflowStepIndex(steps, preferredLastStepId);
  return preferredIndex >= 0 ? preferredIndex : Math.max(0, steps.length - 1);
}
