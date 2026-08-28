import React, { useState } from 'react';
import { useOrcaStore } from '../../store/useOrcaStore';
import { Anchor, LogIn } from 'lucide-react';
import { API_URL } from '../../api/client';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [role, setRole] = useState('fisherman');
  
  // Extra profile fields for Sign Up
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [boatType, setBoatType] = useState('');

  const [loading, setLoading] = useState(false);
  
  const login = useOrcaStore(state => state.login);

  const [isSignUp, setIsSignUp] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const { supabase } = await import('../../api/supabase');
      let authError;
      
      if (isSignUp) {
        const { error } = await supabase.auth.signUp({
          email: username,
          password,
          options: {
            data: { role, name, age, gender, boat_type: boatType },
          },
        });
        authError = error;
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email: username,
          password,
        });
        authError = error;
        
        if (!error) {
          // Update the user's role metadata to match their selection
          await supabase.auth.updateUser({
            data: { role }
          });
        }
      }
      
      if (authError) {
        throw new Error(authError.message);
      }
      
      // State update is handled automatically by onAuthStateChange in the store
    } catch (err: any) {
      setError(err.message || (isSignUp ? 'Sign up failed' : 'Login failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-lg">
        <div className="mb-8 flex flex-col items-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-slate-900 shadow-md">
            <Anchor className="h-8 w-8 text-sky-400" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            {isSignUp ? 'Create an ORCA account' : 'Sign in to ORCA'}
          </h1>
          <p className="mt-2 text-sm text-slate-500">Advisory Platform PS26176</p>
        </div>
        
        {error && (
          <div className="mb-6 rounded-lg bg-red-50 p-4 text-sm text-red-700 border border-red-200">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="username">
              Email
            </label>
            <input
              id="username"
              type="email"
              required
              className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              placeholder="Enter your email"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {isSignUp && (
            <>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">Full Name</label>
                <input
                  type="text"
                  required
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">Age</label>
                  <input
                    type="number"
                    className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 placeholder-slate-400 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                    placeholder="35"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-700">Gender</label>
                  <select
                    className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 bg-white focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
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
                <label className="mb-2 block text-sm font-medium text-slate-700">Boat Type</label>
                <select
                  className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 bg-white focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                  value={boatType}
                  onChange={(e) => setBoatType(e.target.value)}
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
            </>
          )}
          
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700" htmlFor="role">
              {isSignUp ? 'I am a...' : 'Sign in as'}
            </label>
            <select
              id="role"
              className="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 bg-white focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option value="fisherman">Fisherman</option>
              <option value="researcher">Researcher</option>
              <option value="admin">Administrator</option>
            </select>
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 disabled:opacity-70 transition-colors"
          >
            {loading ? (isSignUp ? 'Signing up...' : 'Signing in...') : (
              <>
                <LogIn className="h-4 w-4" />
                {isSignUp ? 'Sign Up' : 'Sign In'}
              </>
            )}
          </button>
        </form>
        
        <div className="mt-6 text-center text-sm text-slate-600">
          {isSignUp ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError('');
            }}
            className="font-medium text-sky-600 hover:text-sky-500 focus:outline-none focus:underline"
          >
            {isSignUp ? 'Sign in instead' : 'Sign up now'}
          </button>
        </div>
      </div>
    </div>
  );
};
