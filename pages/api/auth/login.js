import { serialize } from 'cookie';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { username, password, role, simulationMode } = req.body;

    // Validate input
    if (!username || !password || !role) {
      return res.status(400).json({
        success: false,
        error: 'Username, password, and role are required'
      });
    }

    // Call the Flask backend authentication API
    const backendUrl = process.env.REACT_APP_API_URL || 'http://localhost:3000';
    const response = await fetch(`${backendUrl}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username,
        password
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return res.status(response.status).json({
        success: false,
        error: errorData.error || 'Authentication failed'
      });
    }

    const data = await response.json();

    // Set secure HTTP-only cookie with the session token
    const cookie = serialize('auth_token', data.token || '', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: data.expiresIn || 3600, // 1 hour default
      path: '/',
    });

    res.setHeader('Set-Cookie', cookie);

    // Return success with user data (no sensitive info)
    return res.status(200).json({
      success: true,
      user: {
        id: data.user?.id,
        username: data.user?.username,
        email: data.user?.email,
        role: role,
        simulationMode: simulationMode
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    return res.status(500).json({
      success: false,
      error: 'Internal server error'
    });
  }
}
