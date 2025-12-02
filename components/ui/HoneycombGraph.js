
import React, { useEffect, useRef, useState } from 'react';

// ForceGraph2D relies on the browser window and canvas APIs. Import it lazily
// so that Next.js can safely render pages during SSR/static generation without
// encountering "window is not defined" errors.
let ForceGraph2D = null;

const HoneycombGraph = ({ data, centerNodeId, width = 800, height = 600 }) => {
  const graphRef = useRef();
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [isGraphReady, setIsGraphReady] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function loadGraphLib() {
      if (typeof window === 'undefined') {
        return;
      }

      if (!ForceGraph2D) {
        const module = await import('react-force-graph-2d');
        if (isMounted) {
          ForceGraph2D = module.default;
        }
      }

      if (isMounted) {
        setIsGraphReady(true);
      }
    }

    loadGraphLib();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (data) {
      const nodes = [];
      const links = [];
      const nodeMap = {};

      // Process center node
      if (data.center_node) {
        const centerNode = {
          id: data.center_node.uid,
          name: data.center_node.name || data.center_node.label || 'Unknown',
          axis: data.center_node.axis_number || 0,
          type: data.center_node.node_type || 'unknown',
          val: 20, // Larger size for center node
          color: getAxisColor(data.center_node.axis_number || 0)
        };
        nodes.push(centerNode);
        nodeMap[centerNode.id] = true;
      }

      // Process connections
      if (data.connections_created) {
        data.connections_created.forEach(conn => {
          if (conn.target && !nodeMap[conn.target.uid]) {
            const targetNode = {
              id: conn.target.uid,
              name: conn.target.name || conn.target.label || 'Unknown',
              axis: conn.axis || conn.target.axis_number || 0,
              type: conn.target.node_type || 'unknown',
              val: 10,
              color: getAxisColor(conn.axis || conn.target.axis_number || 0)
            };
            nodes.push(targetNode);
            nodeMap[targetNode.id] = true;
          }

          if (conn.edge) {
            links.push({
              source: conn.edge.source_id,
              target: conn.edge.target_id,
              type: conn.connection_type || conn.edge.edge_type,
              strength: conn.strength || 1.0,
              value: conn.strength || 1.0,
              color: getLinkColor(conn.connection_type || conn.edge.edge_type)
            });
          }
        });
      }

      setGraphData({ nodes, links });
    }
  }, [data]);

  useEffect(() => {
    if (graphRef.current && centerNodeId) {
      const centerNode = graphData.nodes.find(node => node.id === centerNodeId);
      if (centerNode) {
        graphRef.current.centerAt(centerNode.x, centerNode.y, 1000);
        graphRef.current.zoom(2.5, 1000);
      }
    }
  }, [graphData, centerNodeId]);

  const getAxisColor = (axisNumber) => {
    const axisColors = {
      0: '#cccccc', // Default gray
      1: '#ff5555', // Red for Pillar Levels
      2: '#5555ff', // Blue for Sectors
      3: '#55aa55', // Green for Branches
      4: '#aa55aa', // Purple for Methods
      5: '#55aaaa', // Teal for Tools
      6: '#aaaa55', // Yellow for Regulatory
      7: '#ff9955', // Orange for Compliance
      8: '#5599ff', // Light blue for Knowledge Experts
      9: '#ff55aa', // Pink for Skill Experts
      10: '#aa77ff', // Lavender for Role Experts
      11: '#77aaff', // Sky blue for Context Experts
      12: '#ffaa77', // Peach for Locations
      13: '#77ff77'  // Light green for Time
    };
    return axisColors[axisNumber] || axisColors[0];
  };

  const getLinkColor = (linkType) => {
    const linkColors = {
      'direct_application': '#ff5555', // Red
      'enables': '#5555ff',          // Blue
      'implements': '#55aa55',       // Green
      'specializes': '#aa55aa',      // Purple
      'extends': '#55aaaa',          // Teal
      'alternative_to': '#aaaa55',   // Yellow
      'derived_from': '#ff9955',     // Orange
      'regulated_by': '#5599ff',     // Light blue
      'certified_by': '#ff55aa',     // Pink
      'compatible_with': '#aa77ff',  // Lavender
      'prerequisite_for': '#77aaff', // Sky blue
      'crosswalks_to': '#ffaa77'     // Peach
    };
    return linkColors[linkType] || '#aaaaaa'; // Default gray
  };

  const handleNodeClick = (node) => {
    if (graphRef.current) {
      graphRef.current.centerAt(node.x, node.y, 1000);
      graphRef.current.zoom(2.5, 1000);
    }
  };

  return (
    <div className="honeycomb-graph-container" style={{ width, height }}>
      {isGraphReady && graphData.nodes.length > 0 ? (
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          nodeLabel={node => `${node.name} (Axis ${node.axis})`}
          linkLabel={link => `${link.type} (Strength: ${link.strength.toFixed(2)})`}
          nodeRelSize={6}
          onNodeClick={handleNodeClick}
          linkWidth={link => 2 * link.value}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={link => 2 * link.value}
          cooldownTicks={100}
          width={width}
          height={height}
        />
      ) : (
        <div className="text-center p-5">
          <p>
            {isGraphReady
              ? 'No honeycomb data available. Generate a honeycomb network first.'
              : 'Loading visualization engine...'}
          </p>
        </div>
      )}
    </div>
  );
};

export default HoneycombGraph;
