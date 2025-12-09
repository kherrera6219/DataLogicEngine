export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed'
    });
  }

  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';

    // Get the query from the request
    const { query, confidence, confidenceThreshold, refinementSteps, maxLayer } = req.body;

    if (!query) {
      return res.status(400).json({
        success: false,
        error: 'Query is required'
      });
    }

    // Call the backend API
    const response = await fetch(`${backendUrl}/api/v1/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        confidence_threshold: confidenceThreshold || confidence || 0.85,
        refinement_steps: refinementSteps || 12,
        max_layer: maxLayer || 5
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Backend returned ${response.status}`);
    }

    const data = await response.json();

    // Transform backend response to match frontend expectations
    const responseData = {
      response: data.response || data.result,
      query_processed: query,
      confidenceScore: data.confidence_score || data.confidence || 0.85,
      activeLayer: data.active_layer || data.layer || 1,
      elapsedTime: data.elapsed_time || data.processing_time || 0
    };

    return res.status(200).json(responseData);
  } catch (error) {
    console.error('Error processing query:', error);
    return res.status(500).json({
      success: false,
      error: error.message || 'An error occurred while processing your query'
    });
  }
}