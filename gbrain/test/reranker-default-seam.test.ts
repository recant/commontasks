/**
 * #3657 reranker-sunset prep — single-constant seam for the legacy default.
 *
 * The sunsetting `zeroentropyai:zerank-2` default must live in exactly ONE
 * code home (`LEGACY_DEFAULT_RERANKER_MODEL` in src/core/ai/defaults.ts) so
 * the September default swap is a one-line change. Everything else resolves
 * through that constant:
 *   - the three mode bundles (src/core/search/mode.ts)
 *   - the gateway runtime fallback (src/core/ai/gateway.ts DEFAULT_RERANKER_MODEL)
 *
 * The literal is allowed to remain in exactly two other NON-DEFAULT code
 * positions, each with a documented reason:
 *   - src/core/embedding-pricing.ts — a pricing-table KEY, not a default
 *   - src/core/retrieval-upgrade-planner.ts — the HISTORICAL v0.36 ZE cutover
 *     target (dormant ze-switch flow; file is deleted wholesale in the v0.47
 *     removal wave). By definition it targets ZE and must not track the seam.
 *
 * Also pins the sunset list (RERANKER_SUNSETS) the doctor search_mode check
 * consults before recommending `gbrain search modes --reset` (#4382).
 */
import { describe, expect, test } from 'bun:test';
import { readdirSync, readFileSync, statSync } from 'fs';
import { join } from 'path';
import { MODE_BUNDLES } from '../src/core/search/mode.ts';
import {
  LEGACY_DEFAULT_RERANKER_MODEL,
  NEW_INSTALL_DEFAULT_RERANKER_MODEL,
  DEFAULT_LOCAL_RERANKER_MODEL,
  RERANKER_SUNSETS,
  ZEROENTROPY_SUNSET_DATE,
  rerankerSunset,
} from '../src/core/ai/defaults.ts';

