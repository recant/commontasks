/**
 * Clarion benchmark runner — retrieval-only, no model required.
 *
 * Scores the 60-item benchmark at SOURCE-DOCUMENT granularity, which is the
 * only granularity the two conditions share:
 *   - `gold_evidence` names CLAIM ids; each claim carries a `source_id`.
 *   - Condition B (naive RAG) retrieves claims via FTS5 -> source_id directly.
 *   - Condition A (gbrain) retrieves PAGES; source docs import to the slug
 *     `sources/<type>/<name>`, which maps back to a source_id via frontmatter.
 * Comparing at doc level is therefore apples-to-apples; comparing A's pages to
 * B's claims directly would not be.
 *
 * Entity pages (people/, clients/, topics/) can never be gold hits because no
 * claim is anchored to them. That is deliberate: gold_evidence is "the evidence
 * needed to answer", and the graph's job is to help FIND the right source docs,
 * not to substitute for them.
 */
import { readFileSync, readdirSync, statSync } from 'fs';
import { join, relative } from 'path';
import { Database } from 'bun:sqlite';
import { createEngine } from '../gbrain/src/core/engine-factory.ts';
import { loadConfig, toEngineConfig } from '../gbrain/src/core/config.ts';
import { connectWithRetry } from '../gbrain/src/core/db.ts';
import { configureGateway } from '../gbrain/src/core/ai/gateway.ts';
import { buildGatewayConfig } from '../gbrain/src/core/ai/build-gateway-config.ts';
import { handleToolCall } from '../gbrain/src/mcp/server.ts';

const CORPUS = '/home/user/commontasks/clarion-corpus';
const K = Number(process.env.BENCH_K ?? 10);

/** Walk the corpus and map frontmatter `id: srcNNN` -> gbrain page slug. */
function buildSourceIndex(): Map<string, string> {
  const map = new Map<string, string>();
  const walk = (dir: string): void => {
    for (const e of readdirSync(dir)) {
      const p = join(dir, e);
      if (statSync(p).isDirectory()) { walk(p); continue; }
      if (!e.endsWith('.md')) continue;
      const head = readFileSync(p, 'utf8').slice(0, 400);
      const m = head.match(/^id:\s*(\S+)/m);
      if (!m) continue;
      map.set(m[1], relative(CORPUS, p).replace(/\.md$/, ''));
    }
  };
  walk(join(CORPUS, 'sources'));
  return map;
}

interface Scored { p: number; r: number; hit: number; gold: number; n: number }
function score(retrieved: string[], gold: Set<string>): Scored {
  const top = retrieved.slice(0, K);
  const hit = top.filter((s) => gold.has(s)).length;
  // Precision denominator is the ACTUAL returned count, not k: `slm` caps at
  // searchLimit 6 and autocut trims further, so dividing by a fixed k would
  // flatter it for simply returning less. Mean `n` is reported alongside so the
  // precision figures stay interpretable.
  return { p: top.length ? hit / top.length : 0, r: gold.size ? hit / gold.size : 0, hit, gold: gold.size, n: top.length };
}

const bench = JSON.parse(readFileSync(join(CORPUS, 'benchmark.json'), 'utf8'));
const claims = JSON.parse(readFileSync(join(CORPUS, 'claims.json'), 'utf8')) as Array<{ id: string; source_id: string }>;
const claimSource = new Map(claims.map((c) => [c.id, c.source_id]));
const srcSlug = buildSourceIndex();

// Mirrors cli.ts:connectEngine — gateway first (initSchema needs embed dims),
// then engine create + connect. Keyless: no provider key is configured.
const cfg = loadConfig();
if (!cfg) throw new Error('no gbrain config found — is GBRAIN_BRAIN_PATH set?');
configureGateway(buildGatewayConfig(cfg));
const engine = await createEngine(toEngineConfig(cfg));
await connectWithRetry(engine, toEngineConfig(cfg), { noRetry: true });
const db = new Database(join(CORPUS, 'clarion.db'), { readonly: true });

/** Condition B: FTS5 over claims, exactly what build_db.py indexes. */
function conditionB(q: string): string[] {
  const terms = q.replace(/[^\w\s]/g, ' ').split(/\s+/).filter((t) => t.length > 2);
  if (!terms.length) return [];
  const match = terms.map((t) => `"${t}"`).join(' OR ');
  try {
    const rows = db.query(
      `SELECT c.source_id FROM claims_fts f JOIN claims c ON c.rowid=f.rowid
       WHERE claims_fts MATCH ? ORDER BY rank LIMIT ?`,
    ).all(match, K * 3) as Array<{ source_id: string }>;
    return [...new Set(rows.map((r) => srcSlug.get(r.source_id)).filter(Boolean) as string[])];
  } catch { return []; }
}

/** Condition A: gbrain hybrid retrieval through the production op layer. */
async function conditionA(q: string, mode: string): Promise<string[]> {
  const res = await handleToolCall(engine, 'search', { query: q, limit: K * 3, mode }) as any;
  const rows = res?.results ?? res ?? [];
  return [...new Set(rows.map((r: any) => r.slug).filter(Boolean))];
}

const MODES = (process.env.BENCH_MODES ?? 'slm,balanced').split(',');
const agg: Record<string, { p: number[]; r: number[]; n: number[] }> = {};
const byType: Record<string, Record<string, number[]>> = {};
const put = (cond: string, t: string, s: Scored) => {
  (agg[cond] ??= { p: [], r: [], n: [] }).p.push(s.p);
  agg[cond].r.push(s.r);
  agg[cond].n.push(s.n);
  ((byType[t] ??= {})[cond] ??= []).push(s.r);
};

for (const item of bench.items) {
  const gold = new Set(
    (item.gold_evidence as string[])
      .map((c) => srcSlug.get(claimSource.get(c) ?? '') ?? null)
      .filter(Boolean) as string[],
  );
  if (!gold.size) { console.error(`! no gold slugs for ${item.id}`); continue; }
  put('B (naive RAG)', item.query_type, score(conditionB(item.question), gold));
  for (const m of MODES) {
    put(`A (gbrain ${m})`, item.query_type, score(await conditionA(item.question, m), gold));
  }
}

const mean = (a: number[]) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);
const pct = (n: number) => (n * 100).toFixed(1).padStart(5);

console.log(`\n=== Clarion benchmark — retrieval @k=${K}, ${bench.items.length} items, source-doc granularity ===\n`);
console.log(`${'condition'.padEnd(22)} ${'P@k'.padStart(6)} ${'R@k'.padStart(6)} ${'avg #ret'.padStart(9)}`);
for (const [cond, v] of Object.entries(agg)) {
  console.log(`${cond.padEnd(22)} ${pct(mean(v.p))} ${pct(mean(v.r))} ${mean(v.n).toFixed(1).padStart(9)}`);
}
const conds = Object.keys(agg);
console.log(`\n--- Recall@${K} by query type ---`);
console.log(`${'type'.padEnd(14)} ${conds.map((c) => c.slice(0, 16).padStart(17)).join('')}`);
for (const t of Object.keys(byType).sort()) {
  console.log(`${t.padEnd(14)} ${conds.map((c) => pct(mean(byType[t][c] ?? [])).padStart(17)).join('')}`);
}
await engine.close?.();
