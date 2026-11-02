const rejectedReadiness = (reason) => ({
  outcome: reason?.status === 404 ? 'UNAVAILABLE' : 'ERROR',
});

export async function loadDietPlanWorkspace({
  clientId,
  preferredId = '',
  currentId = '',
  api,
  projectDetail,
}) {
  const [plansResult, assessmentResult, contextResult] = await Promise.allSettled([
    api.list(clientId),
    api.assessment(clientId),
    api.context(clientId),
  ]);

  const readiness = assessmentResult.status === 'fulfilled'
    ? {
        outcome: assessmentResult.value.readiness_status || assessmentResult.value.readiness?.outcome || 'NOT_STARTED',
        assessmentId: assessmentResult.value.id,
        assessmentVersion: assessmentResult.value.current_version || assessmentResult.value.version,
      }
    : rejectedReadiness(assessmentResult.reason);
  const healthContext = contextResult.status === 'fulfilled' ? contextResult.value : null;
  const errors = [];

  if (plansResult.status === 'rejected') {
    errors.push(plansResult.reason);
    if (assessmentResult.status === 'rejected') errors.push(assessmentResult.reason);
    if (contextResult.status === 'rejected') errors.push(contextResult.reason);
    return {
      plansStatus: 'error',
      plans: null,
      selectedId: currentId,
      preferredLoaded: false,
      loadError: 'Diet plans could not be loaded.',
      readiness,
      healthContext,
      errors,
    };
  }

  if (assessmentResult.status === 'rejected') errors.push(assessmentResult.reason);
  if (contextResult.status === 'rejected') errors.push(contextResult.reason);
  const details = await Promise.allSettled(
    (plansResult.value.items || []).map((item) => api.detail(item.id).then(projectDetail)),
  );
  const plans = details.filter((item) => item.status === 'fulfilled').map((item) => item.value);
  const failedDetails = details.length - plans.length;
  details.filter((item) => item.status === 'rejected').forEach((item) => errors.push(item.reason));
  const selectedId = preferredId && plans.some((plan) => plan.id === preferredId)
    ? preferredId
    : plans.some((plan) => plan.id === currentId)
      ? currentId
      : plans[0]?.id || '';

  return {
    plansStatus: failedDetails ? 'partial' : 'ready',
    plans,
    selectedId,
    preferredLoaded: Boolean(preferredId) && plans.some((plan) => plan.id === preferredId),
    loadError: failedDetails
      ? `${failedDetails} Diet Plan ${failedDetails === 1 ? 'detail could' : 'details could'} not be loaded.`
      : '',
    readiness,
    healthContext,
    errors,
  };
}

export function createdDraftPresentation(createdId, loadResult) {
  if (loadResult.preferredLoaded) {
    return { state: 'ready', createdId, message: 'Draft created and ready for editing.' };
  }
  return {
    state: 'reload_failed',
    createdId,
    message: `Draft ${createdId} was created, but could not be reloaded. Retry loading this draft; do not create another one.`,
  };
}
