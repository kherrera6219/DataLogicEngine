export default async function handler(req, res) {
  try {
    // Make request to Flask backend
    const response = await fetch('http://localhost:3000/api/memory_stats', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    const data = await response.json();

    // Return the response from the backend
    return res.status(response.status).json(data);
  } catch (error) {
    console.error('Error fetching memory stats:', error);
    return res.status(500).json({ error: 'Failed to fetch memory statistics' });
  }
}