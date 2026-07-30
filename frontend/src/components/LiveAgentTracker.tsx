import React, { useEffect, useState } from 'react';
import { Activity, Brain, Server, CheckCircle2, Zap } from 'lucide-react';

interface LiveAgentTrackerProps {
  taskId: string;
  onComplete: (dashboardPayload: any) => void;
}

export const LiveAgentTracker: React.FC<LiveAgentTrackerProps> = ({ taskId, onComplete }) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('initializing');
  const [logs, setLogs] = useState<string[]>([]);
  
  const statusRef = React.useRef(status);
  const progressRef = React.useRef(progress);

  useEffect(() => {
    const eventSource = new EventSource(`http://localhost:8000/api/stream/${taskId}`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.error) {
          setLogs(prev => [...prev, `[ERROR] ${data.error}`]);
          eventSource.close();
          return;
        }

        if (data.progress_percent !== progressRef.current) {
          setProgress(data.progress_percent);
          progressRef.current = data.progress_percent;
          // Only log significant progress jumps to avoid spamming
          if (data.progress_percent % 10 === 0 || data.progress_percent === 100) {
             setLogs(prev => [...prev, `[SYSTEM] Processing... ${data.progress_percent}% complete.`]);
          }
        }
        
        if (data.status !== statusRef.current) {
          setStatus(data.status);
          statusRef.current = data.status;
          setLogs(prev => [...prev, `[SYSTEM] Pipeline status changed to: ${data.status.toUpperCase()}`]);
        }

        if (data.status === 'completed') {
          setLogs(prev => [...prev, '[SYSTEM] Analysis completed successfully. Generating dashboard...']);
          eventSource.close();
          setTimeout(() => {
            onComplete(data.dashboard_payload);
          }, 1500); 
        } else if (data.status === 'failed') {
          setLogs(prev => [...prev, '[ERROR] Analysis failed! Check backend logs.']);
          eventSource.close();
        }

      } catch (err) {
        console.error("Error parsing SSE data", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      setLogs(prev => [...prev, `[NETWORK] Connection lost. Reconnecting...`]);
    };

    return () => {
      eventSource.close();
    };
  }, [taskId]);

  // Derive active agents based on status
  const agents = [
    { name: 'Semantic Chunker', icon: <Server size={18} />, active: status === 'processing', done: ['agents_running', 'completed'].includes(status) },
    { name: 'Ollama Intelligence', icon: <Brain size={18} />, active: status === 'agents_running', done: status === 'completed' },
    { name: 'pgvector Matching', icon: <Zap size={18} />, active: status === 'agents_running', done: status === 'completed' }
  ];

  return (
    <div className="glass-panel animate-fade-in" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <Activity color="var(--accent-primary)" />
        <h2 style={{ margin: 0 }}>Live Analysis Tracker</h2>
      </div>

      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontWeight: 500, color: 'var(--text-secondary)' }}>Overall Progress</span>
          <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{progress}%</span>
        </div>
        <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
          <div 
            style={{ 
              height: '100%', 
              width: `${progress}%`, 
              background: 'linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))',
              transition: 'width 0.5s ease-out'
            }} 
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        {agents.map((agent, idx) => (
          <div 
            key={idx} 
            style={{
              padding: '16px',
              background: agent.active ? 'rgba(59, 130, 246, 0.1)' : 'rgba(0,0,0,0.2)',
              border: `1px solid ${agent.active ? 'var(--accent-primary)' : 'var(--glass-border)'}`,
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              opacity: (agent.active || agent.done) ? 1 : 0.5,
              transition: 'all 0.3s ease'
            }}
          >
            <div style={{ color: agent.done ? 'var(--success)' : agent.active ? 'var(--accent-primary)' : 'var(--text-secondary)' }}>
              {agent.done ? <CheckCircle2 size={18} /> : agent.icon}
            </div>
            <span style={{ fontWeight: 500, fontSize: '0.9rem' }}>{agent.name}</span>
            {agent.active && (
              <span style={{ marginLeft: 'auto', width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-primary)', animation: 'pulse 1s infinite' }} />
            )}
          </div>
        ))}
      </div>

      <div style={{ background: '#000', borderRadius: '8px', padding: '16px', fontFamily: 'monospace', fontSize: '0.85rem', color: '#4ade80', height: '200px', overflowY: 'auto' }}>
        <div style={{ marginBottom: '8px', color: '#888' }}>$ tail -f /var/log/journabuddy/agents.log</div>
        {logs.map((log, idx) => (
          <div key={idx} style={{ marginBottom: '4px', opacity: 0.9 }}>
            <span style={{ color: '#888' }}>{new Date().toLocaleTimeString()}</span> {log}
          </div>
        ))}
        {status !== 'completed' && status !== 'failed' && (
          <div style={{ animation: 'blink 1s infinite' }}>_</div>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }
        @keyframes blink { 0% { opacity: 0; } 50% { opacity: 1; } 100% { opacity: 0; } }
      `}</style>
    </div>
  );
};
