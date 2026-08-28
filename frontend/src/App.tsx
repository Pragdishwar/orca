import { AppShell, TABS } from './components/layout/AppShell';
import PlatformTab from './pages/PlatformTab';
import AlertsTab from './pages/AlertsTab';
import ValidationTab from './pages/ValidationTab';
import OfflineCompileTab from './pages/OfflineCompileTab';
import TrustTab from './pages/TrustTab';
import { useOrcaStore } from './store/useOrcaStore';
import { Login } from './components/auth/Login';

function App() {
  const activeTab = useOrcaStore(state => state.activeTab);
  const user = useOrcaStore(state => state.user);

  if (!user) {
    return <Login />;
  }

  const activeTabData = TABS.find(t => t.id === activeTab);
  const isAllowed = activeTabData?.roles.includes(user.role);

  return (
    <AppShell>
      {!isAllowed ? (
        <div className="flex h-full flex-col items-center justify-center p-12 text-center">
          <div className="mb-4 rounded-full bg-slate-200 p-4">
            <span className="text-3xl">🔒</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900">Access Denied</h2>
          <p className="mt-2 text-slate-500">
            You do not have permission to view the {activeTabData?.label || 'requested'} page.
          </p>
        </div>
      ) : (
        <>
          {activeTab === 'platform' && <PlatformTab />}
          {activeTab === 'alerts' && <AlertsTab />}
          {activeTab === 'validation' && <ValidationTab />}
          {activeTab === 'offline_compile' && <OfflineCompileTab />}
          {activeTab === 'trust' && <TrustTab />}
        </>
      )}
    </AppShell>
  );
}

export default App;
