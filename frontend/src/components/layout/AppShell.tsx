import React, { useEffect } from 'react';
import {
  Anchor, Bell, Database, DownloadCloud, Radio, Server, Shield, ShieldAlert,
  ShieldCheck, Ship, TriangleAlert, LogOut, User as UserIcon
} from 'lucide-react';
import { useOrcaStore, TabId } from '../../store/useOrcaStore';
import BoatRegistrationModal from '../modals/BoatRegistrationModal';
import { ProvenanceBadge } from '../ui/Primitives';

export const TABS: { id: TabId; label: string; Icon: React.ElementType; roles: string[] }[] = [
  { id: 'platform', label: 'Platform', Icon: Anchor, roles: ['admin', 'fisherman', 'disaster_mgmt', 'coast_guard', 'policy_maker', 'researcher'] },
  { id: 'alerts', label: 'Alerts', Icon: Bell, roles: ['admin', 'fisherman', 'disaster_mgmt', 'coast_guard', 'policy_maker', 'researcher'] },
  { id: 'validation', label: 'Validation', Icon: ShieldAlert, roles: ['admin', 'disaster_mgmt', 'coast_guard', 'policy_maker', 'researcher'] },
  { id: 'offline_compile', label: 'Offline Compile', Icon: DownloadCloud, roles: ['admin', 'fisherman', 'disaster_mgmt', 'coast_guard', 'policy_maker', 'researcher'] },
  { id: 'trust', label: 'Trust & Threshold', Icon: ShieldCheck, roles: ['admin', 'disaster_mgmt', 'policy_maker', 'researcher'] },
  { id: 'profile', label: 'Profile', Icon: UserIcon, roles: ['admin', 'fisherman', 'disaster_mgmt', 'coast_guard', 'policy_maker', 'researcher'] },
];

/** Pipeline chip: fresh / stale / halted / failed, per R-2 bands. */
function PipelineChip() {
  const { health, healthError } = useOrcaStore();
  if (healthError || !health) {
    return (
      <Chip tone="bad" Icon={Server}>
        {healthError ? 'Pipeline unreachable' : 'Pipeline…'}
      </Chip>
    );
  }
  const { pipeline_status: st, staleness_hours: h, primary_source } = health;
  const tone = st === 'active' ? 'good' : st === 'stale' ? 'warn' : 'bad';
  const label = st === 'active' ? `Fresh · ${h.toFixed(1)} h`
    : st === 'stale' ? `Stale · ${h.toFixed(1)} h`
      : st === 'halted' ? 'Halted · >24 h' : 'No source';
  return (
    <Chip tone={tone} Icon={Server} title={`Primary source: ${primary_source ?? 'none'}`}>
      {label}
    </Chip>
  );
}

function GuardChip() {
  const active = useOrcaStore((s) => s.active);
  if (!active) return <Chip tone="neutral" Icon={Shield}>Guard N/A</Chip>;
  const pass = active.guard.result === 'PASS';
  return (
    <Chip tone={pass ? 'good' : 'bad'} Icon={Shield} title={active.guard.reason}>
      Guard {active.guard.result}
    </Chip>
  );
}

