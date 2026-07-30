import React from 'react';
import ReactECharts from 'echarts-for-react';
import { BookOpen, CheckCircle, AlertTriangle, FileText, Brain, Link, Info } from 'lucide-react';

interface DashboardProps {
  payload: any;
}

export const Dashboard: React.FC<DashboardProps> = ({ payload }) => {
  if (!payload) return null;

  const symbolic = payload.symbolic_check || {};
  const readabilityScore = symbolic.flesch_reading_ease || 0;
  const matches = Array.isArray(payload.journal_matches) ? payload.journal_matches : [];
  const agents = payload.agents || {};
  const references = payload.reference_enrichment || [];

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
      data: matches.map((m: any) => m.title).reverse(),
      axisLabel: { color: '#f8fafc', width: 100, overflow: 'truncate' }
    },
    series: [{
      name: 'Compatibility',
      type: 'bar',
      data: matches.map((m: any) => m.compatibility_percent || 0).reverse(),
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <BookOpen color="var(--accent-primary)" size={20} />
            <h3 style={{ margin: 0 }}>Linguistic Integrity</h3>
            <span title="Measures sentence complexity, passive voice usage, and formatting correctness to ensure high academic readability." style={{ cursor: 'help' }}>
              <Info size={16} color="var(--text-secondary)" />
            </span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Mathematical evaluation of text complexity based on Flesch-Kincaid and symbolic grammar rules.
          </p>
          <ReactECharts option={readabilityOptions} style={{ height: '250px' }} theme="dark" opts={{ renderer: 'svg' }} />
        </div>

        {/* Bar Chart */}
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <FileText color="var(--accent-secondary)" size={20} />
            <h3 style={{ margin: 0 }}>Top Journal Matches</h3>
            <span title="Uses pgvector cosine distance to compare your manuscript's semantic embeddings against a database of Open Access journals." style={{ cursor: 'help' }}>
              <Info size={16} color="var(--text-secondary)" />
            </span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Journals statistically most likely to accept your manuscript based on semantic scope similarity.
          </p>
          <ReactECharts option={journalOptions} style={{ height: '250px' }} theme="dark" opts={{ renderer: 'svg' }} />
        </div>
      </div>

      {/* AI Agents Evaluation Panel */}
      {Object.keys(agents).length > 0 && (
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Brain color="#ec4899" size={20} />
            <h3 style={{ margin: 0 }}>LLM Agent Evaluations</h3>
            <span title="Results from Ollama Llama 3 agents running specialized academic peer-review prompts." style={{ cursor: 'help' }}>
              <Info size={16} color="var(--text-secondary)" />
            </span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Qualitative analysis produced by local Language Models evaluating intelligence, rigor, and compliance.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
            {Object.entries(agents).map(([agentName, agentData]: [string, any]) => (
              <div key={agentName} style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px', border: '1px solid var(--glass-border)' }}>
                <h4 style={{ color: 'var(--accent-primary)', marginBottom: '12px', textTransform: 'capitalize' }}>
                  {agentName.replace('_', ' ')}
                </h4>
                {agentData.status === 'degraded' ? (
                  <p style={{ color: 'var(--warning)', fontSize: '0.9rem' }}>API unavailable. Returning degraded result.</p>
                ) : (
                  <ul style={{ fontSize: '0.9rem', color: 'var(--text-primary)', paddingLeft: '20px' }}>
                    {Object.entries(agentData).map(([key, val]) => (
                      <li key={key} style={{ marginBottom: '8px' }}>
                        <strong style={{ color: 'var(--text-secondary)' }}>{key}: </strong> 
                        {Array.isArray(val) ? val.join(', ') : String(val)}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reference Enrichment Panel */}
      {references.length > 0 && (
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Link color="#10b981" size={20} />
            <h3 style={{ margin: 0 }}>Reference Verifications (Crossref / OpenAlex)</h3>
            <span title="DOIs extracted from your text were validated via Crossref API and enriched with citation counts from OpenAlex." style={{ cursor: 'help' }}>
              <Info size={16} color="var(--text-secondary)" />
            </span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Automated verification of your citations to ensure they are valid DOIs and are highly cited.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '300px', overflowY: 'auto' }}>
            {references.map((ref: any, idx: number) => (
              <div key={idx} style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.05)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <strong style={{ fontSize: '0.95rem' }}>{ref.crossref?.title || "Unknown Title"}</strong>
                  {ref.crossref?.is_valid ? <CheckCircle size={18} color="var(--success)" /> : <AlertTriangle size={18} color="var(--danger)" />}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  <span>DOI: {ref.crossref?.doi}</span> | 
                  <span style={{ marginLeft: '8px', color: 'var(--accent-primary)' }}>Citations: {ref.openalex?.citation_count || 0}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Issues Panel */}
      <div className="glass-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <AlertTriangle color="var(--warning)" size={20} />
          <h3 style={{ margin: 0 }}>Symbolic Review Findings</h3>
          <span title="Deterministic rule-based checks that scan for acronym definitions, missing sections, and hardcoded logic flaws." style={{ cursor: 'help' }}>
            <Info size={16} color="var(--text-secondary)" />
          </span>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
          Strict rule violations that could lead to immediate editorial rejection.
        </p>
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
