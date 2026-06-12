import { CAPABILITY_METADATA } from './schemas';

const RETRY_DELAYS_MS = [0, 1000, 2000, 4000]; // index 0 = first attempt (no delay)

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export async function registerCapabilities(client: any): Promise<void> {
  for (const [capabilityId, meta] of Object.entries(CAPABILITY_METADATA)) {
    const maxAttempts = 3;
    let lastError: any;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      if (attempt > 0) {
        const delayMs = 1000 * Math.pow(2, attempt - 1); // 1s, 2s, 4s
        console.log(`[CROO] Retrying capability registration for ${capabilityId} in ${delayMs}ms (attempt ${attempt + 1}/${maxAttempts})`);
        await sleep(delayMs);
      }

      try {
        if (typeof client.registerCapability === 'function') {
          await client.registerCapability({
            id: capabilityId,
            name: meta.name,
            description: meta.description,
            price: meta.price,
            currency: meta.currency,
            sla_seconds: meta.sla_seconds,
          });
          console.log(`[CROO] Registered capability: ${capabilityId} (${meta.name}) @ $${meta.price} ${meta.currency}`);
        } else {
          console.warn(`[CROO] client.registerCapability is not a function — skipping ${capabilityId}`);
        }
        lastError = null;
        break;
      } catch (err: any) {
        lastError = err;
        console.warn(`[CROO] Attempt ${attempt + 1}/${maxAttempts} failed for ${capabilityId}:`, err?.message);
      }
    }

    if (lastError) {
      console.warn(`[CROO] Could not register ${capabilityId} after ${maxAttempts} attempts:`, lastError?.message);
    }
  }

  console.log('[CROO] Capability registration complete');
}