function Chip({ tone, Icon, children, title, onClick }: {
  tone: 'good' | 'warn' | 'bad' | 'neutral';
  Icon: React.ElementType; children: React.ReactNode;
  title?: string; onClick?: () => void;
}) {
  const cls = {
    good: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
    warn: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
    bad: 'bg-red-500/15 text-red-300 border-red-500/40',
    neutral: 'bg-slate-500/15 text-slate-300 border-slate-500/40',
  }[tone];
  const Tag = onClick ? 'button' : 'div';
  return (
    <Tag
      title={title}
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1
        text-xs font-semibold ${cls} ${onClick ? 'hover:brightness-125' : ''}`}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden />
      {children}
    </Tag>
  );
}

/** FR-19: the official bulletin is visible from every tab. */
function AdvisoryStrip() {
  const active = useOrcaStore((s) => s.active);
  const official = active?.official_advisory;
  const disagree = active?.disagreement ?? false;

  if (!official) {
    return (
      <div className="flex items-center justify-center gap-2 border-b border-slate-200
        bg-slate-50 px-4 py-2 text-xs text-slate-500">
        <Radio className="h-3.5 w-3.5" aria-hidden />
        Official advisory loads with your first question.
      </div>
    );
  }

  return (
    <div className={`border-b px-4 py-2.5 text-sm ${disagree
      ? 'border-amber-300 bg-amber-50 text-amber-950'
      : 'border-slate-200 bg-slate-50 text-slate-700'}`}>
      <div className="mx-auto flex max-w-[1800px] flex-wrap items-center gap-x-3 gap-y-1">
        <span className="inline-flex items-center gap-1.5 font-bold">
          <Radio className="h-4 w-4" aria-hidden /> {official.issuer}
        </span>
        <span className="flex-1 min-w-[16rem]">{official.text_en}</span>
        <ProvenanceBadge value={official.provenance} />
        {disagree && (
          <span className="inline-flex items-center gap-1.5 rounded-full border
            border-amber-400 bg-amber-100 px-2.5 py-1 text-xs font-bold text-amber-900">
            <TriangleAlert className="h-3.5 w-3.5" aria-hidden />
            ORCA disagrees — both shown
          </span>
        )}
      </div>
    </div>
  );
}

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const {
    activeBoat, activeTab, language, alertSummary, boot, refreshHealth,
    setActiveTab, setBoatModalOpen, bootError, user, logout
  } = useOrcaStore();

  useEffect(() => {
    boot();
    const id = setInterval(refreshHealth, 30_000);
    return () => clearInterval(id);
  }, [boot, refreshHealth]);

  const unreleased = alertSummary.pending_release ?? 0;

  return (
    <div className="flex min-h-screen flex-col bg-slate-100 text-slate-900">
      <header className="flex flex-wrap items-center justify-between gap-3 bg-slate-900
        px-4 py-3 text-white shadow-md">
        <div className="flex items-center gap-3">
          <span className="flex items-center text-lg font-bold tracking-tight">
            <Anchor className="mr-2 h-5 w-5 text-sky-400" aria-hidden />
            ORCA
            <span className="ml-2 text-xs font-normal text-slate-400">
              · PS26176 · DarkWave
            </span>
          </span>

          <button
            onClick={() => setBoatModalOpen(true)}
            className="flex items-center gap-2 rounded-full border border-slate-700
              bg-slate-800 px-3 py-1.5 text-sm hover:bg-slate-700"
          >
            <Ship className="h-4 w-4 text-slate-300" aria-hidden />
            {activeBoat
              ? `${activeBoat.boat_id} · ${activeBoat.hull_class.replace(/_/g, ' ')}`
              : 'Register a boat'}
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded border border-slate-700 bg-slate-800 px-2 py-1
            text-xs font-semibold uppercase text-slate-300"
            title="Detected from the last query">
            {language}
          </span>
          <PipelineChip />
          <GuardChip />
          <Chip
            tone={unreleased > 0 ? 'warn' : 'neutral'}
            Icon={Bell}
            onClick={() => setActiveTab('alerts')}
            title="Alerts awaiting release"
          >
            {unreleased > 0 ? `${unreleased} pending` : 'No alerts'}
          </Chip>
          
          <div className="ml-2 flex items-center gap-2 border-l border-slate-700 pl-4">
            <span className="text-xs font-semibold text-slate-300">
              {user?.username} ({user?.role})
            </span>
            <button
              onClick={logout}
              className="flex items-center gap-1 rounded-full p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>

      <AdvisoryStrip />

      {bootError && (
        <div className="border-b border-red-300 bg-red-50 px-4 py-2 text-sm text-red-900">
          <strong>Backend unreachable.</strong> {bootError} Panels below will show their
          own error states until it responds.
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        <nav
          aria-label="Desktop Main"
          className="hidden md:flex w-64 flex-col border-r border-slate-200 bg-white p-4 overflow-y-auto shrink-0"
        >
          <div className="flex flex-col gap-2">
            {TABS.filter(tab => tab.roles.includes(user?.role || '')).map(({ id, label, Icon }) => {
              const on = activeTab === id;
              return (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  aria-current={on ? 'page' : undefined}
                  className={`relative flex items-center gap-3 rounded-lg px-3 py-2.5
                    transition-colors ${on
                      ? 'bg-sky-50 text-sky-700 font-medium'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}
                >
                  <Icon className="h-5 w-5" aria-hidden />
                  <span className="text-sm">{label}</span>
                  {id === 'alerts' && unreleased > 0 && (
                    <span className="ml-auto rounded-full bg-red-600 px-2 py-0.5
                      text-xs font-bold text-white">
                      {unreleased}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </nav>

        <main className="flex-1 overflow-auto p-4 pb-24 md:pb-4">
          <div className="mx-auto w-full max-w-[1800px]">
            {children}
          </div>
        </main>
      </div>

      <nav
        aria-label="Mobile Main"
        className="fixed bottom-0 z-40 w-full border-t border-slate-200 bg-white
          px-2 py-1.5 shadow-[0_-2px_10px_rgba(0,0,0,0.06)] md:hidden"
      >
        <div className="mx-auto flex justify-between">
          {TABS.filter(tab => tab.roles.includes(user?.role || '')).map(({ id, label, Icon }) => {
            const on = activeTab === id;
            return (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                aria-current={on ? 'page' : undefined}
                className={`relative flex flex-1 flex-col items-center rounded-lg px-2 py-1.5
                  transition-colors ${on
                    ? 'bg-sky-50 text-sky-700'
                    : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900'}`}
              >
                <Icon className="h-5 w-5" aria-hidden />
                <span className="mt-0.5 text-[10px] font-semibold truncate w-full text-center">{label}</span>
                {id === 'alerts' && unreleased > 0 && (
                  <span className="absolute right-2 top-0 rounded-full bg-red-600 px-1.5
                    text-[10px] font-bold text-white">
                    {unreleased}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </nav>

      <BoatRegistrationModal />
    </div>
  );
};
