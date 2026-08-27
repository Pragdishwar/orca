import React, { useEffect, useState } from 'react';
import {
  Check, Copy, Maximize2, Monitor, Printer, Radio, Smartphone,
} from 'lucide-react';
import { api, BroadcastBundle } from '../api/client';
import { useOrcaStore } from '../store/useOrcaStore';
import {
  EmptyState, ErrorState, Panel, Spinner, VerdictBadge,
} from '../components/ui/Primitives';

const TIERS = [
  { tier: 0, device: 'Landing-centre board', channel: 'Printed / screen at the harbour' },
  { tier: 1, device: 'Any mobile handset', channel: 'SMS' },
  { tier: 2, device: 'VHF set aboard', channel: 'Voice bulletin' },
  { tier: 3, device: 'No device at all', channel: 'Printed slip carried aboard' },
];

export default function OfflineCompileTab() {
  const active = useOrcaStore((s) => s.active);
  const [data, setData] = useState<BroadcastBundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);

  const load = () => {
    if (!active?.advisory_id) return;
    setLoading(true);
    setError(null);
    api.advisoryBroadcast(active.advisory_id)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };
  useEffect(load, [active?.advisory_id]);

  if (!active) {
    return (
      <EmptyState
        title="No active advisory"
        hint="Ask a question on the Platform tab, then come back to see it compiled."
      />
    );
  }
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (loading || !data) return <Spinner label="Rendering broadcast formats…" />;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(data.sms.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch { /* clipboard may be blocked; the text is on screen regardless */ }
  };

  if (fullscreen) {
    return (
      <div className="fixed inset-0 z-50 flex flex-col bg-black p-8 text-white">
        <button
          onClick={() => setFullscreen(false)}
          className="absolute right-6 top-6 rounded border border-slate-600 px-3 py-1
            text-sm text-slate-300 hover:bg-slate-800"
        >
          Close
        </button>
        <h1 className="text-center text-6xl font-black uppercase tracking-widest
          text-red-500">
          {data.board.headline}
        </h1>
        <p className="mt-2 text-center text-2xl text-slate-400">
          {data.board.inlet} · {data.board.date}
        </p>
        <div className="mt-8 grid flex-1 grid-cols-2 gap-6 lg:grid-cols-4">
          {data.board.buckets.map((b) => (
            <div key={b.hull_label}
              className="flex flex-col items-center justify-center rounded-xl border-4
                border-slate-700 p-6 text-center">
              <span className="text-3xl font-bold">{b.hull_label}</span>
              <span className={`mt-4 text-4xl font-black uppercase ${
                b.verdict === 'DO_NOT_CROSS' ? 'text-red-500'
                  : b.verdict === 'MARGINAL' ? 'text-amber-400' : 'text-emerald-400'}`}>
                {b.short}
              </span>
            </div>
          ))}
        </div>
        <p className="mt-6 text-center text-xl text-slate-500">{data.board.footer}</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Offline compile</h2>
          <p className="text-sm text-slate-500">
            One advisory, four formats that reach a boat with no phone and no network.
          </p>
        </div>
        <VerdictBadge verdict={active.verdict} />
      </div>

      <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm
        text-amber-900">
        {data.notice}
      </div>

      <Panel title="Delivery tiers" subtitle="What reaches whom, by the device they have">
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {TIERS.map((t) => (
            <div key={t.tier} className="rounded-lg border border-slate-200 p-3">
              <div className="text-[10px] font-bold uppercase text-slate-400">
                Tier {t.tier}
              </div>
              <div className="mt-1 text-sm font-semibold text-slate-800">{t.device}</div>
              <div className="text-xs text-slate-500">{t.channel}</div>
            </div>
          ))}
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel
          title="SMS"
          right={
            <span className={`rounded px-2 py-1 font-mono text-xs font-bold ${
              data.sms.over_limit
                ? 'bg-red-100 text-red-800' : 'bg-slate-100 text-slate-600'}`}>
              {data.sms.char_count} / {data.sms.limit}
            </span>
          }
        >
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm
            leading-relaxed text-emerald-950">
            {data.sms.content}
          </div>
          {data.sms.over_limit && (
            <p className="mt-2 text-xs font-semibold text-red-700">
              Over 160 characters — this would split into two billed messages.
            </p>
          )}
          <button
            onClick={copy}
            className="mt-3 inline-flex items-center gap-1.5 rounded-lg border
              border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700
              hover:bg-slate-100"
          >
            {copied ? <Check className="h-3.5 w-3.5" aria-hidden />
              : <Copy className="h-3.5 w-3.5" aria-hidden />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </Panel>

        <Panel title="VHF bulletin"
          right={<Radio className="h-4 w-4 text-slate-400" aria-hidden />}>
          <pre className="max-h-52 overflow-y-auto whitespace-pre-wrap rounded-lg border
            border-slate-200 bg-slate-50 p-3 font-mono text-[11px] leading-relaxed
            text-slate-800">
{data.vhf.content}
          </pre>
          <p className="mt-2 text-xs text-slate-500">
            {data.vhf.audio_is_placeholder
              ? 'Audio is a placeholder tone, not speech — no text-to-speech is '
                + 'integrated. The script above is what a watchkeeper would read.'
              : 'Pre-rendered audio available.'}
          </p>
        </Panel>

        <Panel title="Printed slip"
          right={
            <button onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 rounded border border-slate-300
                px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100">
              <Printer className="h-3.5 w-3.5" aria-hidden /> Print
            </button>
          }>
          <pre className="mx-auto w-full max-w-xs whitespace-pre-wrap rounded border-2
            border-dashed border-slate-400 bg-white p-4 font-mono text-[11px]
            leading-relaxed text-slate-900">
{data.slip.content}
          </pre>
        </Panel>

        <Panel title="Landing-centre board"
          subtitle="Hull classes side by side"
          right={
            <button onClick={() => setFullscreen(true)}
              className="inline-flex items-center gap-1.5 rounded border border-slate-300
                px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-100">
              <Maximize2 className="h-3.5 w-3.5" aria-hidden /> Fullscreen
            </button>
          }>
          <div className="rounded-lg bg-black p-4 text-white">
            <div className="text-center text-2xl font-black uppercase tracking-widest
              text-red-500">
              {data.board.headline}
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {data.board.buckets.map((b) => (
                <div key={b.hull_label}
                  className="rounded border-2 border-slate-700 p-2 text-center">
                  <div className="text-sm font-bold">{b.hull_label}</div>
                  <div className={`mt-1 text-base font-black uppercase ${
                    b.verdict === 'DO_NOT_CROSS' ? 'text-red-500'
                      : b.verdict === 'MARGINAL' ? 'text-amber-400' : 'text-emerald-400'}`}>
                    {b.short}
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-3 text-center text-xs text-slate-400">{data.board.footer}</p>
          </div>
        </Panel>
      </div>

      <Panel title="Channel ownership and cost"
        subtitle="Who would run each channel, and what it costs">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[36rem] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="p-2.5">Channel</th>
                <th className="p-2.5">Owner</th>
                <th className="p-2.5">Licence</th>
                <th className="p-2.5 text-right">Cost / bulletin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {data.channels.map((c) => (
                <tr key={c.channel}>
                  <td className="p-2.5 font-medium text-slate-800">{c.channel}</td>
                  <td className="p-2.5 text-slate-600">{c.owner}</td>
                  <td className="p-2.5 text-xs text-slate-500">{c.licence_required}</td>
                  <td className="p-2.5 text-right font-mono tabular-nums">
                    {c.unit_cost_inr === 0 ? 'free' : `₹${c.unit_cost_inr.toFixed(2)}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-sm text-slate-600">
          Estimated monthly infrastructure for 10 landing centres:{' '}
          <strong>₹{data.monthly_infra_inr_10_centres.toLocaleString('en-IN')}</strong>
        </p>
      </Panel>
    </div>
  );
}
