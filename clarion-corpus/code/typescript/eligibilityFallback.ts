/**
 * eligibilityFallback.ts — real-time eligibility with cached fallback + backoff.
 *
 * Author: Jake Osei (platform) · 2026-07-23, ratified permanent 2026-07-28
 * History: INC-2026-007 (Aetna CA rotation, postmortem 2026-07-29). Two
 * lessons are encoded here: (1) the old tight-loop retry amplified load during
 * the outage — replaced with exponential backoff + jitter; (2) the cached-271
 * fallback that saved the afternoon is now a permanent, always-on capability:
 * 24h freshness TTL, mandatory stale labeling, and the hard guardrail that
 * cached data is NEVER a claims-release basis (Priya's caveat, 7/28 review).
 *
 * Run: node eligibilityFallback.ts
 */

interface EligibilityResult {
  memberId: string;
  active: boolean;
  checkedAt: number;     // epoch ms of the underlying 271
  fromCache: boolean;
  staleLabel: string | null; // UI must render this when fromCache
}

interface CacheEntry { active: boolean; checkedAt: number; }

const TTL_HOURS = 24;              // per aetna.yaml fallback.ttl_hours
const RETRY = { baseMs: 400, maxAttempts: 4, jitter: true }; // per aetna.yaml

type LiveChecker = (memberId: string) => Promise<{ active: boolean }>;

const cache = new Map<string, CacheEntry>();

const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

async function withBackoff<T>(fn: () => Promise<T>): Promise<T> {
  let lastErr: unknown;
  for (let attempt = 0; attempt < RETRY.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (e) {
      lastErr = e;
      // Exponential backoff + jitter — the tight loop is what we do NOT do
      // anymore (it hammered Aetna's failing endpoint on 7/21).
      const delay = RETRY.baseMs * 2 ** attempt * (RETRY.jitter ? 0.5 + Math.random() / 2 : 1);
      await sleep(delay);
    }
  }
  throw lastErr;
}

export async function checkEligibility(
  memberId: string, live: LiveChecker, now: number
): Promise<EligibilityResult> {
  try {
    const res = await withBackoff(() => live(memberId));
    cache.set(memberId, { active: res.active, checkedAt: now });
    return { memberId, active: res.active, checkedAt: now, fromCache: false, staleLabel: null };
  } catch {
    const hit = cache.get(memberId);
    const freshEnough = hit && now - hit.checkedAt <= TTL_HOURS * 3600_000;
    if (hit && freshEnough) {
      const ageH = Math.round((now - hit.checkedAt) / 3600_000);
      return {
        memberId, active: hit.active, checkedAt: hit.checkedAt, fromCache: true,
        staleLabel: `CACHED ${ageH}h ago — payer connection degraded`,
      };
    }
    // Outside the TTL: no answer beats a wrong answer. Queue for batch 270.
    throw new Error(`eligibility unavailable for ${memberId} — queued for overnight batch 270`);
  }
}

/** Guardrail: scrub/claims-release requires a LIVE-or-fresh check (SOP-001). */
export function usableForClaimsRelease(r: EligibilityResult): boolean {
  return !r.fromCache;
}

// ---- demo: a compressed INC-2026-007 --------------------------------------
async function main(): Promise<void> {
  const T0 = Date.parse("2026-07-21T08:00:00-04:00");
  let payerUp = true;
  const aetnaLive: LiveChecker = async (id) => {
    if (!payerUp) throw new Error("mTLS handshake failure (unknown intermediate CA)");
    return { active: !id.endsWith("9") }; // deterministic toy adjudication
  };

  console.log("08:00 — healthy: live checks populate the cache");
  for (const id of ["M0031877", "M0044120", "M0090319"]) {
    const r = await checkEligibility(id, aetnaLive, T0);
    console.log(`  ${id}: active=${r.active} fromCache=${r.fromCache}`);
  }

  console.log("09:14 — Aetna rotates its intermediate CA: live checks fail");
  payerUp = false;
  const T1 = Date.parse("2026-07-21T09:14:00-04:00");
  const r = await checkEligibility("M0031877", aetnaLive, T1);
  console.log(`  M0031877: active=${r.active} fromCache=${r.fromCache} label="${r.staleLabel}"`);
  console.log(`  usable for claims release? ${usableForClaimsRelease(r)} (guardrail: cached ≠ scrub)`);

  try {
    await checkEligibility("M0055555", aetnaLive, T1); // never cached → must queue
  } catch (e) {
    console.log(`  M0055555: ${(e as Error).message}`);
  }

  const T2 = T1 + (TTL_HOURS + 2) * 3600_000;
  try {
    await checkEligibility("M0031877", aetnaLive, T2); // cache older than TTL → queue
  } catch {
    console.log(`  +${TTL_HOURS + 2}h: cache expired past ${TTL_HOURS}h TTL → queued, not served stale`);
  }
  console.log("✓ fallback serves labeled cache inside TTL, refuses beyond it, never releases claims");
}

main();
