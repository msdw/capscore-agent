import * as dotenv from 'dotenv';
dotenv.config();

// Resolved from @croo-network/sdk at runtime (handles named/default exports).
let AgentClientClass: any;
let EventTypeEnum: any;
let DeliverableTypeEnum: any;

async function loadSdk(): Promise<void> {
  const sdk: any = await import('@croo-network/sdk');
  const root = sdk.default ?? sdk;
  AgentClientClass = sdk.AgentClient ?? root.AgentClient;
  EventTypeEnum = sdk.EventType ?? root.EventType;
  DeliverableTypeEnum = sdk.DeliverableType ?? root.DeliverableType;
  if (!AgentClientClass) throw new Error('AgentClient not found in @croo-network/sdk');
  console.log('[SDK] @croo-network/sdk loaded');
}

export { loadSdk, AgentClientClass as AgentClient, EventTypeEnum as EventType, DeliverableTypeEnum as DeliverableType };

export function createCrooClient(): any {
  if (!AgentClientClass) throw new Error('SDK not loaded. Call loadSdk() first.');
  // Real SDK v0.2.x config fields are baseURL / wsURL (not apiUrl / wsUrl).
  const config: any = {
    baseURL: process.env.CROO_API_URL || 'https://api.croo.network',
    wsURL: process.env.CROO_WS_URL || 'wss://api.croo.network/ws',
  };
  if (process.env.BASE_RPC_URL) config.rpcURL = process.env.BASE_RPC_URL;
  const sdkKey = process.env.CROO_SDK_KEY;
  if (!sdkKey || sdkKey.startsWith('croo_sk_your')) {
    throw new Error('CROO_SDK_KEY is required (get it from https://agent.croo.network → Register Agent).');
  }
  return new AgentClientClass(config, sdkKey);
}
