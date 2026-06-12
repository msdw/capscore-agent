# CAPScore Agent — 5-Minute Demo Script

**Event:** CROO Hackathon 2026 Demo Day
**Duration:** 5 minutes
**Format:** Live screen share + narration

---

## Pre-Demo Checklist

- [ ] Docker stack running: `docker compose up --build`
- [ ] Browser open at http://localhost:8080
- [ ] Terminal ready with `curl` commands
- [ ] Sample GitHub URL ready: `https://github.com/CROO-Network/capscore-agent`
- [ ] `examples/` folder open in file manager

---

## [0:00–0:30] Hook — The Trust Gap Problem

**Screen:** Browser showing Agent Store with multiple agent listings

**Say:**
> "You're a judge at CROO Hackathon. 50 agents are submitted. Each one claims: 'Full CAP integration. Working demo. One-command setup.' How do you know which ones are actually true? Right now, you don't. You have to click every link, clone every repo, read every README. That's the trust gap. CAPScore closes it."

**Action:** Switch to CAPScore frontend at localhost:8080

---

## [0:30–1:30] Audit Repository — Live Demo (Criterion 1: Technical Execution)

**Screen:** CAPScore frontend, "Audit Repository" tab

**Say:**
> "Let me show you the simplest case first. I'll audit this very repo — CAPScore auditing itself."

**Action:** Type in GitHub URL field:
```
https://github.com/CROO-Network/capscore-agent
```
Check "Run Tests" and "Security Scan". Click **Submit Audit**.

**Say:**
> "The backend immediately creates a job and starts four workers in parallel: repo reproducer, CAP inspector, security scanner, and readme rewriter. Each one is a focused expert. Watch the spinner."

**Screen:** Show spinning status. After ~10 seconds (mock mode), results appear.

**Say:**
> "84 out of 100. Let me walk you through the scorecard."

**Action:** Point to each colored progress bar:
- Technical Execution: 85 — "12 of 14 checks: README, docker-compose, .env.example, CI, Dockerfile — all present."
- A2A Composability: 85 — "CAP schema registered, callable by agents, typed inputs, pricing defined."

---

## [1:30–2:30] Proof Pack — The Killer Feature (Criterion 3: Innovation)

**Screen:** Scorecard results, scroll to "Critical Issues" and "Top Fixes"

**Say:**
> "Here's what no other agent at this hackathon does: a tamper-evident proof pack."

**Action:** Click "Download Proof Pack" button.

**Say:**
> "Every result ships as a ZIP with a SHA-256 hash chain. I can verify this proof independently — no trust required."

**Action:** Open terminal. Run:
```bash
cd ~/Downloads
unzip proof-pack-capscore_*.zip
cat result_hash.sha256
```

**Show output:**
```
sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

**Say:**
> "That hash is computed from canonical JSON. Change one character in the scorecard, the hash breaks. This is cryptographic accountability for agent claims."

---

## [2:30–3:30] A2A Composability — Calling Other Agents (Criterion 2: A2A Composability)

**Screen:** Scroll down to "A2A Calls" section in the result

**Say:**
> "CAPScore doesn't just expose capabilities — it uses them. During that audit, CAPScore placed three CAP orders to sub-agents."

**Action:** Point to the A2A calls table:
- `source-verifier-mock` → 7 seconds → cleared
- `security-scanner-mock` → 90 seconds → cleared  
- `readme-rewriter-mock` → 60 seconds → cleared

**Say:**
> "Each call has its own `result_hash`. These are logged in `manifest.json` inside the proof pack — a provenance chain from buyer order all the way down."

**Action:** Open terminal:
```bash
cat manifest.json | python3 -m json.tool | grep -A 5 '"a2a_calls"'
```

**Say:**
> "Any other agent can call CAPScore the same way. One line of CROO SDK code."

**Action:** Show `cap-provider/src/orderHandler.ts` briefly, highlight the `placeOrder` call.

---

## [3:30–4:15] Verify Claims — For Hackathon Judges (Criterion 5: Presentation Readiness)

**Screen:** Switch to "Verify Claims" tab in frontend

**Say:**
> "Here's the killer use case for judges. Paste in any claims from a submission."

**Action:** Type claims:
```
This agent provides a working CAP provider.
Docker Compose starts the stack with one command.
The README setup works in under 10 minutes.
```

Add evidence URL: `https://github.com/CROO-Network/capscore-agent`

Click **Submit**.

**Say:**
> "Claude reads the actual repo and verifies each claim. 30 seconds."

**Show result:**
- Claim 1: ✓ supported (92%)
- Claim 2: ✓ supported (88%)  
- Claim 3: ~ weak (65%) — "First-time Docker pull may take longer"

**Say:**
> "Not just pass/fail — confidence scores, evidence citations, and suggested rewrites. This is what honest due diligence looks like."

---

## [4:15–4:45] Adoption Readiness — It's Already on the Agent Store (Criterion 4: Adoption Readiness)

**Screen:** Switch to Leaderboard section

**Say:**
> "CAPScore is already registered on the CROO Agent Store with three capabilities. Any agent in the ecosystem can call it right now."

**Action:** Show terminal:
```bash
# Any agent calls CAPScore via CROO SDK
cat examples/sample_order_audit_repository.json
curl -s -X POST http://localhost:8000/jobs/audit-repository \
  -H "Content-Type: application/json" \
  -d @examples/sample_order_audit_repository.json | jq .job_id
```

**Say:**
> "Five commands to run the full stack. One command to audit any repo in the ecosystem."

---

## [4:45–5:00] Close — Infrastructure, Not Just a Tool

**Screen:** Return to frontend leaderboard showing jobs list

**Say:**
> "CAPScore is not just a useful agent — it's a verification primitive for the agent economy itself. Wherever agents make claims, CAPScore can verify them. Wherever value is exchanged, CAPScore can provide the proof. 

> The trust gap is real. We built the tool to close it. Thank you."

---

## Backup Commands (if live demo fails)

```bash
# Start stack manually
docker compose up --build

# Quick health check
curl http://localhost:8000/health

# Submit audit via CLI
curl -s -X POST http://localhost:8000/jobs/audit-repository \
  -H "Content-Type: application/json" \
  -d '{"github_url":"https://github.com/CROO-Network/capscore-agent","run_tests":false}' \
  | python3 -m json.tool

# Show pre-run sample result
cat examples/sample_result.json | python3 -m json.tool | head -40

# Show sample proof pack contents
# (pre-built proof pack in examples/)
unzip -l examples/sample_proof_pack.zip 2>/dev/null || echo "See examples/sample_result.md"
```

---

## Judging Criteria Coverage Map

| Criterion | Demo Segment | Evidence Shown |
|---|---|---|
| Technical Execution (30%) | 0:30–1:30 | Live repo audit; 12/14 checks; CI badge |
| A2A Composability (25%) | 2:30–3:30 | 3 sub-agent calls; CAP schema; CROO SDK snippet |
| Innovation (20%) | 1:30–2:30 | SHA-256 proof pack; hash verification; chain of provenance |
| Adoption Readiness (15%) | 4:15–4:45 | Agent Store listing; 3 capabilities; curl demo |
| Presentation Readiness (10%) | 3:30–4:15 | Claim verification table; confidence scores; suggested rewrites |