describe('LEGACY_DEFAULT_RERANKER_MODEL seam (#3657)', () => {
  test('the three hosted mode bundles resolve their reranker_model through the one constant', () => {
    expect(MODE_BUNDLES.conservative.reranker_model).toBe(LEGACY_DEFAULT_RERANKER_MODEL);
    expect(MODE_BUNDLES.balanced.reranker_model).toBe(LEGACY_DEFAULT_RERANKER_MODEL);
    expect(MODE_BUNDLES.tokenmax.reranker_model).toBe(LEGACY_DEFAULT_RERANKER_MODEL);
  });

  test('the slm bundle resolves through the LOCAL constant, never a hosted default', () => {
    // A reranker receives the query AND the candidate document texts, so a
    // hosted default would ship brain content off-machine on every search —
    // disqualifying for the local profile. This is a privacy invariant, not a
    // preference: assert both that it uses the local constant and that it is
    // not any hosted one.
    expect(MODE_BUNDLES.slm.reranker_model).toBe(DEFAULT_LOCAL_RERANKER_MODEL);
    expect(MODE_BUNDLES.slm.reranker_model).not.toBe(LEGACY_DEFAULT_RERANKER_MODEL);
    expect(MODE_BUNDLES.slm.reranker_model).not.toBe(NEW_INSTALL_DEFAULT_RERANKER_MODEL);
    expect(MODE_BUNDLES.slm.reranker_model.startsWith('llama-server-reranker:')).toBe(true);
  });

  test('the slm bundle keeps autocut legitimate by actually enabling the reranker', () => {
    // autocut cuts on the cross-encoder cliff. Enabling it without a reranker
    // is what `conservative` correctly refuses to do. If a future edit turns
    // the reranker off here, autocut must go with it.
    expect(MODE_BUNDLES.slm.autocut).toBe(true);
    expect(MODE_BUNDLES.slm.reranker_enabled).toBe(true);
    // top_n_in must cover the returned slice (the D4 no-unscored-tail
    // invariant), and exceeding it is what lets the cross-encoder promote a
    // chunk from outside the top 6 into the returned set.
    expect(MODE_BUNDLES.slm.reranker_top_n_in).toBeGreaterThanOrEqual(MODE_BUNDLES.slm.searchLimit);
  });

  test('the slm bundle keeps the zero-LLM retrieval arms ON', () => {
    // The whole point of the bundle: graph signals, relational recall and
    // title contextual retrieval cost no tokens and no API calls, and a weak
    // generator needs MORE retrieval quality, not less. Trimming them to save
    // latency (as `conservative` does) is the wrong trade here.
    expect(MODE_BUNDLES.slm.graph_signals).toBe(true);
    expect(MODE_BUNDLES.slm.relationalRetrieval).toBe(true);
    expect(MODE_BUNDLES.slm.contextual_retrieval).toBe('title');
  });

  test('the constant still carries the pre-swap legacy value (this PR prepares, does NOT choose)', () => {
    expect(LEGACY_DEFAULT_RERANKER_MODEL).toBe('zeroentropyai:zerank-2');
  });

  test('gateway DEFAULT_RERANKER_MODEL is assigned from the constant, not a literal', () => {
    const src = readFileSync(
      join(import.meta.dir, '../src/core/ai/gateway.ts'),
      'utf8',
    );
    expect(src).toContain('DEFAULT_RERANKER_MODEL = LEGACY_DEFAULT_RERANKER_MODEL');
  });

  test('the literal has exactly three code homes in src/ (constant, pricing key, historical ZE target)', () => {
    const LITERAL = 'zeroentropyai:zerank-2';
    const ALLOWED = new Set([
      'src/core/ai/defaults.ts', // LEGACY_DEFAULT_RERANKER_MODEL — the seam
      'src/core/embedding-pricing.ts', // pricing-table key, not a default
      'src/core/retrieval-upgrade-planner.ts', // historical ZE cutover target (deleted v0.47)
    ]);
    const root = join(import.meta.dir, '..');
    const hits: string[] = [];
    const walk = (dir: string): void => {
      for (const name of readdirSync(dir)) {
        const full = join(dir, name);
        const st = statSync(full);
        if (st.isDirectory()) {
          walk(full);
        } else if (name.endsWith('.ts')) {
          const rel = full.slice(root.length + 1);
          for (const line of readFileSync(full, 'utf8').split('\n')) {
            if (!line.includes(LITERAL)) continue;
            const t = line.trim();
            // Comment lines are fine — only CODE positions count.
            if (t.startsWith('//') || t.startsWith('*') || t.startsWith('/*')) continue;
            hits.push(rel);
            break;
          }
        }
      }
    };
    walk(join(root, 'src'));
    const offenders = hits.filter((f) => !ALLOWED.has(f));
    expect(offenders).toEqual([]);
    // The seam home itself must carry it (guards against the constant moving
    // without this allowlist being updated).
    expect(hits).toContain('src/core/ai/defaults.ts');
  });
});

describe('RERANKER_SUNSETS (#3657/#4382)', () => {
  test('the legacy default is on the sunset list with the ZE date + a live replacement', () => {
    const s = rerankerSunset(LEGACY_DEFAULT_RERANKER_MODEL);
    expect(s).not.toBeNull();
    expect(s!.date).toBe(ZEROENTROPY_SUNSET_DATE);
    expect(s!.replacement).toBe(NEW_INSTALL_DEFAULT_RERANKER_MODEL);
  });

  test('every ZeroEntropy reranker matches by provider prefix (zerank-1, zerank-1-small too)', () => {
    expect(rerankerSunset('zeroentropyai:zerank-1')?.date).toBe(ZEROENTROPY_SUNSET_DATE);
    expect(rerankerSunset('zeroentropyai:zerank-1-small')?.date).toBe(ZEROENTROPY_SUNSET_DATE);
  });

  test('live rerankers do not match', () => {
    expect(rerankerSunset('voyage:rerank-2.5')).toBeNull();
    expect(rerankerSunset('voyage:rerank-2.5-lite')).toBeNull();
    expect(rerankerSunset('dashscope-rerank:qwen3-rerank')).toBeNull();
    expect(rerankerSunset('llama-server-reranker:qwen3-reranker-4b')).toBeNull();
    expect(rerankerSunset('openrouter:cohere/rerank-v3.5')).toBeNull();
  });

  test('null/undefined/empty are not sunset', () => {
    expect(rerankerSunset(undefined)).toBeNull();
    expect(rerankerSunset(null)).toBeNull();
    expect(rerankerSunset('')).toBeNull();
  });

  test('a replacement must never itself be on the sunset list', () => {
    for (const s of RERANKER_SUNSETS) {
      expect(rerankerSunset(s.replacement)).toBeNull();
    }
  });
});
