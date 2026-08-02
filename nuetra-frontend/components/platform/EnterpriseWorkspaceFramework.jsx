import {
  BadgeCheck,
  MoreHorizontal,
  Search,
} from 'lucide-react';

import { cn } from './OwnerConsolePrimitives';

export function EnterpriseWorkspaceLayout({ children, className = '' }) {
  return <div className={cn('space-y-6', className)}>{children}</div>;
}

export function EnterprisePageHeader({ badge, title, description, actions }) {
  return (
    <div className="rounded-3xl border border-gray-100/80 bg-white p-6 shadow-[0_1px_3px_rgba(15,23,42,0.05)] md:p-7">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div>
          {badge ? (
            <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 z-label tracking-[0.14em] text-[#237afc]">
              <BadgeCheck className="h-3.5 w-3.5" />
              {badge}
            </div>
          ) : null}
          <h2 className="mt-4 z-h1 text-gray-900">{title}</h2>
          {description ? <p className="mt-2 max-w-3xl z-body text-gray-500">{description}</p> : null}
        </div>
        {actions ? <EnterprisePageActions>{actions}</EnterprisePageActions> : null}
      </div>
    </div>
  );
}

export function EnterprisePageActions({ children }) {
  return <div className="flex flex-wrap items-center gap-3">{children}</div>;
}

export function EnterpriseWorkspaceContent({ children, className = '' }) {
  return <div className={cn('rounded-3xl border border-gray-100/80 bg-white p-6 shadow-[0_1px_3px_rgba(15,23,42,0.05)] md:p-7', className)}>{children}</div>;
}

export function EnterpriseCollectionToolbar({ left, right, children, className = '' }) {
  return (
    <div className={cn('flex flex-col gap-4 rounded-[28px] border border-gray-100 bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)] lg:p-5', className)}>
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="min-w-0 flex-1">{left || children}</div>
        {right ? <div className="flex flex-wrap items-center gap-2">{right}</div> : null}
      </div>
    </div>
  );
}

export function EnterpriseSmartSearch({
  label = 'Smart search',
  summary,
  value,
  onChange,
  onKeyDown,
  onClear,
  placeholder,
  inputRef,
  loading = false,
  recentSearches = [],
  onRecentSearch,
  activeFilters = [],
  onClearAll,
  loadingLabel = 'Refreshing',
}) {
  return (
    <>
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.16em] text-gray-400">{label}</p>
          {summary ? <p className="text-sm font-semibold text-gray-500">{summary}</p> : null}
        </div>
        {loading ? <EnterpriseStatusBadge tone="blue">{loadingLabel}</EnterpriseStatusBadge> : null}
      </div>
      <div className="flex items-center gap-2 rounded-2xl border border-gray-200 bg-gray-50/70 px-4 py-3 shadow-inner transition focus-within:border-[#237afc] focus-within:bg-white focus-within:ring-4 focus-within:ring-blue-50">
        <Search className="h-4 w-4 shrink-0 text-gray-400" />
        <input
          ref={inputRef}
          type="search"
          value={value}
          onChange={(event) => onChange?.(event.target.value)}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          aria-label={placeholder || label}
          className="w-full bg-transparent text-sm font-semibold text-gray-900 outline-none placeholder:text-gray-400"
        />
        {value ? (
          <button type="button" onClick={onClear} className="rounded-full px-2 py-1 text-xs font-black text-gray-400 transition hover:bg-gray-100 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-100">
            Clear
          </button>
        ) : (
          <kbd className="hidden rounded-lg border border-gray-200 bg-gray-50 px-2 py-1 text-[11px] font-black text-gray-400 md:inline-flex">⌘K</kbd>
        )}
      </div>
      {recentSearches.length ? (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="text-xs font-black uppercase tracking-[0.16em] text-gray-400">Recent</span>
          {recentSearches.map((search) => (
            <button
              key={search}
              type="button"
              onClick={() => onRecentSearch?.(search)}
              className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs font-bold text-gray-600 transition hover:border-[#237afc] hover:text-[#237afc] focus:outline-none focus:ring-2 focus:ring-blue-100"
            >
              {search}
            </button>
          ))}
        </div>
      ) : null}
      {activeFilters.length ? (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="text-xs font-black uppercase tracking-[0.16em] text-gray-400">Applied</span>
          {activeFilters.map((filter) => (
            <button
              key={filter.key}
              type="button"
              onClick={filter.onClick}
              className="inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-xs font-bold text-blue-700 transition hover:border-blue-200 hover:bg-white"
            >
              {filter.label}
            </button>
          ))}
          {onClearAll ? (
            <button type="button" onClick={onClearAll} className="rounded-full px-3 py-1.5 text-xs font-black text-gray-400 transition hover:bg-gray-100 hover:text-gray-700">
              Clear all
            </button>
          ) : null}
        </div>
      ) : null}
    </>
  );
}

export function EnterpriseFilterDrawer({ open, title = 'Filters', children, footer, onClose }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/30" role="dialog" aria-modal="true">
      <div className="flex h-full w-full max-w-md flex-col bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-gray-400">Collection controls</p>
            <h3 className="mt-1 text-xl font-black text-gray-900">{title}</h3>
          </div>
          <button type="button" onClick={onClose} className="rounded-xl border border-gray-200 px-3 py-2 text-sm font-black text-gray-600 transition hover:bg-gray-50">
            Close
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">{children}</div>
        {footer ? <div className="border-t border-gray-100 px-6 py-4">{footer}</div> : null}
      </div>
    </div>
  );
}

