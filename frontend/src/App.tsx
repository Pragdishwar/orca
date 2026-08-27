import { AppShell } from './components/layout/AppShell';
import PlatformTab from './pages/PlatformTab';
import AlertsTab from './pages/AlertsTab';
import ValidationTab from './pages/ValidationTab';
import CoverageTab from './pages/CoverageTab';
import OfflineCompileTab from './pages/OfflineCompileTab';
import TrustTab from './pages/TrustTab';
import { useOrcaStore } from './store/useOrcaStore';

function App() {
  const activeTab = useOrcaStore(state => state.activeTab);

  return (
    <AppShell>
      {activeTab === 'platform' && <PlatformTab />}
      {activeTab === 'alerts' && <AlertsTab />}
      {activeTab === 'validation' && <ValidationTab />}
      {activeTab === 'coverage' && <CoverageTab />}
      {activeTab === 'offline_compile' && <OfflineCompileTab />}
      {activeTab === 'trust' && <TrustTab />}
    </AppShell>
  );
}

export default App;
