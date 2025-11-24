const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST,
  port: Number(process.env.DB_PORT) || 5432,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  ssl:
    process.env.DB_SSLMODE && process.env.DB_SSLMODE.toLowerCase() !== 'disable'
      ? { rejectUnauthorized: false }
      : undefined,
});

const DDL = `
CREATE TABLE IF NOT EXISTS items (
  id SERIAL PRIMARY KEY,
  client_user_id TEXT,
  item_id TEXT,
  user_name TEXT,
  user_email TEXT,
  institution_id TEXT,
  institution_name TEXT,
  date_created TIMESTAMP DEFAULT NOW(),
  date_updated TIMESTAMP DEFAULT NOW()
)`;

let tableInitialized = false;

const ALLOWED_METHODS = ['POST', 'OPTIONS'];

function setCors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', ALLOWED_METHODS.join(','));
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

async function ensureTable() {
  if (!tableInitialized) {
    await pool.query(DDL);
    tableInitialized = true;
  }
}

async function fetchPluggyApiKey() {
  const response = await fetch('https://api.pluggy.ai/auth', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      accept: 'application/json',
    },
    body: JSON.stringify({
      clientId: process.env.PLUGGY_CLIENT_ID,
      clientSecret: process.env.PLUGGY_CLIENT_SECRET,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Falha ao autenticar com Pluggy: ${errorText}`);
  }

  const data = await response.json();
  if (!data?.apiKey) {
    throw new Error('Resposta Pluggy sem apiKey');
  }
  console.log('🔑 API KEY OBTIDA');
  return data.apiKey;
}

async function fetchPluggyItem(apiKey, itemId) {
  const response = await fetch(`https://api.pluggy.ai/items/${itemId}`, {
    headers: {
      accept: 'application/json',
      'X-API-KEY': apiKey,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Falha ao buscar item na Pluggy: ${errorText}`);
  }

  const data = await response.json();
  console.log('🔍 ITEM DATA COMPLETO DA PLUGGY:', JSON.stringify(data, null, 2));
  return data;
}

module.exports = async function handler(req, res) {
  console.log('📥 PAYLOAD RECEBIDO:', req.body);
  try {
    setCors(res);

    if (req.method === 'OPTIONS') {
      return res.status(200).end();
    }

    if (req.method !== 'POST') {
      console.error('❌ Método inválido em /api/save-item:', req.method);
      return res.status(405).json({ error: 'Method Not Allowed' });
    }

    const parsedBody =
      typeof req.body === 'string'
        ? JSON.parse(req.body || '{}')
        : req.body || {};

    const {
      clientUserId = null,
      itemId = null,
      userName = null,
      userEmail = null,
      institutionId: incomingInstitutionId = null,
      institutionName: incomingInstitutionName = null,
    } = parsedBody;

    if (!clientUserId) {
      console.error('❌ clientUserId ausente. payload:', parsedBody);
    }
    if (!itemId) {
      console.error('❌ itemId ausente. payload:', parsedBody);
    }

    if (!clientUserId || !itemId) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    let institutionId = incomingInstitutionId;
    let institutionName = incomingInstitutionName;

    if (!institutionId || !institutionName) {
      const apiKey = await fetchPluggyApiKey();
      const itemData = await fetchPluggyItem(apiKey, itemId);

      institutionId =
        itemData?.institution?.id ||
        itemData?.institutionId ||
        itemData?.connector?.id ||
        institutionId ||
        null;

      institutionName =
        itemData?.institution?.name ||
        itemData?.institution?.providerName ||
        itemData?.institution?.fullName ||
        itemData?.connector?.name ||
        institutionName ||
        null;
    }

    console.log('🏦 institutionId final:', institutionId);
    console.log('🏦 institutionName final:', institutionName);

    if (!institutionId || !institutionName) {
      console.error('❌ Não foi possível resolver instituição para o item:', itemId);
    }

    await ensureTable();
    const insertQuery = `
      INSERT INTO items
      (client_user_id, item_id, user_name, user_email, institution_id, institution_name)
      VALUES ($1, $2, $3, $4, $5, $6)
    `;
    await pool.query(insertQuery, [
      clientUserId,
      itemId,
      userName,
      userEmail,
      institutionId,
      institutionName,
    ]);
    return res.status(200).json({ status: 'saved' });
  } catch (err) {
    console.error('🔥 ERRO INTERNO /api/save-item:', err);
    return res.status(500).json({ error: err.message || 'Erro interno' });
  }
};
