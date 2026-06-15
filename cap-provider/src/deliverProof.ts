import axios from 'axios';

/**
 * Deliver an order result through CAP.
 *
 * The CROO protocol records the keccak256 hash of the deliverable on-chain
 * automatically during deliverOrder — no manual proof field is needed. We still
 * embed our scorecard summary + internal SHA-256 result hash + proof-pack URL
 * inside the deliverable text so buyers get a rich, independently verifiable
 * payload. We also best-effort upload the proof-pack ZIP when the SDK supports it.
 */
export async function deliverResult(
  client: any,
  orderId: string,
  job: any,
  DeliverableType: any,
): Promise<void> {
  const apiUrl = process.env.CAPSCORE_API_URL || 'http://localhost:8000';
  const publicBase = process.env.CAPSCORE_PUBLIC_BASE_URL || apiUrl;
  const jobId: string = job.job_id;

  // Best-effort: attach the full proof-pack ZIP if the SDK exposes uploadFile.
  if (typeof client.uploadFile === 'function') {
    try {
      const resp = await axios.get(`${apiUrl}/jobs/${jobId}/proof-pack.zip`, {
        responseType: 'arraybuffer',
        timeout: 30_000,
      });
      await client.uploadFile(`proof-pack-${jobId}.zip`, Buffer.from(resp.data as ArrayBuffer));
      console.log(`[DELIVER] uploaded proof pack for ${jobId}`);
    } catch (err: any) {
      console.warn(`[DELIVER] proof-pack upload skipped:`, err?.message);
    }
  }

  const deliverable = {
    capability: job.capability,
    job_id: jobId,
    overall_score: job.scorecard?.overall_score,
    scores: {
      technical_execution: job.scorecard?.technical_execution?.score,
      a2a_composability: job.scorecard?.a2a_composability?.score,
      innovation: job.scorecard?.innovation?.score,
      adoption_readiness: job.scorecard?.adoption_readiness?.score,
      presentation_readiness: job.scorecard?.presentation_readiness?.score,
    },
    critical_issues: job.scorecard?.critical_issues ?? [],
    top_fixes: job.scorecard?.top_fixes ?? [],
    result_hash: job.result_hash,
    a2a_calls: (job.a2a_calls ?? []).length,
    proof_pack_url: `${publicBase}/jobs/${jobId}/proof-pack.zip`,
    report_url: `${publicBase}/jobs/${jobId}/result.md`,
  };

  const textType = DeliverableType?.Text ?? 'text';
  try {
    await client.deliverOrder(orderId, {
      deliverableType: textType,
      deliverableText: JSON.stringify(deliverable),
    });
    console.log(`[DELIVER] order ${orderId} delivered (score=${deliverable.overall_score}, hash=${job.result_hash})`);
  } catch (err: any) {
    console.error(`[DELIVER] deliverOrder failed for ${orderId}:`, err?.message);
    throw err;
  }
}
