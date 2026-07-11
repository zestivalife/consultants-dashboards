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
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'inline-flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-bold transition-colors disabled:cursor-not-allowed disabled:opacity-60',
        tone === 'primary'
          ? 'bg-[#237afc] text-white shadow-md hover:bg-[#1a62d6]'
          : 'border border-gray-200 bg-white text-gray-700 hover:border-[#237afc] hover:text-[#237afc]'
      )}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}

export function ControlBar({
  searchPlaceholder,
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
