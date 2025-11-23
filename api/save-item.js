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

  const {
    clientUserId,
    itemId,
    userName,
    userEmail,
    institutionId,
    institutionName,
  } = body;

  if (
    !clientUserId ||
    !itemId ||
    !userName ||
    !userEmail ||
    !institutionId ||
    !institutionName
  ) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  try {
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
  } catch (error) {
    console.error('save-item error:', error);
    return res.status(500).json({ error: 'Failed to save item' });
  }
};
