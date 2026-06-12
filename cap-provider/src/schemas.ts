import { z } from 'zod';

export const AuditAgentListingSchema = z.object({
  agent_listing_url: z.string().url(),
  github_url: z.string().url().optional(),
  demo_url: z.string().url().optional(),
  claimed_tracks: z.array(z.string()).optional(),
  depth: z.enum(['quick', 'standard', 'deep']).default('standard'),
});

export const AuditRepositorySchema = z.object({
  github_url: z.string().url(),
  branch: z.string().default('main'),
  run_tests: z.boolean().default(true),
  run_security_scan: z.boolean().default(true),
  expected_start_command: z.string().optional(),
});

export const VerifyClaimsSchema = z.object({
  claims: z.array(z.string()).min(1),
  evidence_urls: z.array(z.string().url()).optional(),
  strictness: z.enum(['lenient', 'standard', 'strict']).default('standard'),
});

export const CAPABILITY_SCHEMAS = {
  audit_agent_listing: AuditAgentListingSchema,
  audit_repository: AuditRepositorySchema,
  verify_claims: VerifyClaimsSchema,
} as const;

export type Capability = keyof typeof CAPABILITY_SCHEMAS;

export const CAPABILITY_METADATA = {
  audit_agent_listing: {
    name: 'Audit Agent Listing',
    description:
      'Audit a CROO Agent Store listing or agent ID. Returns a judging-aligned scorecard, claim verification table, CAP compliance report, and verifiable proof pack.',
    price: '1.00',
    currency: 'USD',
    sla_seconds: 120,
  },
  audit_repository: {
    name: 'Audit Repository',
    description:
      'Reproduce and audit a GitHub repository. Returns reproducibility score, security scan, README analysis, and verifiable proof pack.',
    price: '2.00',
    currency: 'USD',
    sla_seconds: 300,
  },
  verify_claims: {
    name: 'Verify Claims',
    description:
      'Verify claims from a README, listing, or pitch. Returns claim-by-claim verification table with evidence, confidence scores, and suggested rewrites.',
    price: '0.50',
    currency: 'USD',
    sla_seconds: 60,
  },
} as const;
