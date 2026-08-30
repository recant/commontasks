/**
 * denialRateMart.ts — reporting-mart status mapping + denial-rate computation.
 *
 * Author: Jake Osei (platform) · v2 2026-06-09
 * History: THIS FILE is the site of the May 2026 reporting regression
 * (postmortem 2026-06-10). Release 2026.05.12 renamed the claim-state enum;
 * the v1 mapping's silent default bucketed the new pend states into
 * `denied_other`, overstating May denial rates (Northside: 14.3% vs true 8.2%).
 * v2 rules: every state mapped explicitly, unknown states FAIL LOUD, and the
 * embedded regression check reproduces the incident numbers on every run.
 *
 * Run: node denialRateMart.ts
 */

type MartBucket = "paid" | "denied" | "pend" | "in_process";

interface ClaimRecord {
  claimId: string;
  client: string;
  month: string; // YYYY-MM
  state: string; // internal claim-state enum (post-2026.05.12 names)
}

// ---- v2 mapping: explicit rows, fail-loud default -------------------------
const STATE_MAP_V2: Record<string, MartBucket> = {
  paid: "paid",
  denied_carc: "denied",
  denied_other: "denied",
  pended_payer_request: "pend",
  awaiting_attachment: "pend",
  in_process: "in_process",
  submitted: "in_process",
};

export function mapStateV2(state: string): MartBucket {
  const bucket = STATE_MAP_V2[state];
  if (bucket === undefined) {
    // Postmortem rule: schema drift must be an error, never a silent bucket.
    throw new Error(
      `unknown claim state "${state}" — update STATE_MAP_V2 deliberately ` +
      `(see postmortem 2026-06-10; do NOT add a default branch)`
    );
  }
  return bucket;
}

// ---- v1 mapping (KEPT FOR THE RECORD — the buggy version) -----------------
// Pre-release state names, with the fatal `?? "denied_other"` fallthrough.
// After 2026.05.12 renamed `pended` → `pended_payer_request` etc., every pend
// fell into the default and counted as a denial.
function mapStateV1_buggy(state: string): MartBucket {
  const legacy: Record<string, MartBucket> = {
    paid: "paid",
    denied_carc: "denied",
    pended: "pend",          // ← old name; never matches post-release states
    in_process: "in_process",
  };
  return legacy[state] ?? "denied"; // ← THE BUG: silent default
}

// ---- metric ---------------------------------------------------------------
// Definition (unchanged through the incident): CARC-denied ÷ adjudicated,
// pends and in-process excluded from both numerator and denominator.
export function denialRate(claims: ClaimRecord[], map: (s: string) => MartBucket): number {
  let denied = 0, adjudicated = 0;
  for (const c of claims) {
    const b = map(c.state);
    if (b === "denied") { denied++; adjudicated++; }
    else if (b === "paid") { adjudicated++; }
    // pend / in_process: excluded
  }
  return adjudicated === 0 ? 0 : denied / adjudicated;
}

// ---- regression fixture: Northside, May 2026 ------------------------------
// Reproduces the incident's headline RATES (14.3% buggy vs 8.2% true) from
// TK-1102's 231 true CARC denials. (The ticket's 402 mart-denied count also
// swept in in-process rows the mart double-mapped; not modeled here — the
// rates are the contract this regression protects.)
function northsideMayFixture(): ClaimRecord[] {
  const rows: ClaimRecord[] = [];
  const push = (n: number, state: string) => {
    for (let i = 0; i < n; i++) {
      rows.push({ claimId: `NS-${state}-${i}`, client: "northside-clinic", month: "2026-05", state });
    }
  };
  push(231, "denied_carc");
  push(140, "pended_payer_request");
  push(60, "awaiting_attachment");
  push(2586, "paid");
  return rows;
}

function main(): void {
  const fixture = northsideMayFixture();
  const v2 = denialRate(fixture, mapStateV2);
  const v1 = denialRate(fixture, mapStateV1_buggy);
  console.log(`Northside 2026-05 fixture: ${fixture.length} claims`);
  console.log(`  v2 (correct, pends excluded): ${(v2 * 100).toFixed(1)}%   ← corrected MBR number`);
  console.log(`  v1 (buggy silent default):    ${(v1 * 100).toFixed(1)}%   ← the number that almost shipped`);

  // Release regression check (tolerance mirrors the 0.2% reconciliation test)
  if (Math.abs(v2 - 0.082) > 0.002) throw new Error("regression: v2 rate drifted from 8.2%");
  if (Math.abs(v1 - 0.143) > 0.002) throw new Error("fixture drift: v1 no longer reproduces 14.3%");
  console.log("  ✓ regression check: v2=8.2%, v1 reproduces the 14.3% incident number");

  // Fail-loud demo
  try {
    mapStateV2("pended"); // pre-release name — must throw, not bucket
  } catch (e) {
    console.log(`  ✓ fail-loud works: ${(e as Error).message.split(" — ")[0]}`);
  }
}

main();
