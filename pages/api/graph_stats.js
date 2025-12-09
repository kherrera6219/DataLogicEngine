
export default async function handler(req, res) {
  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';

    // Call the backend API for graph statistics
    const response = await fetch(`${backendUrl}/api/v1/graph/stats`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Backend returned ${response.status}`);
    }

    const data = await response.json();

    return res.status(200).json(data);
  } catch (error) {
    console.error('Error fetching graph stats:', error);
    return res.status(500).json({
      error: 'Failed to fetch graph statistics',
      message: error.message
    });
  }
}
