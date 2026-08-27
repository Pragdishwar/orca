import { AppShell } from './components/layout/AppShell';
import PlatformTab from './pages/PlatformTab';
import { useOrcaStore } from './store/useOrcaStore';

function App() {
  const activeTab = useOrcaStore(state => state.activeTab);

  return (
    <AppShell>
      {activeTab === 'platform' && <PlatformTab />}
      {activeTab !== 'platform' && (
        <div className="flex items-center justify-center h-full text-gray-500 font-medium">
          {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} view is under construction.
        </div>
      )}
    </AppShell>
  );
}

export default App;