export function EnterpriseTable({ columns = [], children, className = '' }) {
  return (
    <div className={cn('overflow-hidden rounded-3xl border border-gray-100 bg-white', className)}>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-100">
          <thead className="sticky top-0 z-10 bg-gray-50/90 backdrop-blur">
            <tr>
              {columns.map((column) => (
                <th key={column.key} scope="col" className={cn('px-4 py-3 text-left text-xs font-black uppercase tracking-[0.14em] text-gray-400', column.className || '')}>
                  {column.header || column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">{children}</tbody>
        </table>
      </div>
    </div>
  );
}

export function EnterprisePagination({ page = 1, pageSize = 20, total = 0, onPageChange, onPageSizeChange, pageSizeOptions = [10, 20, 50, 100] }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="flex flex-col gap-3 rounded-3xl border border-gray-100 bg-white px-4 py-3 text-sm font-bold text-gray-600 sm:flex-row sm:items-center sm:justify-between">
      <span>
        Page {page} of {totalPages} · {total} total records
      </span>
      <div className="flex flex-wrap items-center gap-2">
        {onPageSizeChange ? (
          <select value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))} className="rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-bold outline-none focus:border-[#237afc]">
            {pageSizeOptions.map((size) => <option key={size} value={size}>{size} / page</option>)}
          </select>
        ) : null}
        <button type="button" onClick={() => onPageChange?.(Math.max(1, page - 1))} disabled={page <= 1} className="rounded-xl border border-gray-200 px-3 py-2 transition hover:border-[#237afc] hover:text-[#237afc] disabled:cursor-not-allowed disabled:opacity-40">
          Previous
        </button>
        <button type="button" onClick={() => onPageChange?.(Math.min(totalPages, page + 1))} disabled={page >= totalPages} className="rounded-xl border border-gray-200 px-3 py-2 transition hover:border-[#237afc] hover:text-[#237afc] disabled:cursor-not-allowed disabled:opacity-40">
          Next
        </button>
      </div>
    </div>
  );
}

export function EnterpriseBulkToolbar({ selectedCount = 0, actions }) {
  if (!selectedCount) return null;
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-3xl border border-blue-100 bg-blue-50 px-4 py-3">
      <p className="text-sm font-black text-blue-800">{selectedCount} selected</p>
      <div className="flex flex-wrap items-center gap-2">{actions}</div>
    </div>
  );
}

export function EnterpriseActionMenu({ open, onToggle, children }) {
  return (
    <div className="relative">
      <button type="button" onClick={onToggle} className="rounded-xl border border-gray-200 p-2 text-gray-500 transition hover:bg-gray-50" aria-haspopup="menu" aria-expanded={open}>
        <MoreHorizontal className="h-4 w-4" />
      </button>
      {open ? (
        <div className="absolute right-0 top-11 z-30 min-w-[180px] overflow-hidden rounded-2xl border border-gray-100 bg-white p-1 shadow-xl" role="menu">
          {children}
        </div>
      ) : null}
    </div>
  );
}

