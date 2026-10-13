import { useMemo } from 'react';
import { CAPABILITY_STATE, buildAnalyticsViewModel, buildModuleViewModel } from './externalP1ViewModels.mjs';

function StatusPanel({ capability, emptyMessage, isEmpty }) {
  if (capability.state === CAPABILITY_STATE.LOADING) return <div role="status" className="min-h-28 animate-pulse rounded-2xl bg-slate-100 p-5">{capability.message}</div>;
  if (capability.state === CAPABILITY_STATE.ERROR) return <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-800">{capability.message}</div>;
  if (capability.state === CAPABILITY_STATE.UNAVAILABLE) return <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5"><p className="font-semibold text-amber-950">Coming when connected</p><p className="mt-1 text-sm text-amber-800">{capability.message}</p></div>;
  if (isEmpty) return <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-600">{emptyMessage}</div>;
  return null;
}

export function ExternalP1ModuleSurface({ moduleKey, capabilities, records, metrics, loading, error, renderRecord, primaryAction }) {
  const model = useMemo(() => moduleKey === 'analytics'
    ? buildAnalyticsViewModel({ capabilities, metrics, loading, error })
    : buildModuleViewModel({ moduleKey, capabilities, records, loading, error }), [moduleKey, capabilities, records, metrics, loading, error]);
  const items = moduleKey === 'analytics' ? model.metrics : model.records;
  return (
    <section aria-labelledby={`external-p1-${moduleKey}`} className="mx-auto w-full max-w-6xl px-4 pb-[calc(6rem+env(safe-area-inset-bottom))] pt-4 sm:px-6 lg:px-8">
      <header className="mb-5"><p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-600">External practice</p><h1 id={`external-p1-${moduleKey}`} className="mt-1 text-2xl font-black tracking-tight text-slate-950 sm:text-3xl">{model.title}</h1></header>
      <StatusPanel capability={model.capability} emptyMessage={model.emptyMessage} isEmpty={model.isEmpty} />
      {model.capability.state === CAPABILITY_STATE.READY && items.length > 0 ? <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">{items.map((item, index) => <article key={item.id || item.key || index} className="min-w-0 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">{renderRecord ? renderRecord(item) : <><h2 className="break-words font-bold text-slate-950">{item.title || item.label || 'Record'}</h2>{item.value !== undefined ? <p className="mt-2 text-2xl font-black text-slate-900">{String(item.value)}</p> : null}</>}</article>)}</div> : null}
      {primaryAction && model.capability.state === CAPABILITY_STATE.READY ? <div className="fixed inset-x-0 bottom-0 z-20 border-t border-slate-200 bg-white/95 p-3 pb-[calc(.75rem+env(safe-area-inset-bottom))] backdrop-blur md:sticky md:mt-6 md:rounded-2xl md:border"><button type="button" onClick={primaryAction.onClick} className="min-h-12 w-full rounded-xl bg-blue-600 px-5 py-3 font-bold text-white focus:outline-none focus:ring-4 focus:ring-blue-200 md:ml-auto md:block md:w-auto">{primaryAction.label}</button></div> : null}
    </section>
  );
}
