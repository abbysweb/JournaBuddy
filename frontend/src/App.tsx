import { useState } from 'react';
import { UploadSection } from './components/UploadSection';
import { LiveAgentTracker } from './components/LiveAgentTracker';
import { Dashboard } from './components/Dashboard';
import { FileSearch } from 'lucide-react';

function App() {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [dashboardPayload, setDashboardPayload] = useState<any>(null);

  const handleUploadSuccess = (newTaskId: string) => {
    setTaskId(newTaskId);
    setDashboardPayload(null);
  };

  const handleAnalysisComplete = (payload: any) => {
    setDashboardPayload(payload);
  };

  const reset = () => {
    setTaskId(null);
    setDashboardPayload(null);
  };

  return (
    <div className="app-container">
      <header className="header animate-fade-in">
        <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(255,255,255,0.05)', padding: '16px', borderRadius: '50%', marginBottom: '24px' }}>
          <FileSearch size={48} color="var(--accent-primary)" />
        </div>
        <h1><span className="text-gradient">JournaBuddy</span> Intelligence</h1>
        <p>AI-powered manuscript optimization and journal matching</p>
      </header>

      <main>
        {!taskId && (
          <div className="animate-fade-in">
            <UploadSection onUploadSuccess={handleUploadSuccess} />
          </div>
        )}

        {taskId && !dashboardPayload && (
          <LiveAgentTracker taskId={taskId} onComplete={handleAnalysisComplete} />
        )}

        {dashboardPayload && (
          <div className="animate-fade-in">
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '24px' }}>
              <button className="glass-button" onClick={reset}>
                Analyze Another Paper
              </button>
            </div>
            <Dashboard payload={dashboardPayload} taskId={taskId} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
