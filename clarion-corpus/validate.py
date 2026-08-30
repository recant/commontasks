#!/usr/bin/env python3
"""validate.py — referential-integrity and consistency checks for the Clarion corpus.

Hard requirements (spec §7.7): JSON valid; every edge endpoint exists; every
claim.source_id exists; every anchor resolves; every benchmark gold-evidence id
exists. Plus scenario guards (S7 must stay unresolved, honeypot wiring, gaps,
temporal sanity, wikilink resolution, benchmark shape).

Usage: python3 validate.py   (exit 0 = pass)
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TODAY = "2026-08-30"
errors, warnings = [], []
def err(msg): errors.append(msg)
def warn(msg): warnings.append(msg)

def load(name):
    try:
        return json.loads((ROOT / name).read_text(encoding="utf-8"))
    except Exception as e:
        err(f"{name}: JSON parse failed: {e}")
        return None

reg = load("entities.json")
claims = load("claims.json")
graph = load("graph_seed.json")
bench = load("benchmark.json")
if errors:
    print("\n".join(errors)); sys.exit(1)

people = {p["id"] for p in reg["people"]}
topics = {t["id"] for t in reg["topics"]}
sources = {s["id"]: s for s in reg["sources"]}

# ---- registry ----
if len(reg["sources"]) != 60:
    err(f"registry has {len(reg['sources'])} sources, expected 60")
raws = {}
for s in reg["sources"]:
    p = ROOT / s["path"]
    if not p.exists():
        err(f"{s['id']}: file missing: {s['path']}"); continue
    raw = p.read_text(encoding="utf-8")
    raws[s["id"]] = raw
    m = re.search(r"^id:\s*(\S+)\s*$", raw, re.M)
    if not m or m.group(1) != s["id"]:
        err(f"{s['id']}: frontmatter id mismatch in {s['path']}")
    if f"date: {s['date']}" not in raw:
        err(f"{s['id']}: frontmatter date != registry date {s['date']}")
    if s["date"] > TODAY:
        err(f"{s['id']}: source dated after today ({s['date']})")

# ---- claims ----
claim_by_id = {}
for c in claims:
    cid = c["id"]
    if cid in claim_by_id:
        err(f"duplicate claim id {cid}")
    claim_by_id[cid] = c
    sid = c["source_id"]
    if sid not in sources:
        err(f"{cid}: unknown source_id {sid}"); continue
    if not cid.startswith(f"clm_{sid}_"):
        err(f"{cid}: id does not match source {sid}")
    if c["speaker"] not in people:
        err(f"{cid}: unknown speaker {c['speaker']}")
    if c["date"] != sources[sid]["date"]:
        err(f"{cid}: claim date {c['date']} != source date {sources[sid]['date']}")
    for t in c["topics"]:
        if t not in topics:
            err(f"{cid}: unknown topic {t}")
    raw = raws.get(sid, "")
    quote, line = c["anchor"]["quote"], c["anchor"]["line"]
    if quote not in raw:
        err(f"{cid}: anchor quote not found in source: {quote[:60]!r}")
    else:
        lines = raw.splitlines()
        if not (1 <= line <= len(lines)) or quote not in lines[line - 1]:
            err(f"{cid}: anchor line {line} does not contain the quote")

# ---- graph ----
node_ids = set()
for n in graph["nodes"]:
    if n["id"] in node_ids:
        err(f"duplicate node id {n['id']}")
    node_ids.add(n["id"])
for cid in claim_by_id:
    if cid not in node_ids:
        err(f"claim {cid} missing from graph nodes")
edge_types = {"speaker_of","from_source","about","asked","answered","resolves",
              "supports","contradicts","supersedes","expert_in","mentions",
              "decided_in","justified_by","promised_in","owned_by","derived_from",
              "involves","precedes"}
sup_edges, contra_edges, resolves_targets = [], [], set()
touched_by_supersedes = set()
for e in graph["edges"]:
    if e["src"] not in node_ids: err(f"edge src missing: {e['src']} ({e['type']})")
    if e["dst"] not in node_ids: err(f"edge dst missing: {e['dst']} ({e['type']})")
    if e["type"] not in edge_types: err(f"unknown edge type {e['type']}")
    if e["type"] == "supersedes":
        sup_edges.append(e); touched_by_supersedes.update([e["src"], e["dst"]])
    if e["type"] == "contradicts": contra_edges.append(e)
    if e["type"] == "resolves": resolves_targets.add(e["dst"])

# supersedes: newer -> older, older must be status=superseded, scope required
for e in sup_edges:
    a, b = claim_by_id.get(e["src"]), claim_by_id.get(e["dst"])
    if not a or not b:
        err(f"supersedes edge on non-claims: {e['src']}->{e['dst']}"); continue
    if a["date"] < b["date"]:
        err(f"supersedes direction wrong (src older): {e['src']}->{e['dst']}")
    if b["status"] != "superseded":
        err(f"superseded target {e['dst']} has status {b['status']}")
    if a["status"] != "current":
        err(f"superseding claim {e['src']} not current")
    if not e["props"].get("scope"):
        err(f"supersedes edge missing scope: {e['src']}->{e['dst']}")

# every superseded claim is the target of a supersedes edge
sup_targets = {e["dst"] for e in sup_edges}
for cid, c in claim_by_id.items():
    if c["status"] == "superseded" and cid not in sup_targets:
        err(f"{cid} is status=superseded but no supersedes edge points at it")

# ---- S7 guard: the attachment disagreement must be unresolved ----
s7 = ["clm_src034_02", "clm_src034_03", "clm_src035_02", "clm_src035_03"]
for cid in s7:
    c = claim_by_id.get(cid)
    if not c: err(f"S7 claim missing: {cid}")
    elif c["status"] != "current": err(f"S7 claim {cid} must be current, is {c['status']}")
    if cid in touched_by_supersedes:
        err(f"S7 claim {cid} touched by a supersedes edge — the debate must stay unresolved")
live = [e for e in contra_edges if e["props"].get("resolution") == "unresolved"]
if len(live) < 1: err("no unresolved contradicts edge found (S7 requires >=1)")
resolved = [e for e in contra_edges if e["props"].get("resolution") == "resolved"]
if len(resolved) < 1: err("no resolved contradicts edge found (spec requires >=1)")

# honeypot wiring: the spec's exact pair
if not any(e["src"] == "clm_src014_02" and e["dst"] == "clm_src003_04" for e in sup_edges):
    err("missing honeypot supersedes edge clm_src014_02 -> clm_src003_04")

# ---- questions / gaps ----
q_by_id = {q["id"]: q for q in reg["questions"]}
ask_counts = {}
for e in graph["edges"]:
    if e["type"] == "asked":
        ask_counts[e["dst"]] = ask_counts.get(e["dst"], 0) + 1
for n in graph["nodes"]:
    if n["type"] == "question":
        if n["props"]["ask_count"] != ask_counts.get(n["id"], 0):
            err(f"{n['id']}: ask_count {n['props']['ask_count']} != asked edges {ask_counts.get(n['id'],0)}")
freq = [q for q in reg["questions"]
        if len(q["asks"]) >= 3 and len({a["person"] for a in q["asks"]}) >= 3]
if len(freq) < 3: err(f"only {len(freq)} questions asked >=3x by >=3 distinct people (need >=3)")
for g in reg["gaps"]:
    q = g.get("question")
    if q in ("q_anthem_mod59", "q_retro_elig", "q_attach_strategy") and q in resolves_targets:
        err(f"gap question {q} has a resolving doc — gap invalidated")
if len(reg["gaps"]) < 3: err("fewer than 3 seeded gaps")

# ---- action items ----
statuses = [a["status"] for a in reg["action_items"]]
if len(reg["action_items"]) < 10: err("fewer than 10 action items")
for st in ("done", "open", "overdue"):
    if st not in statuses: err(f"no action item with status {st}")
for a in reg["action_items"]:
    if a["owner"] not in people: err(f"{a['id']}: unknown owner")
    if a["status"] == "overdue" and a["due"] >= TODAY:
        err(f"{a['id']}: marked overdue but due {a['due']} >= today")
    if a["status"] == "open" and a["due"] < TODAY:
        warn(f"{a['id']}: open with past due date {a['due']} (should it be overdue?)")

# ---- benchmark ----
items = bench["items"]
if len(items) != 60: err(f"benchmark has {len(items)} items, expected 60")
by_type = {}
for it in items:
    by_type.setdefault(it["query_type"], []).append(it)
    for ev in it["gold_evidence"]:
        if ev not in claim_by_id: err(f"{it['id']}: gold_evidence {ev} does not exist")
    known = people | topics | set(sources) | {c["id"] for c in reg["clients"]} | {p["id"] for p in reg["payers"]}
    for ent in it["entities"]:
        if ent not in known: err(f"{it['id']}: unknown entity {ent}")
    if not it.get("rubric"): err(f"{it['id']}: missing rubric")
if len(by_type) != 12: err(f"benchmark covers {len(by_type)} query types, expected 12")
for qt, its in by_type.items():
    if len(its) != 5: err(f"benchmark type {qt}: {len(its)} items, expected 5")
    diffs = sorted(i["difficulty"] for i in its)
    if diffs != ["cross_source", "cross_source", "distractor_trap", "single_source", "single_source"]:
        err(f"benchmark type {qt}: difficulty mix {diffs} != 2 single / 2 cross / 1 trap")
b2 = next((i for i in items if i["id"] == "b_change_02"), None)
if not b2 or b2["gold_evidence"] != ["clm_src014_02", "clm_src003_04"]:
    err("b_change_02 does not match the spec example (gold_evidence pair)")

# ---- wikilinks resolve (suffix match, .md implied) ----
md_files = [p for p in ROOT.rglob("*.md") if "claim_parts" not in str(p)]
rels = {str(p.relative_to(ROOT))[:-3] for p in md_files}  # path sans .md
link_rx = re.compile(r"\[\[([^\]|#]+)")
for p in md_files:
    for link in link_rx.findall(p.read_text(encoding="utf-8")):
        link = link.strip()
        if not any(r == link or r.endswith("/" + link) for r in rels):
            err(f"{p.relative_to(ROOT)}: unresolved wikilink [[{link}]]")

# ---- report ----
for w in warnings: print("WARN:", w)
if errors:
    print(f"\nFAIL — {len(errors)} error(s):")
    for e in errors: print("  -", e)
    sys.exit(1)
print(f"PASS — {len(claims)} claims / {len(graph['nodes'])} nodes / {len(graph['edges'])} edges / "
      f"{len(items)} benchmark items / {len(md_files)} markdown files, all checks green"
      + (f" ({len(warnings)} warnings)" if warnings else ""))

if __name__ == "__main__" or True:
    pass
