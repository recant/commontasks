#!/usr/bin/env python3
"""build_db.py — load the Clarion corpus into clarion.db (SQLite + FTS5).

Schema per spec §2. Inputs: entities.json, claims.json, graph_seed.json, and the
source markdown files (raw text). Stdlib only.

Usage: python3 build_db.py [--db clarion.db]
"""
import json, sqlite3, argparse, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DDL = """
CREATE TABLE sources(id TEXT PRIMARY KEY, type TEXT, path TEXT, date TEXT,
                     title TEXT, participants JSON, raw TEXT);
CREATE TABLE nodes(id TEXT PRIMARY KEY, type TEXT, label TEXT, props JSON);
CREATE TABLE edges(src TEXT, dst TEXT, type TEXT, props JSON,
                   PRIMARY KEY(src,dst,type));
CREATE TABLE claims(id TEXT PRIMARY KEY, text TEXT, speaker TEXT, source_id TEXT,
                    date TEXT, stance TEXT, status TEXT, anchor TEXT, topics JSON);
CREATE VIRTUAL TABLE claims_fts USING fts5(text, content='claims', content_rowid='rowid');
"""

def parse_frontmatter(text):
    """Minimal frontmatter parser: flat `key: value` between leading --- fences.
    Values are tried as JSON (covers quoted strings and flow lists), else raw."""
    fm = {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return fm
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line or line.startswith(" "):
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        try:
            fm[key.strip()] = json.loads(val)
        except (json.JSONDecodeError, ValueError):
            fm[key.strip()] = val
    return fm

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "clarion.db"))
    args = ap.parse_args()

    reg = json.loads((ROOT / "entities.json").read_text(encoding="utf-8"))
    claims = json.loads((ROOT / "claims.json").read_text(encoding="utf-8"))
    graph = json.loads((ROOT / "graph_seed.json").read_text(encoding="utf-8"))

    dbp = Path(args.db)
    if dbp.exists():
        dbp.unlink()
    con = sqlite3.connect(dbp)
    con.executescript(DDL)

    for s in reg["sources"]:
        raw = (ROOT / s["path"]).read_text(encoding="utf-8")
        fm = parse_frontmatter(raw)
        if fm.get("id") != s["id"]:
            sys.exit(f"frontmatter id mismatch in {s['path']}: {fm.get('id')} != {s['id']}")
        con.execute("INSERT INTO sources VALUES (?,?,?,?,?,?,?)",
                    (s["id"], s["type"], s["path"], s["date"], s["title"],
                     json.dumps(s["participants"]), raw))

    for c in claims:
        con.execute("INSERT INTO claims VALUES (?,?,?,?,?,?,?,?,?)",
                    (c["id"], c["text"], c["speaker"], c["source_id"], c["date"],
                     c["stance"], c["status"], json.dumps(c["anchor"], ensure_ascii=False),
                     json.dumps(c["topics"])))

    for n in graph["nodes"]:
        con.execute("INSERT INTO nodes VALUES (?,?,?,?)",
                    (n["id"], n["type"], n["label"], json.dumps(n["props"], ensure_ascii=False)))
    for e in graph["edges"]:
        con.execute("INSERT OR IGNORE INTO edges VALUES (?,?,?,?)",
                    (e["src"], e["dst"], e["type"], json.dumps(e["props"], ensure_ascii=False)))

    con.execute("INSERT INTO claims_fts(claims_fts) VALUES('rebuild')")
    con.commit()

    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("sources", "claims", "nodes", "edges")}
    # smoke-test the honeypot: FTS for the appeal-window query should surface the stale SOP claim
    hits = con.execute(
        "SELECT c.id FROM claims_fts f JOIN claims c ON c.rowid=f.rowid "
        "WHERE claims_fts MATCH 'UnitedHealthcare reconsideration' ORDER BY rank LIMIT 3").fetchall()
    con.close()
    print(f"clarion.db built: {counts}")
    print(f"FTS smoke test ('UnitedHealthcare reconsideration') top hits: {[h[0] for h in hits]}")

if __name__ == "__main__":
    main()
