import {
  buildWorkflowSteps,
  getWorkflowLastStepIndex,
  getWorkflowStepId,
  getWorkflowStepIndex,
} from './workflowEngine';

export const INVITATION_STEP_DEFINITIONS = {
  role: {
    id: 'role',
    label: 'Role',
    title: 'Select role',
  },
  contact: {
    id: 'contact',
    label: 'Contact',
    title: 'Enter contact information',
  },
  platform: {
    id: 'platform',
    label: 'Platform',
    title: 'Select platform',
  },
  organization: {
    id: 'organization',
    label: 'Organization',
    title: 'Select organization',
  },
  workspace: {
    id: 'workspace',
    label: 'Workspace',
    title: 'Select workspace',
  },
  scope: {
    id: 'scope',
    label: 'Access Scope',
    title: 'Access Scope',
  },
  products: {
    id: 'products',
    label: 'Products',
    title: 'Select products',
  },
  review: {
    id: 'review',
    label: 'Review',
    title: 'Review invitation',
  },
  send: {
    id: 'send',
    label: 'Send',
    title: 'Send invitation',
  },
};

const INVITATION_PRODUCT_WORKFLOWS = {
  pending: ['role', 'contact', 'platform'],
  nuetra: ['role', 'contact', 'platform', 'organization', 'workspace', 'scope', 'review', 'send'],
  fiteatsy: ['role', 'contact', 'platform', 'products', 'review', 'send'],
};

export function getInvitationProductMode(product) {
  if (!product) return 'pending';
  return /fiteatsy/i.test(product.name || '') ? 'fiteatsy' : 'nuetra';
}

export function buildInvitationWorkflowSteps({ selectedProduct }) {
  const productMode = getInvitationProductMode(selectedProduct);
  return buildWorkflowSteps({
    stepDefinitions: INVITATION_STEP_DEFINITIONS,
    orderedStepIds: INVITATION_PRODUCT_WORKFLOWS[productMode] || INVITATION_PRODUCT_WORKFLOWS.pending,
  });
}

export function getInvitationWorkflowState({ steps, activeStep, selectedProduct }) {
  const productMode = getInvitationProductMode(selectedProduct);
  const stepId = getWorkflowStepId(steps, activeStep, 'role');
  const sendStepIndex = getWorkflowStepIndex(steps, 'send');
  const lastStepIndex = getWorkflowLastStepIndex(steps, 'send');
  const scopeStepId = productMode === 'fiteatsy' ? 'products' : 'scope';

  return {
    productMode,
    stepId,
    sendStepIndex,
    lastStepIndex,
    scopeStepId,
    roleStepIndex: Math.max(0, getWorkflowStepIndex(steps, 'role')),
    contactStepIndex: Math.max(0, getWorkflowStepIndex(steps, 'contact')),
    platformStepIndex: Math.max(0, getWorkflowStepIndex(steps, 'platform')),
    organizationStepIndex: Math.max(0, getWorkflowStepIndex(steps, 'organization')),
    workspaceStepIndex: Math.max(0, getWorkflowStepIndex(steps, 'workspace')),
    scopeStepIndex: Math.max(0, getWorkflowStepIndex(steps, scopeStepId)),
    requiresOrganization: productMode === 'nuetra',
    requiresWorkspace: productMode === 'nuetra',
  };
}
