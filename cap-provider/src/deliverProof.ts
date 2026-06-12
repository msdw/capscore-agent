import axios from 'axios';

export async function deliverProof(
  client: any,
  orderId: string,
  jobResult: any,
  apiUrl: string
): Promise<void> {
  const jobId: string = jobResult.job_id;
  const resultHash: string = jobResult.result_hash || '';
  const publicBase = process.env.CAPSCORE_PUBLIC_BASE_URL || apiUrl;
  const proofPackUrl = `${publicBase}/jobs/${jobId}/proof-pack.zip`;

  console.log(`[PROOF] Preparing delivery for order=${orderId} job=${jobId}`);

  // --- Download proof pack ---
  let zipBuffer: Buffer | null = null;
  try {
    const resp = await axios.get(`${apiUrl}/jobs/${jobId}/proof-pack.zip`, {
      responseType: 'arraybuffer',
      timeout: 30_000,
    });
    zipBuffer = Buffer.from(resp.data as ArrayBuffer);
    console.log(`[PROOF] Downloaded proof pack for job ${jobId}: ${zipBuffer.length} bytes`);
  } catch (err: any) {
    console.warn(`[PROOF] Could not download proof pack for job ${jobId}:`, err?.message);
  }

  // --- Upload proof pack to CROO ---
  if (zipBuffer !== null && typeof client.uploadFile === 'function') {
    try {
      await client.uploadFile(`proof-pack-${jobId}.zip`, zipBuffer);
      console.log(`[PROOF] Uploaded proof pack for order ${orderId}`);
    } catch (err: any) {
      console.warn(`[PROOF] Upload failed for order ${orderId}:`, err?.message);
    }
  } else if (zipBuffer === null) {
    console.warn(`[PROOF] Skipping upload — proof pack not available for job ${jobId}`);
  } else {
    console.warn(`[PROOF] client.uploadFile is not available — skipping upload`);
  }

  // --- Deliver order ---
  const deliverable = {
    deliverableType: 'json',
    deliverableText: JSON.stringify({
      job_id: jobId,
      result_hash: resultHash,
      proof_pack_url: proofPackUrl,
      overall_score: jobResult.scorecard?.overall_score ?? null,
      status: 'delivered',
    }),
  };

  try {
    await client.deliverOrder(orderId, deliverable);
    console.log(`[PROOF] Delivered order ${orderId} with result_hash=${resultHash}`);
  } catch (err: any) {
    console.error(`[PROOF] deliverOrder failed for order ${orderId}:`, err?.message);
  }
}
