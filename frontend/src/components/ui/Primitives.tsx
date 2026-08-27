import React from 'react';
import {
  AlertTriangle, CheckCircle2, HelpCircle, Loader2, OctagonAlert, RefreshCw,
} from 'lucide-react';
import type { Verdict } from '../../api/client';

/**
 * Accessibility (NFR): a verdict is never conveyed by colour alone. Every
 * badge carries an icon and a text label as well.
 */
const VERDICT_STYLE: Record<Verdict | 'UNKNOWN', {
  label: string; cls: string; Icon: React.ElementType;
}> = {
  SAFE: {
    label: 'Safe to cross',
    cls: 'bg-emerald-50 text-emerald-900 border-emerald-300',
    Icon: CheckCircle2,
  },
  MARGINAL: {
    label: 'Marginal',
    cls: 'bg-amber-50 text-amber-900 border-amber-300',
    Icon: AlertTriangle,
  },
  DO_NOT_CROSS: {
    label: 'Do not cross',
    cls: 'bg-red-50 text-red-900 border-red-300',
    Icon: OctagonAlert,
  },
  UNKNOWN: {
    label: 'No advisory',
    cls: 'bg-slate-100 text-slate-700 border-slate-300',
    Icon: HelpCircle,
  },
};

export function VerdictBadge({ verdict, size = 'md' }: {
  verdict: Verdict | 'UNKNOWN' | null | undefined;
  size?: 'sm' | 'md' | 'lg';
}) {
  const s = VERDICT_STYLE[(verdict as Verdict) ?? 'UNKNOWN'] ?? VERDICT_STYLE.UNKNOWN;
  const pad = size === 'lg' ? 'text-lg px-4 py-2 gap-2.5'
    : size === 'sm' ? 'text-xs px-2 py-0.5 gap-1'
      : 'text-sm px-3 py-1.5 gap-2';
  const icon = size === 'lg' ? 'w-6 h-6' : size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4';
  return (
    <span className={`inline-flex items-center rounded-full border font-bold ${s.cls} ${pad}`}>
      <s.Icon className={icon} aria-hidden />
      {s.label}
    </span>
  );
}

const PROVENANCE_STYLE: Record<string, string> = {
  REAL: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  SYNTHETIC: 'bg-violet-100 text-violet-800 border-violet-300',
  SYNTHETIC_STRUCTURED: 'bg-violet-100 text-violet-800 border-violet-300',
};

/** SRS 4.4: synthetic data is never displayed without this badge. */
export function ProvenanceBadge({ value, title }: { value?: string | null; title?: string }) {
  if (!value) return null;
  const label = value === 'SYNTHETIC_STRUCTURED' ? 'SYNTHETIC · schema-matched' : value;
  return (
    <span
      title={title ?? 'Data provenance (SRS 4.4)'}
      className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-bold
        tracking-wide ${PROVENANCE_STYLE[value] ?? 'bg-slate-100 text-slate-700 border-slate-300'}`}
    >
      {label}
    </span>
  );
}

const ACCESS_STYLE: Record<string, string> = {
  CONNECTED: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  ATTEMPTED: 'bg-amber-100 text-amber-800 border-amber-300',
  SUBSTITUTED: 'bg-orange-100 text-orange-900 border-orange-300',
};

export function AccessBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex rounded border px-1.5 py-0.5 text-[10px] font-bold
      ${ACCESS_STYLE[status] ?? 'bg-slate-100 text-slate-700 border-slate-300'}`}>
      {status}
    </span>
  );
}

export function StatusTag({ status }: { status: 'BUILT' | 'MOCKUP' }) {
  return status === 'BUILT' ? (
    <span className="inline-flex items-center gap-1 rounded-full border border-emerald-300
      bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-800">
      <CheckCircle2 className="h-3.5 w-3.5" aria-hidden /> BUILT
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 rounded-full border border-slate-300
      bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-700">
      <AlertTriangle className="h-3.5 w-3.5" aria-hidden /> MOCKUP
    </span>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-500" role="status">
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
      {label ?? 'Loading…'}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-900">
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
        <div className="flex-1">
          <p className="font-semibold">Could not load this panel.</p>
          <p className="mt-1 text-red-800">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center gap-1.5 rounded-md border
                border-red-300 bg-white px-3 py-1.5 font-medium text-red-800
                hover:bg-red-100"
            >
              <RefreshCw className="h-3.5 w-3.5" aria-hidden /> Retry
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8
      text-center">
      <p className="font-medium text-slate-700">{title}</p>
      {hint && <p className="mt-1 text-sm text-slate-500">{hint}</p>}
    </div>
  );
}

export function Panel({ title, subtitle, right, children, className = '' }: {
  title?: string; subtitle?: string; right?: React.ReactNode;
  children: React.ReactNode; className?: string;
}) {
  return (
    <section className={`rounded-xl border border-slate-200 bg-white shadow-sm ${className}`}>
      {(title || right) && (
        <header className="flex items-start justify-between gap-4 border-b border-slate-200
          px-5 py-3">
          <div>
            {title && <h3 className="font-bold text-slate-800">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {right}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}

export function Metric({ label, value, sub, tone = 'neutral' }: {
  label: string; value: React.ReactNode; sub?: React.ReactNode;
  tone?: 'neutral' | 'good' | 'warn' | 'bad';
}) {
  const toneCls = {
    neutral: 'text-slate-900', good: 'text-emerald-700',
    warn: 'text-amber-700', bad: 'text-red-700',
  }[tone];
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="text-[11px] font-bold uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-3xl font-black tabular-nums ${toneCls}`}>{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}
