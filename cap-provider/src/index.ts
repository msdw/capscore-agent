import * as dotenv from 'dotenv';
import * as http from 'http';
dotenv.config();

let online = false;

/** Minimal health server so the provider can run as a free web service (Render injects $PORT). */
function startHealthServer(): void {
  const port = parseInt(process.env.PORT || '3000', 10);
  http
    .createServer((req, res) => {
      if (req.url === '/health') {
        res.writeHead(online ? 200 : 503, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: online ? 'online' : 'starting', agent: 'CAPScore CAP provider' }));
      } else {
        res.writeHead(200, { 'Content-Type': 'text/plain' });
        res.end('CAPScore CAP provider — see /health');
      }
    })
    .listen(port, () => console.log(`[CAPSCORE] health server on :${port}`));
}

async function main(): Promise<void> {
  startHealthServer();
  console.log('[CAPSCORE] Starting CAP Provider v0.2.0');
  console.log(`[CAPSCORE] CROO API: ${process.env.CROO_API_URL || 'https://api.croo.network'}`);
  console.log(`[CAPSCORE] CROO WS:  ${process.env.CROO_WS_URL || 'wss://api.croo.network/ws'}`);
  console.log(`[CAPSCORE] Analysis API: ${process.env.CAPSCORE_API_URL || 'http://localhost:8000'}`);

  const { loadSdk, createCrooClient, EventType, DeliverableType } = await import('./crooClient');
  await loadSdk();

  const { setupOrderHandler } = await import('./orderHandler');
  const { printServiceConfig } = await import('./registerCapabilities');

  // Services (capabilities/pricing/schemas) are configured in the CROO dashboard,
  // not via the SDK. Print the intended config for reference on startup.
  printServiceConfig();

  const client = createCrooClient();
  console.log('[CAPSCORE] CROO client created');

  // connectWebSocket() returns an event stream we attach lifecycle handlers to.
  let stream: any;
  try {
    stream = await client.connectWebSocket();
    online = true;
    console.log('[CAPSCORE] WebSocket connected — agent is online and discoverable in the Store.');
  } catch (err: any) {
    console.error('[CAPSCORE] WebSocket connection failed:', err?.message);
    process.exit(1);
  }

  setupOrderHandler(stream, client, EventType, DeliverableType);

  const shutdown = async (signal: string): Promise<void> => {
    console.log(`[CAPSCORE] ${signal} — shutting down...`);
    try { await stream?.close?.(); } catch {}
    try { await client.disconnect?.(); } catch {}
    process.exit(0);
  };
  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));

  const health = setInterval(() => console.log(`[CAPSCORE] online — ${new Date().toISOString()}`), 60_000);
  health.unref();
  console.log('[CAPSCORE] CAP Provider ready — waiting for orders.');
}

main().catch((err: unknown) => {
  console.error('[CAPSCORE] Fatal error:', err);
  process.exit(1);
});
