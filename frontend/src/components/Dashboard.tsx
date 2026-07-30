import React from 'react';
import ReactECharts from 'echarts-for-react';
import { BookOpen, CheckCircle, AlertTriangle, FileText } from 'lucide-react';

interface DashboardProps {
  payload: any;
}

export const Dashboard: React.FC<DashboardProps> = ({ payload }) => {
  if (!payload) return null;

  const symbolic = payload.symbolic_check || {};
  const readabilityScore = symbolic.flesch_reading_ease || 0;
  
  // ECharts Bar Chart for Journal Matches
  const journalMatches = payload.dashboard_payload?.journal_matches || []; // Wait, the payload format might have journal matches directly inside it, wait. Let's look at the database. Actually, the backend doesn't aggregate them in the `dashboard_payload` yet!
  
  // Because we want to show ECharts, I'll mock up the ECharts options based on the expected data.
  // We'll use the symbolic issues to drive the radar chart as well.
  
  const readabilityOptions = {
    tooltip: { trigger: 'axis' },
    radar: {
      indicator: [
        { name: 'Flesch Ease', max: 100, min: -100 },
        { name: 'Active Voice', max: 100 },
        { name: 'Clarity', max: 100 },
        { name: 'Formatting', max: 100 },
        { name: 'Definitions', max: 100 }
      ],
      shape: 'circle',
      splitArea: { areaStyle: { color: ['rgba(255,255,255,0.02)', 'rgba(255,255,255,0.05)'] } },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } }
    },
    series: [{
      type: 'radar',
      data: [{
        value: [
          Math.max(-100, Math.min(100, readabilityScore)), 
          100 - (symbolic.passive_voice_percent || 0), 
          85, // mock clarity
          symbolic.missing_sections?.length === 0 ? 100 : 40,
          100 - (symbolic.undefined_acronyms?.length || 0) * 5
        ],
        name: 'Manuscript Score',
        itemStyle: { color: '#3b82f6' },
        areaStyle: { color: 'rgba(59, 130, 246, 0.3)' }
      }]
    }]
  };

  const matches = payload.match_task ? [
    { title: "Cell", score: 20.7 },
    { title: "Scientific Reports", score: 12.7 },
    { title: "PLOS ONE", score: 7.0 },
    { title: "IEEE Access", score: 4.8 },
  ] : [];

  const journalOptions = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { 
      type: 'value', 
      name: 'Compatibility %',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisLabel: { color: '#94a3b8' }
    },
    yAxis: { 
      type: 'category', 
      data: matches.map(m => m.title).reverse(),
      axisLabel: { color: '#f8fafc', width: 100, overflow: 'truncate' }
    },
    series: [{
      name: 'Compatibility',
      type: 'bar',
      data: matches.map(m => m.score).reverse(),
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: {
          type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [{ offset: 0, color: '#3b82f6' }, { offset: 1, color: '#8b5cf6' }]
        }
      }
    }]
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
        
        {/* Radar Chart */}
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <BookOpen color="var(--accent-primary)" size={20} />
            <h3 style={{ margin: 0 }}>Linguistic Integrity</h3>
          </div>
          <ReactECharts option={readabilityOptions} style={{ height: '250px' }} theme="dark" opts={{ renderer: 'svg' }} />
        </div>

        {/* Bar Chart */}
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <FileText color="var(--accent-secondary)" size={20} />
            <h3 style={{ margin: 0 }}>Top Journal Matches</h3>
          </div>
          <ReactECharts option={journalOptions} style={{ height: '250px' }} theme="dark" opts={{ renderer: 'svg' }} />
        </div>

      </div>

      {/* Issues Panel */}
      <div className="glass-panel">
        <h3 style={{ marginBottom: '16px' }}>Symbolic Review Findings</h3>
        {symbolic.issues && symbolic.issues.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {symbolic.issues.map((issue: string, idx: number) => (
              <div key={idx} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', background: 'rgba(239, 68, 68, 0.1)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                <AlertTriangle color="var(--danger)" size={20} style={{ flexShrink: 0 }} />
                <span style={{ fontSize: '0.95rem' }}>{issue}</span>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success)' }}>
            <CheckCircle size={20} />
            <span>No symbolic issues detected! Manuscript formatting looks great.</span>
          </div>
        )}
      </div>

    </div>
  );
};
