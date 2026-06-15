import axios from 'axios';
import { CAPABILITY_SCHEMAS, Capability } from './schemas';
import { deliverResult } from './deliverProof';

const CAPABILITY_TO_ENDPOINT: Record<Capability, string> = {
  audit_agent_listing: 'audit-agent',
  audit_repository: 'audit-repository',
  verify_claims: 'verify-claims',
};

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// Order input is captured at negotiation time and used once the order is paid.
const orderInputs = new Map<string, { capability: Capability; input: any }>();

/** Parse the requester's requirements/input from a CROO event (defensive across shapes). */
function extractInput(event: any): any {
  const raw =
    event?.requirements ?? event?.input ?? event?.payload ?? event?.metadata ?? event?.requirement;
  if (raw == null) return {};
  if (typeof raw === 'string') {
    try { return JSON.parse(raw); } catch { return { _text: raw }; }
  }
  return raw;
}

/** Infer which capability an order is for from the input fields. */
function inferCapability(input: any): Capability | null {
  if (Array.isArray(input?.claims) && input.claims.length) return 'verify_claims';
  if (input?.agent_listing_url) return 'audit_agent_listing';
  if (input?.github_url) return 'audit_repository';
  return null;
}

async function runJob(apiUrl: string, capability: Capability, input: any, maxSeconds: number): Promise<any> {
  const endpoint = CAPABILITY_TO_ENDPOINT[capability];
  const create = await axios.post(`${apiUrl}/jobs/${endpoint}`, input, { timeout: 10_000 });
  const jobId = create.data.job_id;
  console.log(`[JOB] created ${jobId} (${capability})`);

  const deadline = Date.now() + maxSeconds * 1000;
  while (Date.now() < deadline) {
    await sleep(3000);
    try {
      const { data: job } = await axios.get(`${apiUrl}/jobs/${jobId}`, { timeout: 5000 });
      if (job.status === 'done') { console.log(`[JOB] ${jobId} done`); return job; }
      if (job.status === 'failed') throw new Error(job.error ?? 'job failed');
      console.log(`[JOB] ${jobId} ${job.status}...`);
    } catch (err: any) {
      console.warn(`[JOB] poll error:`, err?.message);
    }
  }
  throw new Error(`job ${jobId} timed out after ${maxSeconds}s`);
}

/**
 * Wire the CAP order lifecycle onto the WebSocket stream:
 *   NegotiationCreated -> acceptNegotiation (capture input)
 *   OrderPaid          -> run analysis on the deployed API -> deliverOrder
 *   OrderCompleted     -> log settlement
 */
export function setupOrderHandler(stream: any, client: any, EventType: any, DeliverableType: any): void {
  const apiUrl = process.env.CAPSCORE_API_URL || 'http://localhost:8000';
  const maxSeconds = parseInt(process.env.MAX_JOB_SECONDS || '300', 10);

  stream.on(EventType.NegotiationCreated, async (e: any) => {
    const negotiationId = e?.negotiation_id ?? e?.negotiationId;
    const input = extractInput(e);
    const capability = inferCapability(input);
    console.log(`[ORDER] NegotiationCreated negotiation=${negotiationId} inferredCapability=${capability}`);

    if (!capability) {
      console.warn('[ORDER] Could not infer capability from input; rejecting.');
      try { await client.rejectNegotiation?.(negotiationId, 'Unrecognized request shape'); } catch {}
      return;
    }

    // Best-effort schema validation (non-fatal: schemas have defaults).
    const parsed = CAPABILITY_SCHEMAS[capability].safeParse(input);
    const finalInput = parsed.success ? parsed.data : input;

    try {
      const res = await client.acceptNegotiation(negotiationId);
      const orderId = res?.order?.orderId ?? res?.order?.order_id ?? res?.orderId ?? res?.order_id;
      if (orderId) orderInputs.set(String(orderId), { capability, input: finalInput });
      console.log(`[ORDER] accepted negotiation ${negotiationId} -> order ${orderId}`);
    } catch (err: any) {
      console.error(`[ORDER] acceptNegotiation failed:`, err?.message);
    }
  });

  stream.on(EventType.OrderPaid, async (e: any) => {
    const orderId = String(e?.order_id ?? e?.orderId ?? '');
    console.log(`[ORDER] OrderPaid order=${orderId} — starting analysis`);

    let ctx = orderInputs.get(orderId);
    if (!ctx) {
      // Fallback: re-extract from this event if we lost the mapping (e.g., restart).
      const input = extractInput(e);
      const capability = inferCapability(input);
      if (capability) ctx = { capability, input };
    }
    if (!ctx) { console.error(`[ORDER] No input context for order ${orderId}; cannot deliver.`); return; }

    try {
      const job = await runJob(apiUrl, ctx.capability, ctx.input, maxSeconds);
      await deliverResult(client, orderId, job, DeliverableType);
      orderInputs.delete(orderId);
    } catch (err: any) {
      console.error(`[ORDER] analysis/delivery failed for order ${orderId}:`, err?.message);
    }
  });

  stream.on(EventType.OrderCompleted, (e: any) => {
    console.log(`[ORDER] OrderCompleted (settled) order=${e?.order_id ?? e?.orderId}`);
  });

  console.log('[CROO] Order lifecycle handlers registered (Negotiation→Paid→Deliver→Completed)');
}
