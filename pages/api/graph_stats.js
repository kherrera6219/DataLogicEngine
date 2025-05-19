export default async function handler(req, res) {
  try {
    // Make a request to the Flask backend
    const response = await fetch(`http://localhost:3000/api/graph_stats`);
    const data = await response.json();

    // Return the response from the backend
    return res.status(response.status).json(data);
  } catch (error) {
    console.error('Error fetching graph stats:', error);
    return res.status(500).json({ error: 'Failed to fetch graph statistics' });
  }
}