export default async function handler(req, res) {
  try {
    // For demonstration, we'll return simulated graph statistics instead of calling Flask backend
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

    return res.status(200).json({
      success: true,
      data: simulatedGraphStats
    });
  } catch (error) {
    console.error('Error fetching graph stats:', error);
    return res.status(500).json({ success: false, error: 'Failed to fetch graph statistics' });
  }
}