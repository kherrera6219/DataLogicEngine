
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { query, target_confidence, chat_id } = req.body;
    
    // Make a request to the Flask backend
    const response = await fetch(`http://localhost:3000/api/ukg/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        target_confidence: target_confidence || 0.85,
        chat_id
      }),
    });
    
    const data = await response.json();
    
    // Return the response from the backend
    return res.status(response.status).json(data);
  } catch (error) {
    console.error('Error processing query:', error);
    return res.status(500).json({ error: 'Failed to process query' });
  }
}
