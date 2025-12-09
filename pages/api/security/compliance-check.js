export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ success: false, message: 'Method not allowed' });
  }

  try {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';
    const { framework, control_id } = req.body;

    // Call the backend compliance API
    const endpoint = control_id
      ? `${backendUrl}/api/security/compliance/status`
      : `${backendUrl}/api/compliance/standards`;

    const response = await fetch(endpoint, {
      method: control_id ? 'GET' : 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Backend returned ${response.status}`);
    }

    const data = await response.json();

    // Transform backend response to match expected format
    if (control_id && data.controls) {
      const control = data.controls.find(c => c.id === control_id);
      if (!control) {
        throw new Error(`Control ${control_id} not found in framework ${framework}`);
      }
      return res.status(200).json({
        framework: framework || 'SOC2',
        control_id,
        ...control,
        timestamp: new Date().toISOString()
      });
    }

    return res.status(200).json(data);
  } catch (error) {
    console.error('Error in compliance check:', error);
    return res.status(500).json({
      success: false,
      message: 'Error performing compliance check',
      error: error.message
    });
  }
}