export function EnterpriseToast({ message, type = 'success', onClose }) {
  if (!message) return null;
  const tones = {
    success: 'border-emerald-100 bg-emerald-50 text-emerald-800',
    error: 'border-red-100 bg-red-50 text-red-800',
    info: 'border-blue-100 bg-blue-50 text-blue-800',
  };
  return (
    <div className={cn('fixed right-5 top-24 z-50 rounded-2xl border px-4 py-3 text-sm font-bold shadow-xl', tones[type] || tones.info)}>
      <div className="flex items-center gap-3">
        <span>{message}</span>
        {onClose ? <button type="button" onClick={onClose} className="text-current opacity-70 hover:opacity-100">Dismiss</button> : null}
      </div>
    </div>
  );
}

export function EnterpriseConfirmationDialog({ open, title, description, confirmLabel = 'Confirm', cancelLabel = 'Cancel', tone = 'primary', onConfirm, onCancel, children }) {
  if (!open) return null;
  const confirmTone = tone === 'danger' ? 'border-red-600 bg-red-600 text-white hover:bg-red-700' : 'border-[#237afc] bg-[#237afc] text-white hover:bg-[#1a62d6]';
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4" role="dialog" aria-modal="true">
      <div className="w-full max-w-lg rounded-[28px] bg-white p-6 shadow-2xl">
        <h3 className="text-xl font-black text-gray-900">{title}</h3>
        {description ? <p className="mt-2 text-sm font-semibold text-gray-500">{description}</p> : null}
        {children ? <div className="mt-5">{children}</div> : null}
        <div className="mt-6 flex flex-wrap justify-end gap-3">
          <button type="button" onClick={onCancel} className="rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-black text-gray-700 transition hover:bg-gray-50">
            {cancelLabel}
          </button>
          <button type="button" onClick={onConfirm} className={cn('rounded-xl border px-4 py-3 text-sm font-black transition', confirmTone)}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export function EnterpriseEmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="rounded-3xl border border-dashed border-gray-200 bg-white px-6 py-16 text-center">
      {Icon ? <Icon className="mx-auto h-10 w-10 text-gray-300" /> : null}
      <h4 className="mt-4 z-h3 text-gray-900">{title}</h4>
      {description ? <p className="mt-2 z-body text-gray-500">{description}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function EnterpriseSkeleton({ rows = 5 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-16 animate-pulse rounded-2xl bg-gray-100" />
      ))}
    </div>
  );
}

export function EnterpriseLoadingOverlay({ show, label = 'Loading...' }) {
  if (!show) return null;
  return (
    <div className="absolute inset-0 z-20 flex items-center justify-center rounded-3xl bg-white/70 backdrop-blur-sm">
      <div className="rounded-2xl border border-gray-100 bg-white px-4 py-3 text-sm font-black text-gray-600 shadow-lg">{label}</div>
    </div>
  );
}

export function EnterpriseStatusBadge({ children, tone = 'neutral' }) {
  const tones = {
    neutral: 'bg-gray-100 text-gray-700 border-gray-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    green: 'bg-green-50 text-green-700 border-green-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    violet: 'bg-violet-50 text-violet-700 border-violet-200',
    red: 'bg-red-50 text-red-700 border-red-200',
  };
  return <span className={cn('rounded-full border px-3 py-1 z-label', tones[tone] || tones.neutral)}>{children}</span>;
}

export function EnterpriseChip({ children, active = false, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'rounded-full border px-4 py-2 text-sm font-bold transition-colors',
        active ? 'border-[#237afc] bg-[#237afc] text-white shadow-sm' : 'border-gray-200 bg-white text-gray-600 hover:border-[#237afc] hover:text-[#237afc]'
      )}
    >
      {children}
    </button>
  );
}

export function EnterpriseAvatar({ label, tone = 'from-[#237afc] to-[#58b6ff]' }) {
  return (
    <div className={cn('flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br text-sm font-black text-white', tone)}>
      {label}
    </div>
  );
}
