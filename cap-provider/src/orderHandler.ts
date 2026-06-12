import axios from 'axios';
import { CAPABILITY_SCHEMAS, Capability } from './schemas';
import { deliverProof } from './deliverProof';

const CAPABILITY_TO_ENDPOINT: Record<string, string> = {
  audit_agent_listing: 'audit-agent',
  audit_repository: 'audit-repository',
  verify_claims: 'verify-claims',
};

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function setupOrderHandler(client: any, EventType: any): void {
  const apiUrl = process.env.CAPSCORE_API_URL || 'http://localhost:8000';
  const maxSeconds = parseInt(process.env.MAX_JOB_SECONDS || '300', 10);

  if (!EventType) {
    console.error('[ORDER] EventType is undefined — cannot register NegotiationCreated listener');
    return;
  }

  client.on(EventType.NegotiationCreated, async (event: any) => {
    const { negotiationId, capability, payload, orderId } = event ?? {};

    console.log(`[ORDER] NegotiationCreated: negotiationId=${negotiationId} capability=${capability} orderId=${orderId}`);

    // --- Validate capability ---
    const schema = CAPABILITY_SCHEMAS[capability as Capability];
    if (!schema) {
      console.error(`[ORDER] Unknown capability: "${capability}" — skipping order`);
      return;
    }

    // --- Validate payload against Zod schema ---
    const parsed = schema.safeParse(payload);
    if (!parsed.success) {
      console.error(`[ORDER] Invalid payload for capability "${capability}":`, parsed.error.format());
      return;
    }

    console.log(`[ORDER] Payload validated for capability: ${capability}`);

    // --- Accept negotiation ---
    try {
      await client.acceptNegotiation(negotiationId);
      console.log(`[ORDER] Accepted negotiation: ${negotiationId}`);
    } catch (err: any) {
      console.error(`[ORDER] Failed to accept negotiation ${negotiationId}:`, err?.message);
      return;
    }

    // --- Submit job to Python API ---
    const endpoint = CAPABILITY_TO_ENDPOINT[capability];
    if (!endpoint) {
      console.error(`[ORDER] No API endpoint mapped for capability: ${capability}`);
      return;
    }

    let jobId: string;
    try {
      const res = await axios.post(
        `${apiUrl}/jobs/${endpoint}`,
        (parsed as any).data,
        { timeout: 10_000 }
      );
      jobId = res.data.job_id;
      console.log(`[ORDER] Job created: ${jobId} (capability=${capability})`);
    } catch (err: any) {
      console.error(`[ORDER] Failed to create job for capability "${capability}":`, err?.message);
      return;
    }

    // --- Poll for completion ---
    const deadline = Date.now() + maxSeconds * 1000;
    let jobResult: any = null;
    const pollIntervalMs = 3000;

    console.log(`[ORDER] Polling job ${jobId} (timeout=${maxSeconds}s)...`);

    while (Date.now() < deadline) {
      await sleep(pollIntervalMs);
      try {
        const statusRes = await axios.get(`${apiUrl}/jobs/${jobId}`, { timeout: 5000 });
        const job = statusRes.data;

        if (job.status === 'done') {
          console.log(`[ORDER] Job ${jobId} completed successfully`);
          jobResult = job;
          break;
        }

        if (job.status === 'failed') {
          console.error(`[ORDER] Job ${jobId} failed: ${job.error ?? 'unknown error'}`);
          break;
        }

        console.log(`[ORDER] Job ${jobId} status: ${job.status} (elapsed=${Math.round((Date.now() - (deadline - maxSeconds * 1000)) / 1000)}s)`);
      } catch (err: any) {
        console.warn(`[ORDER] Poll error for job ${jobId}:`, err?.message);
      }
    }

    if (!jobResult) {
      const reason = Date.now() >= deadline ? 'timed out' : 'failed';
      console.error(`[ORDER] Job ${jobId} ${reason} — cannot deliver order ${orderId ?? negotiationId}`);
      return;
    }

    // --- Deliver proof ---
    await deliverProof(client, orderId ?? negotiationId, jobResult, apiUrl);
  });

  console.log('[CROO] Order handler registered (listening for NegotiationCreated events)');
}
