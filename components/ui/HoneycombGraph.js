import React, { useEffect, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Spinner, Text, makeStyles, mergeClasses } from '@fluentui/react-components';

const useStyles = makeStyles({
  root: {
    position: 'relative',
    width: '100%',
    height: '100%',
    borderRadius: '20px',
    backgroundColor: 'var(--colorNeutralBackground3)',
    border: '1px solid rgba(255, 255, 255, 0.04)',
    boxShadow: '0 18px 45px rgba(9, 17, 32, 0.35)',
    overflow: 'hidden',
  },
  centered: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    width: '100%',
    height: '100%',
    textAlign: 'center',
    color: 'var(--colorNeutralForeground3)',
  },
  spinner: {
    color: 'var(--colorBrandForegroundLink)',
  },
});

const DEFAULT_GRAPH = { nodes: [], links: [] };

const HoneycombGraph = ({
  data,
  graphData: externalGraphData,
  centerNodeId,
  width = 800,
  height = 520,
  loading = false,
  emptyMessage = 'No honeycomb data available. Generate a honeycomb network first.',
  className,
  style,
  onNodeClick,
}) => {
  const styles = useStyles();
  const graphRef = useRef();
  const [graphData, setGraphData] = useState(externalGraphData || DEFAULT_GRAPH);

  useEffect(() => {
    if (externalGraphData) {
      setGraphData(externalGraphData);
      return;
    }

    if (!data) {
      setGraphData(DEFAULT_GRAPH);
      return;
    }

    const nodes = [];
    const links = [];
    const nodeMap = {};

    if (data.center_node) {
      const centerNode = {
        id: data.center_node.uid,
        name: data.center_node.name || data.center_node.label || 'Unknown',
        axis: data.center_node.axis_number || 0,
        type: data.center_node.node_type || 'unknown',
        val: 20,
        color: getAxisColor(data.center_node.axis_number || 0),
      };
      nodes.push(centerNode);
      nodeMap[centerNode.id] = true;
    }

    if (data.connections_created) {
      data.connections_created.forEach((conn) => {
        if (conn.target && !nodeMap[conn.target.uid]) {
          const targetNode = {
            id: conn.target.uid,
            name: conn.target.name || conn.target.label || 'Unknown',
            axis: conn.axis || conn.target.axis_number || 0,
            type: conn.target.node_type || 'unknown',
            val: 10,
            color: getAxisColor(conn.axis || conn.target.axis_number || 0),
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
            color: getLinkColor(conn.connection_type || conn.edge.edge_type),
          });
        }
      });
    }

    setGraphData({ nodes, links });
  }, [data, externalGraphData]);

  useEffect(() => {
    if (!graphRef.current || !centerNodeId) {
      return;
    }

    const centerNode = graphData.nodes.find((node) => node.id === centerNodeId);
    if (centerNode) {
      graphRef.current.centerAt(centerNode.x, centerNode.y, 1000);
      graphRef.current.zoom(2.5, 1000);
    }
  }, [graphData, centerNodeId]);

  const containerStyle = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
    ...style,
  };

  const hasNodes = graphData.nodes && graphData.nodes.length > 0;

  return (
    <div className={mergeClasses(styles.root, className)} style={containerStyle}>
      {loading ? (
        <div className={styles.centered}>
          <Spinner appearance="primary" size="large" className={styles.spinner} />
          <Text>No data yet&mdash;fetching the honeycomb network.</Text>
        </div>
      ) : hasNodes ? (
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          nodeLabel={(node) => `${node.name} (Axis ${node.axis ?? 'N/A'})`}
          linkLabel={(link) => `${link.type || 'connection'} (Strength: ${Number(link.strength || link.value || 1).toFixed(2)})`}
          nodeRelSize={6}
          onNodeClick={(node) => {
            if (onNodeClick) {
              onNodeClick(node);
            }
            if (graphRef.current) {
              graphRef.current.centerAt(node.x, node.y, 1000);
              graphRef.current.zoom(2.5, 1000);
            }
          }}
          linkWidth={(link) => 2 * Number(link.value || link.strength || 1)}
          linkColor={(link) => link.color || getLinkColor(link.type)}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={(link) => 2 * Number(link.value || link.strength || 1)}
          cooldownTicks={100}
          width={typeof width === 'number' ? width : undefined}
          height={typeof height === 'number' ? height : undefined}
        />
      ) : (
        <div className={styles.centered}>
          <Text>{emptyMessage}</Text>
        </div>
      )}
    </div>
  );
};

const getAxisColor = (axisNumber = 0) => {
  const axisColors = {
    0: '#6b778d',
    1: '#ff5555',
    2: '#5555ff',
    3: '#55aa55',
    4: '#aa55aa',
    5: '#55aaaa',
    6: '#aaaa55',
    7: '#ff9955',
    8: '#5599ff',
    9: '#ff55aa',
    10: '#aa77ff',
    11: '#77aaff',
    12: '#ffaa77',
    13: '#77ff77',
  };

  return axisColors[axisNumber] || axisColors[0];
};

const getLinkColor = (linkType) => {
  const linkColors = {
    direct_application: '#ff5555',
    enables: '#5555ff',
    implements: '#55aa55',
    specializes: '#aa55aa',
    extends: '#55aaaa',
    alternative_to: '#aaaa55',
    derived_from: '#ff9955',
    regulated_by: '#5599ff',
    certified_by: '#ff55aa',
    compatible_with: '#aa77ff',
    prerequisite_for: '#77aaff',
    crosswalks_to: '#ffaa77',
  };

  return linkColors[linkType] || '#aaaaaa';
};

export default HoneycombGraph;
