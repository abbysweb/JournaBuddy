import React, { useEffect, useRef } from 'react';
import { Network } from 'vis-network';

interface CitationGraphProps {
  references: any[];
}

export const CitationGraph: React.FC<CitationGraphProps> = ({ references }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);

  useEffect(() => {
    if (!containerRef.current || references.length === 0) return;

    // The central node is the user's manuscript
    const nodes: any[] = [
      { id: 'manuscript', label: 'Your Manuscript', shape: 'star', color: '#ec4899', size: 30 }
    ];
    
    const edges: any[] = [];

    references.forEach((ref) => {
      if (ref.crossref?.doi) {
        const nodeId = ref.crossref.doi;
        const citationCount = ref.openalex?.citation_count || 0;
        
        // Scale node size by citation count (min 10, max 40)
        const size = Math.min(40, Math.max(10, citationCount / 10));
        
        // Truncate title for label
        let label = ref.crossref.title || nodeId;
        if (label.length > 20) label = label.substring(0, 20) + '...';

        nodes.push({
          id: nodeId,
          label: label,
          title: ref.crossref.title + `\nCitations: ${citationCount}`,
          shape: 'dot',
          size: size,
          color: ref.crossref.is_valid ? '#10b981' : '#ef4444'
        });

        edges.push({
          from: 'manuscript',
          to: nodeId,
          arrows: 'to',
          color: { color: 'rgba(255,255,255,0.2)' }
        });
      }
    });

    const data = { nodes, edges };
    
    const options = {
      nodes: {
        font: { color: '#e2e8f0', size: 12 }
      },
      physics: {
        forceAtlas2Based: { gravitationalConstant: -50, centralGravity: 0.01, springLength: 100, springConstant: 0.08 },
        maxVelocity: 50,
        solver: 'forceAtlas2Based',
        timestep: 0.35,
        stabilization: { iterations: 150 }
      },
      interaction: { hover: true, tooltipDelay: 200 }
    };

    networkRef.current = new Network(containerRef.current, data, options);

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [references]);

  if (!references || references.length === 0) return null;

  return (
    <div style={{ width: '100%', height: '400px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};
