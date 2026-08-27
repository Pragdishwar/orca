import React, { useEffect, useState } from 'react';
import { Check, Lock, Trash2, X } from 'lucide-react';
import { api, Boat } from '../../api/client';
import { useOrcaStore } from '../../store/useOrcaStore';

const HULL_CLASSES = [
  { value: 'PLYWOOD_CANOE', label: 'Plywood canoe' },
  { value: 'FRP_SMALL', label: 'Small FRP' },
  { value: 'TRAWLER_MED', label: 'Mechanised trawler' },
  { value: 'TRAWLER_DEEP', label: 'Deep-sea trawler' },
];

/** Length decides the threshold bucket when the skipper does not pick a class. */
function bucketFor(lengthM: number): string {
  if (lengthM < 7) return 'PLYWOOD_CANOE';
  if (lengthM < 11) return 'FRP_SMALL';
  if (lengthM < 18) return 'TRAWLER_MED';
  return 'TRAWLER_DEEP';
}

const emptyForm = {
  boat_id: '', hull_class: 'FRP_SMALL', length_m: 9, engine_hp: 25,
  crew: 4, home_harbour: 'Muthalapozhi',
};

export default function BoatRegistrationModal() {
  const {
    isBoatModalOpen, setBoatModalOpen, boats, activeBoat, setActiveBoat, refreshBoats,
  } = useOrcaStore();
  const [form, setForm] = useState(emptyForm);
  const [grounds, setGrounds] = useState<{ ground_id: string; local_name: string }[]>([]);
  const [selectedGrounds, setSelectedGrounds] = useState<string[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [banner, setBanner] = useState<string | null>(null);

  useEffect(() => {
    if (isBoatModalOpen && grounds.length === 0) {
      api.grounds().then((d) => setGrounds(d.grounds)).catch(() => setGrounds([]));
    }
  }, [isBoatModalOpen, grounds.length]);

  if (!isBoatModalOpen) return null;

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.boat_id.trim()) e.boat_id = 'A registration number is required.';
    else if (boats.some((b) => b.boat_id === form.boat_id.trim()))
      e.boat_id = 'That registration is already on file.';
    if (!(form.length_m > 0)) e.length_m = 'Length must be greater than zero.';
    if (!(form.engine_hp >= 0)) e.engine_hp = 'Engine power cannot be negative.';
    if (!(form.crew > 0)) e.crew = 'At least one crew member.';
    if (!form.home_harbour.trim()) e.home_harbour = 'Home harbour is required.';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const submit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    if (!validate()) return;
    setBusy(true);
    setBanner(null);
    try {
      const payload: Boat = {
        boat_id: form.boat_id.trim(),
        hull_class: form.hull_class,
        length_m: Number(form.length_m),
        engine_hp: Number(form.engine_hp),
        crew: Number(form.crew),
        home_harbour: form.home_harbour.trim(),
        threshold_bucket: form.hull_class,
      };
      const created = await api.createBoat(payload);
      await refreshBoats();
      setActiveBoat(created);
      setForm(emptyForm);
      setSelectedGrounds([]);
      setBanner(`Registered ${created.boat_id}. Threshold bucket: ${created.threshold_bucket}.`);
    } catch (e) {
      setErrors({ form: e instanceof Error ? e.message : 'Could not save the boat.' });
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id: string) => {
    try {
      await api.deleteBoat(id);
      await refreshBoats();
    } catch { /* list keeps its previous state */ }
  };

  const field = 'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none '
    + 'focus:ring-2 focus:ring-sky-500';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog" aria-modal="true" aria-label="Boat registration">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-xl bg-white
        shadow-2xl">
        <header className="sticky top-0 flex items-center justify-between bg-slate-900
          px-5 py-3 text-white">
          <h2 className="text-lg font-bold">Boat registry</h2>
          <button onClick={() => setBoatModalOpen(false)} aria-label="Close"
            className="rounded p-1 text-slate-400 hover:bg-slate-800 hover:text-white">
            <X className="h-5 w-5" aria-hidden />
          </button>
        </header>

        <div className="grid gap-5 p-5 md:grid-cols-2">
          <section>
            <h3 className="mb-2 text-sm font-bold text-slate-800">Registered boats</h3>
            {boats.length === 0 && (
              <p className="text-sm text-slate-500">None yet. Register one on the right.</p>
            )}
            <ul className="space-y-1.5">
              {boats.map((b) => (
                <li key={b.boat_id}
                  className={`flex items-center gap-2 rounded-lg border p-2.5 ${
                    activeBoat?.boat_id === b.boat_id
                      ? 'border-sky-400 bg-sky-50' : 'border-slate-200'}`}>
                  <button onClick={() => setActiveBoat(b)} className="flex-1 text-left">
                    <div className="text-sm font-bold text-slate-800">{b.boat_id}</div>
                    <div className="text-xs text-slate-500">
                      {b.hull_class.replace(/_/g, ' ')} · {b.length_m} m · {b.crew} crew
                    </div>
                  </button>
                  {activeBoat?.boat_id === b.boat_id && (
                    <Check className="h-4 w-4 text-sky-600" aria-hidden />
                  )}
                  <button onClick={() => remove(b.boat_id)}
                    aria-label={`Delete ${b.boat_id}`}
                    className="rounded p-1.5 text-slate-400 hover:bg-red-50
                      hover:text-red-600">
                    <Trash2 className="h-4 w-4" aria-hidden />
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <form onSubmit={submit} className="space-y-3">
            <h3 className="text-sm font-bold text-slate-800">Register a boat</h3>

            {banner && (
              <p className="rounded border border-emerald-300 bg-emerald-50 p-2 text-xs
                text-emerald-900">{banner}</p>
            )}
            {errors.form && (
              <p className="rounded border border-red-300 bg-red-50 p-2 text-xs
                text-red-900">{errors.form}</p>
            )}

            <Field label="Registration number" error={errors.boat_id}>
              <input className={field} value={form.boat_id} placeholder="KL-05-1234"
                onChange={(e) => setForm({ ...form, boat_id: e.target.value })} />
            </Field>

            <Field label="Hull class">
              <select className={field} value={form.hull_class}
                onChange={(e) => setForm({ ...form, hull_class: e.target.value })}>
                {HULL_CLASSES.map((h) => (
                  <option key={h.value} value={h.value}>{h.label}</option>
                ))}
              </select>
            </Field>

            <div className="grid grid-cols-3 gap-2">
              <Field label="Length (m)" error={errors.length_m}>
                <input className={field} type="number" step="0.1" value={form.length_m}
                  onChange={(e) => {
                    const length_m = parseFloat(e.target.value);
                    setForm({ ...form, length_m, hull_class: bucketFor(length_m) });
                  }} />
              </Field>
              <Field label="Engine (hp)" error={errors.engine_hp}>
                <input className={field} type="number" value={form.engine_hp}
                  onChange={(e) => setForm({ ...form, engine_hp: +e.target.value })} />
              </Field>
              <Field label="Crew" error={errors.crew}>
                <input className={field} type="number" value={form.crew}
                  onChange={(e) => setForm({ ...form, crew: +e.target.value })} />
              </Field>
            </div>

            <Field label="Home harbour" error={errors.home_harbour}>
              <input className={field} value={form.home_harbour}
                onChange={(e) => setForm({ ...form, home_harbour: e.target.value })} />
            </Field>

            <div>
              <span className="text-xs font-bold uppercase text-slate-500">
                Usual grounds
              </span>
              <p className="mb-1.5 mt-0.5 flex items-start gap-1 text-[11px] text-slate-500">
                <Lock className="mt-0.5 h-3 w-3 shrink-0 text-emerald-600" aria-hidden />
                Names only. No coordinate is ever stored against a boat (R-6).
              </p>
              <div className="flex flex-wrap gap-1.5">
                {grounds.map((g) => {
                  const on = selectedGrounds.includes(g.ground_id);
                  return (
                    <button
                      key={g.ground_id}
                      type="button"
                      onClick={() => setSelectedGrounds(on
                        ? selectedGrounds.filter((x) => x !== g.ground_id)
                        : [...selectedGrounds, g.ground_id])}
                      className={`rounded-full border px-2.5 py-1 text-xs font-medium
                        ${on ? 'border-sky-300 bg-sky-50 text-sky-800'
                          : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'}`}
                    >
                      {on && <Check className="mr-1 inline h-3 w-3" aria-hidden />}
                      {g.local_name}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t border-slate-200 pt-3">
              <button type="button" onClick={() => setBoatModalOpen(false)}
                className="rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium
                  text-slate-700 hover:bg-slate-200">
                Close
              </button>
              <button type="submit" disabled={busy}
                className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-bold text-white
                  hover:bg-sky-700 disabled:bg-slate-300">
                {busy ? 'Saving…' : 'Save profile'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function Field({ label, error, children }: {
  label: string; error?: string; children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="text-xs font-bold uppercase text-slate-500">{label}</span>
      <div className="mt-1">{children}</div>
      {error && <span className="mt-0.5 block text-[11px] text-red-600">{error}</span>}
    </label>
  );
}
