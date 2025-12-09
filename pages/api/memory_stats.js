
export default async function handler(req, res) {
  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';

    // Call the backend API for memory statistics
    const response = await fetch(`${backendUrl}/api/unified/memory_locate`, {
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
    console.error('Error fetching memory stats:', error);
    return res.status(500).json({
      error: 'Failed to fetch memory statistics',
      message: error.message
    });
  }
}
