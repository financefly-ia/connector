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

module.exports = async function handler(req, res) {
  console.log('📥 PAYLOAD RECEBIDO EM /api/save-item:', req.body);
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

    const body = {
      clientUserId: parsedBody.clientUserId ?? null,
      itemId: parsedBody.itemId ?? null,
      userName: parsedBody.userName ?? null,
      userEmail: parsedBody.userEmail ?? null,
      institutionId: parsedBody.institutionId ?? null,
      institutionName: parsedBody.institutionName ?? null,
    };

    console.log('📥 SAVE-ITEM PAYLOAD NORMALIZADO:', body);

    const {
      clientUserId,
      itemId,
      userName,
      userEmail,
      institutionId,
      institutionName,
    } = body;

    if (!clientUserId) {
      console.error('❌ clientUserId ausente. payload:', body);
    }
    if (!itemId) {
      console.error('❌ itemId ausente. payload:', body);
    }
    if (!institutionId) {
      console.error('❌ institutionId ausente. payload:', body);
    }
    if (!institutionName) {
      console.error('❌ institutionName ausente. payload:', body);
    }

    if (!clientUserId || !itemId || !institutionId) {
      return res.status(400).json({ error: 'Missing required fields' });
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
