/**
 * Multi-Query Expansion — v0.14+ delegates LLM call to the AI gateway.
 *
 * Sanitization layer (prompt-injection defense) stays HERE, not in the gateway:
 * the gateway is provider-agnostic; sanitization is gbrain's responsibility.
 *
 * Security (Fix 3 / M1 / M2 / M3):
 *   - sanitizeQueryForPrompt() strips injection patterns from user input
 *   - sanitizeExpansionOutput() validates LLM output before it reaches search
 *   - console.warn never logs the query text itself (privacy)
 */

import { expand as gatewayExpand, isAvailable as gatewayIsAvailable } from '../ai/gateway.ts';
import { countCJKAwareWords } from '../cjk.ts';
import { isLocalOnlyProfile } from '../model-config.ts';

const MAX_QUERIES = 3;
const MIN_WORDS = 3;
const MAX_QUERY_CHARS = 500;

/**
 * Expansion width for the local/SLM profile.
 *
 * A small model's paraphrases cluster much more tightly around the original
 * query than a Haiku-class model's do, so each variant recovers fewer true
 * synonym misses. Widening the variant count buys back some of that lost
 * recall — the fan-out is cheap on the retrieval side (extra SQL arms fused by
 * RRF), and recall is precisely what a weak generator cannot compensate for
 * with reasoning.
 *
 * `MAX_QUERIES_LOCAL` counts the ORIGINAL query plus alternatives, matching
 * MAX_QUERIES above (5 = original + 4), so the two constants stay consistent.
 */
const MAX_QUERIES_LOCAL = 5;
const MAX_ALTERNATIVES = 2;
const MAX_ALTERNATIVES_LOCAL = 4;

/**
 * Resolve expansion width from the active profile.
 *
 * Read from the environment rather than threaded through `expandQuery`'s
 * signature: every caller (ops/search.ts, eval-longmemeval.ts) passes only a
 * query string, and widening that signature would touch call sites for a knob
 * that is a deployment property, not a per-call one.
 *
 * Gating on the local profile rather than on `search.mode === 'slm'` is correct
 * in every combination that can actually occur: expansion is only ON in
 * `tokenmax` and `slm`. tokenmax on a cloud model keeps 3/2; slm (always local)
 * gets 5/4; and tokenmax under GBRAIN_LOCAL_ONLY also gets 5/4, which is right
 * for the same weak-paraphrase reason.
 */
function expansionWidth(): { maxQueries: number; maxAlternatives: number } {
  return isLocalOnlyProfile()
    ? { maxQueries: MAX_QUERIES_LOCAL, maxAlternatives: MAX_ALTERNATIVES_LOCAL }
    : { maxQueries: MAX_QUERIES, maxAlternatives: MAX_ALTERNATIVES };
}

/**
 * Defense-in-depth sanitization for user queries before they reach the LLM.
 */
export function sanitizeQueryForPrompt(query: string): string {
  const original = query;
  let q = query;
  if (q.length > MAX_QUERY_CHARS) q = q.slice(0, MAX_QUERY_CHARS);
  q = q.replace(/```[\s\S]*?```/g, ' ');
  q = q.replace(/<\/?[a-zA-Z][^>]*>/g, ' ');
  q = q.replace(/^(\s*(ignore|forget|disregard|override|system|assistant|human)[\s:]+)+/gi, '');
  q = q.replace(/\s+/g, ' ').trim();
  if (q !== original) {
    console.warn('[gbrain] sanitizeQueryForPrompt: stripped content from user query before LLM expansion');
  }
  return q;
}

/**
 * Validate LLM-produced alternative queries. LLM output is untrusted.
 */
export function sanitizeExpansionOutput(
  alternatives: unknown[],
  maxAlternatives: number = expansionWidth().maxAlternatives,
): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of alternatives) {
    if (typeof raw !== 'string') continue;
    let s = raw.replace(/[\x00-\x1f\x7f]/g, '').trim();
    if (s.length === 0) continue;
    if (s.length > MAX_QUERY_CHARS) s = s.slice(0, MAX_QUERY_CHARS);
    const key = s.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(s);
    if (out.length >= maxAlternatives) break;
  }
  return out;
}

export async function expandQuery(query: string): Promise<string[]> {
  if (countCJKAwareWords(query) < MIN_WORDS) return [query];

  // Skip LLM call entirely if gateway has no expansion provider configured.
  if (!gatewayIsAvailable('expansion')) return [query];

  try {
    const sanitized = sanitizeQueryForPrompt(query);
    if (sanitized.length === 0) return [query];

    // gateway.expand() returns [original + expansions]. We feed it the sanitized
    // copy so the LLM channel is safe; the ORIGINAL query remains the first entry
    // for downstream search (gateway.expand includes the query it was called with).
    const gatewayResults = await gatewayExpand(sanitized);

    // Resolved once per call so the alternative cap and the final slice can
    // never disagree about how wide this profile expands.
    const width = expansionWidth();

    // Validate LLM-produced alternatives (everything after the first entry).
    const alternatives = gatewayResults.slice(1);
    const sanitizedAlts = sanitizeExpansionOutput(alternatives, width.maxAlternatives);

    // Original query + sanitized alternatives, deduped, capped at maxQueries.
    const all = [query, ...sanitizedAlts];
    const unique = [...new Set(all.map(q => q.toLowerCase().trim()))];
    return unique.slice(0, width.maxQueries).map(q =>
      all.find(orig => orig.toLowerCase().trim() === q) || q,
    );
  } catch {
    return [query];
  }
}
