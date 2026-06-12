import * as dotenv from 'dotenv';
dotenv.config();

async function main(): Promise<void> {
  console.log('[CAPSCORE] Starting CAP Provider v0.1.0');
  console.log(`[CAPSCORE] API URL: ${process.env.CROO_API_URL || 'https://api.croo.network'}`);
  console.log(`[CAPSCORE] WS URL: ${process.env.CROO_WS_URL || 'wss://api.croo.network/ws'}`);
  console.log(`[CAPSCORE] CAPScore API: ${process.env.CAPSCORE_API_URL || 'http://localhost:8000'}`);

  // Dynamically import to ensure SDK is loaded before use
  const { loadSdk, createCrooClient, EventType } = await import('./crooClient');

  // Load the CROO SDK
  await loadSdk();

  const { registerCapabilities } = await import('./registerCapabilities');
  const { setupOrderHandler } = await import('./orderHandler');

  // Create the CROO client
  const client = createCrooClient();
  console.log('[CAPSCORE] CROO client created');

  // Register all capabilities with retry logic
  await registerCapabilities(client);

  // Get EventType from the loaded SDK (re-import to get the resolved value)
  const { EventType: resolvedEventType } = await import('./crooClient');

  // Setup order handler (registers NegotiationCreated listener)
  setupOrderHandler(client, resolvedEventType);

  // Connect WebSocket
  try {
    await client.connectWebSocket();
    console.log('[CAPSCORE] WebSocket connected — listening for CAP orders...');
  } catch (err: any) {
    console.error('[CAPSCORE] WebSocket connection failed:', err?.message);
    process.exit(1);
  }

  // Graceful shutdown handler
  const shutdown = async (signal: string): Promise<void> => {
    console.log(`[CAPSCORE] Received ${signal} — shutting down gracefully...`);
    try {
      if (typeof client.disconnect === 'function') {
        await client.disconnect();
        console.log('[CAPSCORE] Client disconnected');
      }
    } catch (err: any) {
      console.warn('[CAPSCORE] Error during disconnect:', err?.message);
    }
    process.exit(0);
  };

  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));

  // Periodic health check log
  const healthInterval = setInterval(() => {
    console.log(`[CAPSCORE] Health OK — ${new Date().toISOString()}`);
  }, 60_000);

  // Prevent the health interval from keeping the process alive on shutdown
  healthInterval.unref();

  console.log('[CAPSCORE] CAP Provider ready');
}

main().catch((err: unknown) => {
  console.error('[CAPSCORE] Fatal error:', err);
  process.exit(1);
});
