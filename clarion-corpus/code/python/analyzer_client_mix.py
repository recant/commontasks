#!/usr/bin/env python3
"""analyzer_client_mix.py — client/patient panel analyzer (business analytics).

Author: Sofia Chen (reporting) · 2026-08-20
Related: topics/em-coding-levels, the Whitfield review (src052), MBR pipeline.

Per-client profile from claim-level data: demographics (age bands), payer mix,
insurance amounts (billed vs allowed), health-condition categories, E/M level-4
share vs benchmark, and first-pass acceptance. This is the script behind the
"67.8% at 99214" population check quoted in #claims-ops on 8/13.

PHI note (per the compliance policy): synthetic/derived data only — member ids
are surrogate keys, no names/DOBs leave the warehouse. Minimum necessary.

Runs standalone on a deterministic synthetic sample shaped like production
(profiles below mirror the real book: Harbor's level-4 overweight, Cedar
Point's clean pediatric curve, Lakeview's Anthem-heavy PT volume).
"""
from __future__ import annotations
import random
from collections import Counter
from dataclasses import dataclass

TODAY = "2026-08-30"
EM_L4_BENCHMARK = {"family_medicine": 0.44, "pediatrics": 0.33, "orthopedics": 0.51,
                   "behavioral": 0.38, "imaging": 0.0, "multi": 0.45}

# Client profiles mirror the account book (see clients/*.md).
CLIENT_PROFILES = {
    "harbor-family-medicine": dict(specialty="family_medicine", n=500, l4_share=0.68,
        payers={"masshealth": 0.45, "unitedhealth": 0.30, "aetna": 0.15, "anthem": 0.10},
        conditions={"hypertension": 0.30, "diabetes": 0.22, "asthma_copd": 0.14,
                    "wellness": 0.20, "musculoskeletal": 0.14},
        ages=(5, 88), avg_billed=182.0, first_pass=0.902),
    "cedar-point-pediatrics": dict(specialty="pediatrics", n=500, l4_share=0.31,
        payers={"anthem": 0.35, "masshealth": 0.30, "aetna": 0.20, "brightpath": 0.15},
        conditions={"wellness": 0.44, "immunization": 0.22, "asthma_copd": 0.16,
                    "otitis_uri": 0.18},
        ages=(0, 18), avg_billed=96.0, first_pass=0.941),
    "lakeview-orthopedics": dict(specialty="orthopedics", n=500, l4_share=0.49,
        payers={"anthem": 0.55, "unitedhealth": 0.30, "masshealth": 0.15},
        conditions={"musculoskeletal": 0.62, "post_surgical": 0.23, "wellness": 0.05,
                    "chronic_pain": 0.10},
        ages=(16, 84), avg_billed=310.0, first_pass=0.928),
    "northside-clinic": dict(specialty="multi", n=500, l4_share=0.46,
        payers={"anthem": 0.30, "unitedhealth": 0.25, "masshealth": 0.25, "aetna": 0.20},
        conditions={"hypertension": 0.24, "diabetes": 0.18, "musculoskeletal": 0.22,
                    "wellness": 0.24, "behavioral": 0.12},
        ages=(1, 92), avg_billed=164.0, first_pass=0.918),
}

AGE_BANDS = [(0, 17, "0-17"), (18, 39, "18-39"), (40, 64, "40-64"), (65, 200, "65+")]

@dataclass
class ClaimRow:
    member_id: str
    client: str
    payer: str
    age: int
    condition: str
    em_code: str        # 99213 / 99214 / "" for non-E/M
    billed: float
    allowed: float
    first_pass: bool

def _pick(rng: random.Random, weights: dict[str, float]) -> str:
    r, acc = rng.random(), 0.0
    for k, w in weights.items():
        acc += w
        if r <= acc:
            return k
    return k  # float dust

def synthesize(seed: int = 42) -> list[ClaimRow]:
    rng = random.Random(seed)
    rows = []
    for client, p in CLIENT_PROFILES.items():
        for i in range(p["n"]):
            em = ""
            if p["specialty"] != "imaging" and rng.random() < 0.7:  # 70% E/M visits
                em = "99214" if rng.random() < p["l4_share"] else "99213"
            billed = round(rng.gauss(p["avg_billed"], p["avg_billed"] * 0.35), 2)
            billed = max(billed, 25.0)
            rows.append(ClaimRow(
                member_id=f"M{rng.randrange(10**7):07d}", client=client,
                payer=_pick(rng, p["payers"]), age=rng.randint(*p["ages"]),
                condition=_pick(rng, p["conditions"]), em_code=em,
                billed=billed, allowed=round(billed * rng.uniform(0.55, 0.85), 2),
                first_pass=rng.random() < p["first_pass"]))
    return rows

def band(age: int) -> str:
    return next(label for lo, hi, label in AGE_BANDS if lo <= age <= hi)

def profile(rows: list[ClaimRow], client: str) -> dict:
    sub = [r for r in rows if r.client == client]
    em = [r for r in sub if r.em_code]
    l4 = sum(1 for r in em if r.em_code == "99214") / len(em) if em else 0.0
    spec = CLIENT_PROFILES[client]["specialty"]
    return {
        "claims": len(sub),
        "payer_mix": Counter(r.payer for r in sub).most_common(),
        "age_bands": Counter(band(r.age) for r in sub).most_common(),
        "top_conditions": Counter(r.condition for r in sub).most_common(3),
        "avg_billed": sum(r.billed for r in sub) / len(sub),
        "avg_allowed": sum(r.allowed for r in sub) / len(sub),
        "em_l4_share": l4,
        "em_l4_benchmark": EM_L4_BENCHMARK[spec],
        "em_flag": "⚠ AUDIT-SCREEN" if l4 - EM_L4_BENCHMARK[spec] > 0.15 else "ok",
        "first_pass_rate": sum(r.first_pass for r in sub) / len(sub),
    }

def main():
    rows = synthesize()
    print(f"Client panel analyzer — {len(rows)} synthetic claims, as-of {TODAY}\n")
    for client in CLIENT_PROFILES:
        p = profile(rows, client)
        print(f"== {client} ==")
        print(f"  claims {p['claims']} | avg billed ${p['avg_billed']:.2f} | "
              f"avg allowed ${p['avg_allowed']:.2f} | first-pass {p['first_pass_rate']:.1%}")
        print(f"  payer mix: " + ", ".join(f"{k} {v/p['claims']:.0%}" for k, v in p["payer_mix"]))
        print(f"  ages: " + ", ".join(f"{k} {v/p['claims']:.0%}" for k, v in p["age_bands"]))
        print(f"  conditions: " + ", ".join(f"{k} {v/p['claims']:.0%}" for k, v in p["top_conditions"]))
        print(f"  E/M level-4 share {p['em_l4_share']:.1%} vs benchmark "
              f"{p['em_l4_benchmark']:.0%} → {p['em_flag']}\n")
    print("Screen rule: level-4 share >15 points over specialty benchmark flags an")
    print("audit screen (distribution is a screen, not a verdict — see the 8/12")
    print("Whitfield call: audit documentation, never blanket-downcode).")

if __name__ == "__main__":
    main()
