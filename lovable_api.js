/**
 * Stock prediction API client for Lovable (Vite) frontends.
 * Point BASE_URL at your deployed Python API (see server.py).
 *
 * Set VITE_STOCK_API_URL in Lovable env to your server origin, e.g. https://api.yourdomain.com
 */

const BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_STOCK_API_URL) ||
  'http://127.0.0.1:5000';

const defaultHeaders = (apiKey) => {
  const h = { 'Content-Type': 'application/json' };
  if (apiKey) h['X-API-Key'] = apiKey;
  return h;
};

export async function checkHealth(apiKey) {
  const r = await fetch(`${BASE_URL}/health`, { headers: defaultHeaders(apiKey) });
  return r.json();
}

/** Latest polled quote (backend refreshes watched symbols on MARKET_REFRESH_SECONDS). */
export async function getQuote(symbol, apiKey) {
  const r = await fetch(
    `${BASE_URL}/api/v1/quote?${new URLSearchParams({ symbol })}`,
    { headers: defaultHeaders(apiKey) }
  );
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || r.statusText);
  return data;
}

/**
 * @param {string} symbol
 * @param {object} [clientContext] — merged on server with live market signals
 * @param {string} [apiKey] — if STOCK_API_KEY is set on server
 */
export async function predictStock(symbol, clientContext = undefined, apiKey = undefined) {
  const body = { symbol };
  if (clientContext && typeof clientContext === 'object') body.client_context = clientContext;
  const r = await fetch(`${BASE_URL}/api/v1/predict`, {
    method: 'POST',
    headers: defaultHeaders(apiKey),
    body: JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || r.statusText);
  return data;
}

export async function analyzePortfolio(holdings, clientContext = undefined, apiKey = undefined) {
  const body = { holdings };
  if (clientContext && typeof clientContext === 'object') body.client_context = clientContext;
  const r = await fetch(`${BASE_URL}/api/v1/portfolio`, {
    method: 'POST',
    headers: defaultHeaders(apiKey),
    body: JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || r.statusText);
  return data;
}

export default { checkHealth, getQuote, predictStock, analyzePortfolio, BASE_URL };
