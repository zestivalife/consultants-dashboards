import { BadgeCheck, Search } from 'lucide-react';

export function cn(...values) {
  return values.filter(Boolean).join(' ');
}

export function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
}

export function StatPill({ icon: Icon, label, value, tone = 'from-[#237afc] to-[#58b6ff]' }) {
  return (
    <div className="rounded-2xl border border-gray-100 bg-gradient-to-br from-white to-gray-50 p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[11px] font-black uppercase tracking-[0.24em] text-gray-400">{label}</p>
          <p className="mt-3 text-3xl font-black tracking-tight text-gray-900">{value}</p>
        </div>
        <div className={cn('rounded-2xl bg-gradient-to-br p-3 text-white shadow-sm', tone)}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

export function ModuleFrame({ badge, title, description, actions, children }) {
  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-[#f2f2f7] bg-white p-8 shadow-[0px_4px_4px_-1px_rgba(12,12,13,0.1),0px_4px_4px_-1px_rgba(12,12,13,0.05)]">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-[11px] font-black uppercase tracking-[0.24em] text-[#237afc]">
              <BadgeCheck className="h-3.5 w-3.5" />
              {badge}
            </div>
            <h2 className="mt-4 text-3xl font-black tracking-tight text-gray-900">{title}</h2>
            <p className="mt-2 max-w-3xl text-sm text-gray-500">{description}</p>
          </div>
          {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
        </div>
        <div className="mt-8">{children}</div>
      </div>
    </div>
  );
}

export function ActionButton({ icon: Icon, label, tone = 'secondary', onClick, type = 'button', disabled = false }) {
  const toneClasses = {
    primary: 'border-[#237afc] bg-[#237afc] text-white shadow-md hover:bg-[#1a62d6]',
    secondary: 'border border-gray-200 bg-white text-gray-700 hover:border-[#237afc] hover:text-[#237afc]',
    ghost: 'border border-transparent bg-gray-50 text-gray-600 hover:bg-gray-100 hover:text-gray-900',
    text: 'border border-transparent bg-transparent text-[#237afc] hover:bg-blue-50',
    danger: 'border border-red-200 bg-red-50 text-red-700 hover:border-red-300 hover:bg-red-100',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'inline-flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60',
        toneClasses[tone] || toneClasses.secondary
      )}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}

export function ControlBar({
  searchPlaceholder,
  searchValue = '',
  onSearchChange,
  onSearchKeyDown,
  filters = [],
  activeFilter,
  onFilterChange,
  rightControls,
}) {
  return (
    <div className="flex flex-col gap-4 rounded-3xl border border-gray-100 bg-gray-50/70 p-4 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-1 items-center gap-3 rounded-2xl border border-gray-200 bg-white px-4 py-3">
        <Search className="h-4 w-4 text-gray-400" />
        <input
          type="text"
          value={searchValue}
          onChange={(event) => onSearchChange?.(event.target.value)}
          onKeyDown={onSearchKeyDown}
          placeholder={searchPlaceholder}
          className="w-full bg-transparent text-sm text-gray-900 outline-none placeholder:text-gray-400"
        />
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {filters.map((filter) => (
          <button
            key={filter.key}
            onClick={() => onFilterChange?.(filter.key)}
            className={cn(
              'rounded-full border px-4 py-2 text-sm font-bold transition-colors',
              activeFilter === filter.key
                ? 'bg-[#237afc] text-white shadow-sm border-[#237afc]'
                : 'bg-white text-gray-600 border-gray-200 hover:border-[#237afc] hover:text-[#237afc]'
            )}
          >
            {filter.label}
          </button>
        ))}
        {rightControls}
      </div>
    </div>
  );
}

export function Badge({ children, tone = 'neutral' }) {
  const tones = {
    neutral: 'bg-gray-100 text-gray-700 border-gray-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    green: 'bg-green-50 text-green-700 border-green-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    violet: 'bg-violet-50 text-violet-700 border-violet-200',
    red: 'bg-red-50 text-red-700 border-red-200',
  };
  return <span className={cn('rounded-full border px-3 py-1 text-xs font-bold', tones[tone])}>{children}</span>;
}

export function Panel({ title, subtitle, action, children }) {
  return (
    <div className="rounded-3xl border border-gray-100 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-gray-900">{title}</h3>
          {subtitle ? <p className="mt-1 text-sm text-gray-500">{subtitle}</p> : null}
        </div>
        {action}
      </div>
      <div className="mt-5">{children}</div>
    </div>
  );
}

export function MiniBarChart({ data, suffix = '', color = 'from-[#237afc] to-[#58b6ff]' }) {
  const max = Math.max(...data.map((item) => item.value), 1);
  return (
    <div className="space-y-3">
      {data.map((item) => (
        <div key={item.label}>
          <div className="mb-1 flex items-center justify-between text-sm">
            <span className="font-medium text-gray-700">{item.label}</span>
            <span className="font-bold text-gray-900">
              {item.value}
              {suffix}
            </span>
          </div>
          <div className="h-2 rounded-full bg-gray-100">
            <div
              className={cn('h-2 rounded-full bg-gradient-to-r', color)}
              style={{ width: `${(item.value / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="rounded-3xl border border-dashed border-gray-200 bg-white px-6 py-16 text-center">
      <Icon className="mx-auto h-10 w-10 text-gray-300" />
      <h4 className="mt-4 text-lg font-bold text-gray-900">{title}</h4>
      <p className="mt-2 text-sm text-gray-500">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function WorkflowModal({
  eyebrow,
  title,
  description,
  steps = [],
  activeStep = 0,
  onStepChange,
  onClose,
  footer,
  children,
}) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/40 p-0 md:p-6">
      <div className="flex h-dvh w-full flex-col overflow-hidden bg-white shadow-2xl md:h-[760px] md:max-h-[92vh] md:max-w-5xl md:rounded-[28px]">
        <WorkflowHeader eyebrow={eyebrow} title={title} description={description} onClose={onClose} />

        <div className="sticky top-0 z-10 shrink-0 border-b border-gray-100 bg-white px-5 py-3 md:px-6">
          <WizardStepper steps={steps} activeStep={activeStep} onStepChange={onStepChange} />
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto bg-gray-50 px-5 py-5 md:px-6 md:py-6">{children}</div>

        {footer ? <WorkflowFooter>{footer}</WorkflowFooter> : null}
      </div>
    </div>
  );
}

export function WorkflowHeader({ eyebrow, title, description, onClose }) {
  return (
    <header className="sticky top-0 z-20 shrink-0 border-b border-gray-100 bg-white px-5 py-5 md:px-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          {eyebrow ? <p className="z-label text-[#237afc]">{eyebrow}</p> : null}
          <h3 className="mt-2 z-h1 text-gray-900">{title}</h3>
          {description ? <p className="mt-2 max-w-3xl z-body text-gray-500">{description}</p> : null}
        </div>
        <button type="button" onClick={onClose} className="z-btn z-btn-secondary">
          Cancel
        </button>
      </div>
    </header>
  );
}

export function WorkflowFooter({ children }) {
  return (
    <footer className="sticky bottom-0 z-20 shrink-0 border-t border-gray-100 bg-white px-5 py-4 md:px-6">
      {children}
    </footer>
  );
}

export function WizardStepper({ steps = [], activeStep = 0, onStepChange }) {
  return (
    <div className="-mx-1 flex min-h-[72px] gap-2 overflow-x-auto px-1 pb-1" aria-label="Workflow steps">
      {steps.map((step, index) => (
        <button
          key={step.id || step.label}
          type="button"
          onClick={() => onStepChange?.(index)}
          className={cn(
            'min-w-[132px] rounded-2xl border px-3 py-2 text-left transition md:min-w-[148px]',
            activeStep === index
              ? 'border-[#237afc] bg-[#f5f9ff] text-[#237afc]'
              : index < activeStep
                ? 'border-emerald-100 bg-emerald-50 text-emerald-700'
                : 'border-gray-100 bg-gray-50 text-gray-500'
          )}
        >
          <span className="block z-label text-current">Step {index + 1}</span>
          <span className="mt-1 block z-table-content font-semibold">{step.label}</span>
        </button>
      ))}
    </div>
  );
}

export function WorkflowCard({ title, description, children }) {
  return (
    <section className="rounded-[24px] border border-gray-100 bg-white p-5 shadow-sm">
      <SectionHeader title={title} description={description} />
      <div className="mt-5">{children}</div>
    </section>
  );
}

export function FormSection({ title, description, children }) {
  return (
    <section className="space-y-4">
      <SectionHeader title={title} description={description} />
      {children}
    </section>
  );
}

export function SectionHeader({ title, description }) {
  if (!title && !description) return null;
  return (
    <div>
      {title ? <h4 className="z-h3 text-gray-900">{title}</h4> : null}
      {description ? <p className="mt-2 z-body text-gray-500">{description}</p> : null}
    </div>
  );
}

export function ReviewCard({ label, value }) {
  return (
    <div className="rounded-2xl bg-gray-50 px-4 py-3">
      <p className="z-label text-gray-500">{label}</p>
      <p className="mt-1 z-table-content font-semibold text-gray-900">{value}</p>
    </div>
  );
}

export function Field({ label, helper, error, children }) {
  return (
    <label className="block">
      {label ? <span className="mb-2 block z-label text-gray-500">{label}</span> : null}
      {children}
      {helper ? <span className="mt-2 block z-subtitle text-gray-500">{helper}</span> : null}
      {error ? <span className="mt-2 block z-subtitle text-red-600">{error}</span> : null}
    </label>
  );
}
