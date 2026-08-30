#!/usr/bin/env python3
"""derive.py — assemble claims.json and graph_seed.json from the corpus.

Inputs:
  entities.json            canonical registry (people/clients/payers/topics/sources/
                           questions/decisions/action_items/gaps/skills/timeline_chains)
  <parts-dir>/claims_*.json  claim part files (quote-only anchors)
  tools/edges_manual.json  hand-authored claim-level edges

Outputs (corpus root):
  claims.json      all claims, anchors resolved to {line, quote} against source files
  graph_seed.json  full graph: nodes + edges (derived + manual)

Usage: python3 tools/derive.py [--parts-dir PATH]
Stdlib only. Exits non-zero if any anchor quote fails to resolve.
"""
import json, sys, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def resolve_anchor(source_path, quote):
    """Return 1-based line number of first line containing quote, or None.
    Handles quotes spanning a single line only (all ours do)."""
    text = source_path.read_text(encoding="utf-8")
    if quote not in text:
        return None
    for i, line in enumerate(text.splitlines(), 1):
        if quote in line:
            return i
    return -1  # in text but not on one line (shouldn't happen)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts-dir", default=None, help="directory holding claims_*.json part files")
    args = ap.parse_args()

    reg = load(ROOT / "entities.json")
    manual = load(ROOT / "tools" / "edges_manual.json")

    # ---- claims: merge parts, resolve anchors ----
    parts_dir = Path(args.parts_dir) if args.parts_dir else ROOT / "tools" / "claim_parts"
    part_files = sorted(parts_dir.glob("claims_*.json"))
    if not part_files:
        sys.exit(f"no claims_*.json part files found in {parts_dir}")

    src_by_id = {s["id"]: s for s in reg["sources"]}
    claims, errors = [], []
    for pf in part_files:
        for c in load(pf):
            sid = c["source_id"]
            if sid not in src_by_id:
                errors.append(f"{c['id']}: unknown source {sid}"); continue
            spath = ROOT / src_by_id[sid]["path"]
            line = resolve_anchor(spath, c["anchor"]["quote"])
            if line is None:
                errors.append(f"{c['id']}: anchor quote not found in {spath.name}: {c['anchor']['quote'][:60]!r}")
            else:
                c["anchor"] = {"line": line, "quote": c["anchor"]["quote"]}
            claims.append(c)

    if errors:
        print("ANCHOR RESOLUTION ERRORS:")
        for e in errors:
            print("  -", e)
        sys.exit(1)

    seen = set()
    for c in claims:
        if c["id"] in seen:
            sys.exit(f"duplicate claim id {c['id']}")
        seen.add(c["id"])
    claims.sort(key=lambda c: c["id"])

    (ROOT / "claims.json").write_text(
        json.dumps(claims, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"claims.json: {len(claims)} claims, all anchors resolved")

    # ---- graph: nodes ----
    nodes, edges = [], []
    def node(id, type, label, **props):
        nodes.append({"id": id, "type": type, "label": label, "props": props})
    def edge(src, dst, type, **props):
        edges.append({"src": src, "dst": dst, "type": type, "props": props})

    for p in reg["people"]:
        node(p["id"], "person", p["name"], role=p["role"], internal=p["internal"], slug=p["slug"])
    for c in reg["clients"]:
        node(c["id"], "client", c["name"], specialty=c["specialty"],
             contract_end=c["contract_end"], status=c["status"], slug=c["slug"])
    for p in reg["payers"]:
        node(p["id"], "payer", p["name"], slug=p["slug"])
    for t in reg["topics"]:
        node(t["id"], "topic", t["label"], slug=t["slug"], scenario=t["scenario"])
    for s in reg["sources"]:
        node(s["id"], "source", s["title"], doc_type=s["type"], date=s["date"],
             path=s["path"], distractor=s.get("distractor", False))
    for c in claims:
        node(c["id"], "claim", c["text"][:110], speaker=c["speaker"], date=c["date"],
             stance=c["stance"], status=c["status"], source_id=c["source_id"])
    for q in reg["questions"]:
        askers = sorted({a["person"] for a in q["asks"]})
        node(q["id"], "question", q["text"], topic=q["topic"],
             ask_count=len(q["asks"]), askers=askers)
    for d in reg["decisions"]:
        node(d["id"], "decision", d["label"], date=d["date"],
             decided_by=d["decided_by"], status=d["status"], topic=d["topic"])
    for a in reg["action_items"]:
        props = {k: a[k] for k in ("owner", "due", "status", "scenario") if k in a}
        for k in ("promised_to", "done_date", "note"):
            if k in a: props[k] = a[k]
        node(a["id"], "action_item", a["label"], **props)
    for g in reg["gaps"]:
        node(g["id"], "knowledge_gap", g["label"], topic=g["topic"], question=g.get("question"))
    for s in reg["skills"]:
        node(s["id"], "skill", s["label"], path=s["path"])

    # ---- graph: derived edges ----
    for c in claims:
        edge(c["speaker"], c["id"], "speaker_of")
        edge(c["id"], c["source_id"], "from_source")
        for t in c["topics"]:
            edge(c["id"], t, "about")
    for q in reg["questions"]:
        edge(q["id"], q["topic"], "about")
        for a in q["asks"]:
            edge(a["person"], q["id"], "asked", source=a["source"], date=a["date"])
    for d in reg["decisions"]:
        edge(d["id"], d["topic"], "about")
        edge(d["id"], d["source"], "decided_in")
    for g in reg["gaps"]:
        edge(g["id"], g["topic"], "about")
        if g.get("question"):
            edge(g["id"], g["question"], "about")
    for a in reg["action_items"]:
        edge(a["id"], a["source"], "promised_in")
        kw = {"promised_to": a["promised_to"]} if "promised_to" in a else {}
        edge(a["id"], a["owner"], "owned_by", **kw)
    for s in reg["skills"]:
        for src in s["derived_from"]:
            edge(s["id"], src, "derived_from")
    for p in reg["people"]:
        for t in p.get("expertise", []):
            edge(p["id"], t, "expert_in", basis="registry")
    for s in reg["sources"]:
        for c in s.get("clients", []):
            edge(s["id"], c, "involves")
        for p in s.get("payers", []):
            edge(s["id"], p, "involves")
    for chain_name, chain in reg.get("timeline_chains", {}).items():
        for a, b in zip(chain, chain[1:]):
            edge(a, b, "precedes", chain=chain_name)

    # ---- graph: manual edges ----
    for e in manual["supersedes"]:
        edge(e["src"], e["dst"], "supersedes", scope=e["scope"])
    for e in manual["supports"]:
        edge(e["src"], e["dst"], "supports", note=e.get("note", ""))
    for e in manual["contradicts"]:
        props = {"resolution": e["resolution"]}
        if "resolved_by" in e: props["resolved_by"] = e["resolved_by"]
        if "note" in e: props["note"] = e["note"]
        edge(e["src"], e["dst"], "contradicts", **props)
    for e in manual["answered"]:
        edge(e["src"], e["dst"], "answered", note=e.get("note", ""))
    for e in manual["resolves"]:
        edge(e["src"], e["dst"], "resolves", note=e.get("note", ""))
    for e in manual["justified_by"]:
        edge(e["src"], e["dst"], "justified_by")
    for e in manual["mentions"]:
        edge(e["src"], e["dst"], "mentions")

    # ---- integrity: every edge endpoint must be a node ----
    ids = {n["id"] for n in nodes}
    dupes = len(nodes) - len(ids)
    if dupes:
        sys.exit(f"{dupes} duplicate node ids")
    bad = [(e["src"], e["dst"], e["type"]) for e in edges
           if e["src"] not in ids or e["dst"] not in ids]
    if bad:
        print("DANGLING EDGE ENDPOINTS:")
        for b in bad: print("  -", b)
        sys.exit(1)

    graph = {"nodes": nodes, "edges": edges}
    (ROOT / "graph_seed.json").write_text(
        json.dumps(graph, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    by_type = {}
    for n in nodes: by_type[n["type"]] = by_type.get(n["type"], 0) + 1
    et = {}
    for e in edges: et[e["type"]] = et.get(e["type"], 0) + 1
    print(f"graph_seed.json: {len(nodes)} nodes, {len(edges)} edges")
    print("  nodes:", json.dumps(by_type))
    print("  edges:", json.dumps(et))

if __name__ == "__main__":
    main()
