import React, { useState } from 'react';
import { useOrcaStore } from '../../store/useOrcaStore';
import { User, Shield } from 'lucide-react';
import { supabase } from '../../api/supabase';

export const Profile: React.FC = () => {
  const user = useOrcaStore(state => state.user);
  const [role, setRole] = useState(user?.role || 'fisherman');
  const [name, setName] = useState(user?.name || '');
  const [age, setAge] = useState(user?.age || '');
  const [gender, setGender] = useState(user?.gender || '');
  const [boatType, setBoatType] = useState(user?.boatType || '');
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  const hasChanges = role !== user?.role || name !== user?.name || age !== user?.age || gender !== user?.gender || boatType !== user?.boatType;

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ text: '', type: '' });

    try {
      const { error } = await supabase.auth.updateUser({
        data: { role, name, age, gender, boat_type: boatType }
      });
      
      if (error) throw error;
      
      setMessage({ text: 'Profile updated successfully!', type: 'success' });
      await supabase.auth.refreshSession();
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to update profile', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="mx-auto max-w-2xl py-8">
      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-8 flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-sky-100 text-sky-600">
            <User className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Your Profile</h1>
            <p className="text-slate-500">{user.username}</p>
          </div>
        </div>

        {message.text && (
          <div className={`mb-6 rounded-lg p-4 text-sm ${
            message.type === 'error' 
              ? 'bg-red-50 text-red-700 border border-red-200' 
              : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
          }`}>
            {message.text}
          </div>
        )}

        <form onSubmit={handleUpdateProfile} className="space-y-6 max-w-md">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">
              Account Email
            </label>
            <input
              type="text"
              disabled
              value={user.username}
              className="w-full rounded-lg border border-slate-300 bg-slate-50 px-4 py-2.5 text-slate-500 cursor-not-allowed"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">
              Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="John Doe"
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Age
              </label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                placeholder="35"
                className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700">
                Gender
              </label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              >
                <option value="">Select...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
                <option value="prefer_not_to_say">Prefer not to say</option>
              </select>
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">
              Boat Type
            </label>
            <select
              value={boatType}
              onChange={(e) => setBoatType(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            >
              <option value="">Select a boat type...</option>
              <option value="canoe">Canoe / Kayak</option>
              <option value="skiff">Skiff</option>
              <option value="trawler">Trawler</option>
              <option value="frp">FRP (Fiberglass)</option>
              <option value="commercial">Commercial Vessel</option>
              <option value="research">Research Vessel</option>
              <option value="none">None</option>
            </select>
          </div>

          <div className="pt-4 border-t border-slate-100">
            <label className="mb-2 block text-sm font-medium text-slate-700 flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Assigned Role
            </label>
            <p className="mb-3 text-xs text-slate-500">
              Changing your role will instantly update the tabs and permissions you have access to.
            </p>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            >
              <option value="fisherman">Fisherman (Basic Access)</option>
              <option value="researcher">Researcher (Advanced Access)</option>
              <option value="admin">Administrator (Full Access)</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading || !hasChanges}
            className="rounded-lg bg-slate-900 px-6 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>
    </div>
  );
};
