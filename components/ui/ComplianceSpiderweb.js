
import React, { useEffect, useState, useRef } from 'react';
import * as d3 from 'd3';

const ComplianceSpiderweb = ({ standardId }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const svgRef = useRef();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/compliance/standards/${standardId || ''}`);
        const result = await response.json();
        
        if (result.status === 'success') {
          setData(result);
        } else {
          setError(result.message || 'Failed to load compliance data');
        }
      } catch (err) {
        setError('Error fetching compliance data: ' + err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [standardId]);
  
  useEffect(() => {
    if (!data || !svgRef.current) return;
    
    // Clear previous visualization
    d3.select(svgRef.current).selectAll('*').remove();
    
    const width = 800;
    const height = 600;
    const radius = Math.min(width, height) / 2 - 80;
    
    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${width / 2}, ${height / 2})`);
    
    // Create the spider web structure
    const standard = data.standard;
    const childStandards = data.child_standards || [];
    
    // Draw the center node (the current standard)
    svg.append('circle')
      .attr('r', 30)
      .attr('fill', getColorByType(standard.standard_type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);
    
    svg.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '.3em')
      .attr('fill', '#fff')
      .attr('font-size', '10px')
      .text(standard.label);
    
    // Draw the child nodes arranged in a circle
    const angleStep = (2 * Math.PI) / Math.max(childStandards.length, 1);
    
    childStandards.forEach((child, i) => {
      const angle = i * angleStep;
      const x = radius * Math.cos(angle);
      const y = radius * Math.sin(angle);
      
      // Draw connection line
      svg.append('line')
        .attr('x1', 0)
        .attr('y1', 0)
        .attr('x2', x)
        .attr('y2', y)
        .attr('stroke', '#aaa')
        .attr('stroke-width', 1);
      
      // Draw child node
      svg.append('circle')
        .attr('r', 20)
        .attr('cx', x)
        .attr('cy', y)
        .attr('fill', getColorByType(child.standard.standard_type))
        .attr('stroke', '#fff')
        .attr('stroke-width', 1);
      
      // Draw child node label
      svg.append('text')
        .attr('x', x)
        .attr('y', y)
        .attr('text-anchor', 'middle')
        .attr('dy', '.3em')
        .attr('fill', '#fff')
        .attr('font-size', '8px')
        .text(child.standard.label);
    });
    
    // Draw legend
    const legend = svg.append('g')
      .attr('transform', `translate(${-width/2 + 50}, ${-height/2 + 50})`);
    
    const standardTypes = ['iso', 'nist', 'pci', 'hipaa', 'gdpr'];
    
    standardTypes.forEach((type, i) => {
      legend.append('circle')
        .attr('r', 8)
        .attr('cx', 10)
        .attr('cy', i * 25)
        .attr('fill', getColorByType(type));
      
      legend.append('text')
        .attr('x', 25)
        .attr('y', i * 25 + 4)
        .text(type.toUpperCase())
        .attr('fill', '#333');
    });
    
  }, [data]);
  
  // Helper function to get color by standard type
  const getColorByType = (type) => {
    const colors = {
      'iso': '#1f77b4',
      'nist': '#ff7f0e',
      'pci': '#2ca02c',
      'hipaa': '#d62728',
      'gdpr': '#9467bd',
      'default': '#8c564b'
    };
    
    return colors[type] || colors.default;
  };
  
  if (loading) return <div className="text-center p-5">Loading compliance data...</div>;
  if (error) return <div className="alert alert-danger">{error}</div>;
  if (!data) return <div className="alert alert-info">No compliance data available</div>;
  
  return (
    <div className="compliance-spiderweb-container">
      <h3 className="text-center mb-4">Compliance Standards Spiderweb</h3>
      <div className="text-center">
        {data.standard && (
          <div className="mb-3">
            <h4>{data.standard.label}</h4>
            <p className="text-muted">{data.standard.description}</p>
            <p><strong>Type:</strong> {data.standard.standard_type.toUpperCase()}</p>
            <p><strong>Level:</strong> {data.standard.standard_level}</p>
            <p><strong>Code:</strong> {data.standard.code}</p>
          </div>
        )}
        
        <div className="spiderweb-visualization">
          <svg ref={svgRef}></svg>
        </div>
        
        {data.child_standards && data.child_standards.length > 0 && (
          <div className="mt-4">
            <h5>Child Standards ({data.child_standards.length})</h5>
            <div className="row">
              {data.child_standards.map(child => (
                <div key={child.standard.uid} className="col-md-4 mb-3">
                  <div className="card">
                    <div className="card-body">
                      <h6 className="card-title">{child.standard.label}</h6>
                      <p className="card-text small">{child.standard.code}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ComplianceSpiderweb;
