import { CAPABILITY_METADATA, CAPABILITY_SCHEMAS } from './schemas';

/**
 * In CROO CAP, services (capabilities + pricing + SLA + requirement schema) are
 * configured in the dashboard (https://agent.croo.network → Configure → + Add Service),
 * NOT via an SDK call. There is no client.registerCapability().
 *
 * This prints the exact service config to enter in the dashboard so the listing
 * matches the input schemas this provider routes on.
 */
export function printServiceConfig(): void {
  console.log('\n[CONFIG] Configure these 3 services in the CROO dashboard (agent.croo.network → Configure):');
  for (const [id, meta] of Object.entries(CAPABILITY_METADATA)) {
    const schema = (CAPABILITY_SCHEMAS as any)[id];
    const fields = schema?.shape ? Object.keys(schema.shape) : [];
    console.log(
      `  • ${meta.name}\n` +
      `      price: $${meta.price} ${meta.currency} | SLA: ${Math.round(meta.sla_seconds / 60)}m | deliverable: Text (JSON)\n` +
      `      requirement fields: ${fields.join(', ') || '(see schemas.ts)'}`,
    );
  }
  console.log('[CONFIG] Services auto-activate on save and become discoverable in the Agent Store.\n');
}
