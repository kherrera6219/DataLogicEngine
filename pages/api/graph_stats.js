export default async function handler(req, res) {
  try {
    // Call Flask backend
    const response = await fetch('http://localhost:3000/api/ukg/graph_stats');
    const data = await response.json();

    // Return the response from the backend
    return res.status(response.status).json(data);
  } catch (error) {
    console.error('Error fetching graph stats:', error);
    return res.status(500).json({ error: 'Failed to fetch graph statistics' });
  }
}
export default async function handler(req, res) {
  try {
    // In a real implementation, this would call your backend
    // For demonstration, we'll return simulated graph statistics
    
    const simulatedGraphStats = {
      total_nodes: 13572,
      total_edges: 46891,
      node_types: {
        'knowledge_domain': 138,
        'topic': 824,
        'method': 427,
        'tool': 573,
        'regulatory_framework': 231,
        'compliance_standard': 185,
        'knowledge_expert': 346,
        'skill_expert': 289,
        'role_expert': 173,
        'context_expert': 192,
        'location': 321,
        'time_period': 94
      },
      last_updated: new Date().toISOString()
    };

    return res.status(200).json(simulatedGraphStats);
  } catch (error) {
    console.error('Error fetching graph stats:', error);
    return res.status(500).json({ error: 'Failed to fetch graph statistics' });
  }
}
