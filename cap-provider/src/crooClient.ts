import * as dotenv from 'dotenv';
dotenv.config();

// NOTE: Actual import depends on @croo-network/sdk API.
// We use a resilient wrapper that handles both named exports and default exports.
let AgentClientClass: any;
let EventTypeEnum: any;

async function loadSdk(): Promise<void> {
  try {
    const sdk = await import('@croo-network/sdk');
    AgentClientClass = sdk.AgentClient || (sdk as any).default?.AgentClient;
    EventTypeEnum = sdk.EventType || (sdk as any).default?.EventType;
    if (!AgentClientClass) throw new Error('AgentClient not found in @croo-network/sdk');
    console.log('[SDK] @croo-network/sdk loaded successfully');
  } catch (e) {
    console.error('Failed to load @croo-network/sdk:', e);
    throw e;
  }
}

export { loadSdk, AgentClientClass as AgentClient, EventTypeEnum as EventType };

export function createCrooClient(): any {
  if (!AgentClientClass) {
    throw new Error('SDK not loaded. Call loadSdk() before createCrooClient().');
  }
  const config = {
    apiUrl: process.env.CROO_API_URL || 'https://api.croo.network',
    wsUrl: process.env.CROO_WS_URL || 'wss://api.croo.network/ws',
  };
  const sdkKey = process.env.CROO_SDK_KEY;
  if (!sdkKey) throw new Error('CROO_SDK_KEY is required');
  return new AgentClientClass(config, sdkKey);
}
