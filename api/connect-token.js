const ALLOWED_METHODS = ['POST', 'OPTIONS'];

function setCors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', ALLOWED_METHODS.join(','));
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

module.exports = async function handler(req, res) {
  setCors(res);

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  const body =
    typeof req.body === 'string'
      ? JSON.parse(req.body || '{}')
      : req.body || {};

  const clientUserId = body.clientUserId || null;
  const itemId = body.itemId || null;

  if (!clientUserId) {
    return res.status(400).json({ error: 'clientUserId is required' });
  }

  const clientId = process.env.PLUGGY_CLIENT_ID;
  const clientSecret = process.env.PLUGGY_CLIENT_SECRET;

  if (!clientId || !clientSecret) {
    return res
      .status(500)
      .json({ error: 'Pluggy credentials are not configured' });
  }

  try {
    const authResponse = await fetch('https://api.pluggy.ai/auth', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        accept: 'application/json',
      },
      body: JSON.stringify({
        clientId,
        clientSecret,
      }),
    });

    if (authResponse.status === 401) {
      return res.status(401).json({ error: 'Invalid Pluggy credentials' });
    }

    if (!authResponse.ok) {
      const text = await authResponse.text();
      console.error('Pluggy auth error:', text);
      return res.status(500).json({ error: 'Failed to authenticate with Pluggy' });
    }

    const authData = await authResponse.json();
    const apiKey = authData.apiKey;

    if (!apiKey) {
      return res.status(500).json({ error: 'Pluggy API key missing' });
    }

    const tokenResponse = await fetch('https://api.pluggy.ai/connect_token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        accept: 'application/json',
        'X-API-KEY': apiKey,
      },
      body: JSON.stringify(
        itemId
          ? { clientUserId, itemId }
          : { clientUserId }
      ),
    });

    if (!tokenResponse.ok) {
      const text = await tokenResponse.text();
      console.error('Pluggy token error:', text);
      if (tokenResponse.status === 401) {
        return res.status(401).json({ error: 'Unauthorized to generate token' });
      }
      return res.status(500).json({ error: 'Failed to generate connect token' });
    }

    const tokenData = await tokenResponse.json();
    const accessToken = tokenData.accessToken;

    if (!accessToken) {
      return res.status(500).json({ error: 'Pluggy accessToken missing' });
    }

    return res.status(200).json({ accessToken });
  } catch (error) {
    console.error('connect-token error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
};
