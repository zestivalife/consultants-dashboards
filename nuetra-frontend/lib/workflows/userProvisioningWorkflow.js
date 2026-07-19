import {
  buildWorkflowSteps,
  getWorkflowLastStepIndex,
  getWorkflowStepId,
  getWorkflowStepIndex,
} from './workflowEngine';

export const USER_PROVISIONING_STEP_DEFINITIONS = {
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
  products: {
    id: 'products',
    label: 'Products',
    title: 'Select products',
  },
  review: {
    id: 'review',
    label: 'Review',
    title: 'Review user',
  },
  create: {
    id: 'create',
    label: 'Create',
    title: 'Create user',
  },
};

const USER_PROVISIONING_PRODUCT_WORKFLOWS = {
  pending: ['role', 'contact', 'platform'],
  nuetra: ['role', 'contact', 'platform', 'organization', 'workspace', 'products', 'review', 'create'],
  fiteatsy: ['role', 'contact', 'platform', 'products', 'review', 'create'],
};

export function getUserProvisioningProductMode(product, platformKey = '') {
  if (/fiteatsy/i.test(platformKey)) return 'fiteatsy';
  if (/nuetra/i.test(platformKey)) return 'nuetra';
  if (!product) return 'pending';
  return /fiteatsy/i.test(product.name || '') ? 'fiteatsy' : 'nuetra';
}

export function buildUserProvisioningWorkflowSteps({ selectedProduct, selectedPlatformKey }) {
  const productMode = getUserProvisioningProductMode(selectedProduct, selectedPlatformKey);
  return buildWorkflowSteps({
    stepDefinitions: USER_PROVISIONING_STEP_DEFINITIONS,
    orderedStepIds: USER_PROVISIONING_PRODUCT_WORKFLOWS[productMode] || USER_PROVISIONING_PRODUCT_WORKFLOWS.pending,
  });
}

export function getUserProvisioningWorkflowState({ steps, activeStep, selectedProduct, selectedPlatformKey }) {
  const productMode = getUserProvisioningProductMode(selectedProduct, selectedPlatformKey);
  const stepId = getWorkflowStepId(steps, activeStep, 'role');
  const createStepIndex = getWorkflowStepIndex(steps, 'create');
  const lastStepIndex = getWorkflowLastStepIndex(steps, 'create');
  const scopeStepId = 'products';

  return {
    productMode,
    stepId,
    createStepIndex,
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
