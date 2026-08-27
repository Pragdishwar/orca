import React from 'react';
import { useOrcaStore } from '../../store/useOrcaStore';
import { Anchor, Bell, Shield, ShieldAlert, Activity, CheckCircle, Ship, Map, AlertTriangle, FileText, Database, Settings, DownloadCloud, ShieldCheck } from 'lucide-react';
import BoatRegistrationModal from '../modals/BoatRegistrationModal';

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { 
    activeBoat, language, pipelineStatus, guardDisagreement, 
    unreleasedAlertsCount, officialAdvisoryText, activeTab, 
    setLanguage, setActiveTab, setBoatModalOpen 
  } = useOrcaStore();

  const handleTabClick = (tab: any) => {
    setActiveTab(tab);
  };

  const tabs = [
    { id: 'platform', label: 'Platform', icon: <Anchor className="w-5 h-5" /> },
    { id: 'alerts', label: 'Alerts', icon: <Bell className="w-5 h-5" /> },
    { id: 'validation', label: 'Validation', icon: <ShieldAlert className="w-5 h-5" /> },
    { id: 'coverage', label: 'Coverage', icon: <Database className="w-5 h-5" /> },
    { id: 'offline_compile', label: 'Offline Compile', icon: <DownloadCloud className="w-5 h-5" /> },
    { id: 'trust', label: 'Trust & Threshold', icon: <ShieldCheck className="w-5 h-5" /> },
  ];

  return (
    <div className="flex flex-col min-h-screen bg-gray-50 text-gray-900">
      {/* Header */}
      <header className="bg-slate-900 text-white p-4 flex items-center justify-between shadow-md">
        <div className="flex items-center space-x-4">
          <div className="font-bold text-xl tracking-tight flex items-center">
            <Anchor className="w-6 h-6 mr-2 text-blue-400" />
            ORCA <span className="text-gray-400 mx-2 text-sm font-normal">· PS26176 · DarkWave</span>
          </div>
          
          <button 
            onClick={() => setBoatModalOpen(true)}
            className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-full text-sm border border-slate-700 transition-colors"
          >
            <Ship className="w-4 h-4 text-gray-300" />
            <span>{activeBoat ? activeBoat.hullClass : 'Select Boat'}</span>
          </button>
        </div>

        <div className="flex items-center space-x-6">
          <select 
            value={language}
            onChange={(e) => setLanguage(e.target.value as any)}
            className="bg-slate-800 text-white text-sm rounded-md px-2 py-1 border border-slate-700 outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="en">English</option>
            <option value="ml">മലയാളം (Malayalam)</option>
            <option value="ta">தமிழ் (Tamil)</option>
          </select>

          {/* Pipeline Health */}
          <div className="flex items-center space-x-1">
            <Activity className="w-4 h-4 text-gray-400" />
            {pipelineStatus.stalenessHours < 6 ? (
              <span className="bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full text-xs font-medium border border-emerald-500/30">Fresh</span>
            ) : pipelineStatus.stalenessHours > 24 ? (
              <span className="bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full text-xs font-medium border border-red-500/30">Stale &gt;24h</span>
            ) : (
              <span className="bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full text-xs font-medium border border-amber-500/30">Delayed</span>
            )}
          </div>

          {/* Guard Status */}
          <div className="flex items-center space-x-1">
            <Shield className="w-4 h-4 text-gray-400" />
            {!guardDisagreement ? (
              <span className="bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full text-xs font-medium border border-emerald-500/30">Guard Active</span>
            ) : (
              <span className="bg-red-500/20 text-red-400 px-2 py-0.5 rounded-full text-xs font-medium border border-red-500/30">Guard Intervened</span>
            )}
          </div>

          {/* Alerts Notification */}
          <div className="relative">
            <Bell className={`w-5 h-5 ${unreleasedAlertsCount > 0 ? 'text-amber-400' : 'text-gray-400'}`} />
            {unreleasedAlertsCount > 0 && (
              <span className="absolute -top-2 -right-2 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                {unreleasedAlertsCount}
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Official Advisory Pinned Banner */}
      <div className={`p-3 text-sm font-medium flex items-center justify-center border-b shadow-sm ${
        guardDisagreement ? 'bg-amber-100 text-amber-900 border-amber-300' : 'bg-blue-50 text-blue-900 border-blue-200'
      }`}>
        <AlertTriangle className={`w-4 h-4 mr-2 ${guardDisagreement ? 'text-amber-600' : 'text-blue-600'}`} />
        <span>{officialAdvisoryText}</span>
        {guardDisagreement && (
          <span className="ml-2 font-bold">(Local ORCA verdict conflicts with INCOIS)</span>
        )}
      </div>

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto p-6 pb-24">
        {children}
      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 w-full bg-white border-t shadow-[0_-2px_10px_rgba(0,0,0,0.05)] px-4 py-2 flex justify-between items-center z-40">
        <div className="max-w-4xl mx-auto w-full flex justify-between">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              className={`flex flex-col items-center p-2 rounded-lg transition-colors ${
                activeTab === tab.id ? 'text-blue-600 bg-blue-50' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              {tab.icon}
              <span className="text-[10px] font-medium mt-1">{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* Modals */}
      <BoatRegistrationModal />
    </div>
  );
};
