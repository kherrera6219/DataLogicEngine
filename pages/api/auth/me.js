import { parse } from 'cookie';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Parse cookies from request
    const cookies = parse(req.headers.cookie || '');
    const authToken = cookies.auth_token;

    if (!authToken) {
      return res.status(401).json({
        success: false,
        error: 'Not authenticated'
      });
    }

    // Verify token with backend
    const backendUrl = process.env.REACT_APP_API_URL || 'http://localhost:3000';
    const response = await fetch(`${backendUrl}/api/auth/verify`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
    });

    if (!response.ok) {
      return res.status(401).json({
        success: false,
        error: 'Invalid or expired token'
      });
    }

    const data = await response.json();

    return res.status(200).json({
      success: true,
      user: data.user
    });
  } catch (error) {
    console.error('Auth verification error:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal server error'
    });
  }
}
