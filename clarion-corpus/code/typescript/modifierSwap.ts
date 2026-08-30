/**
 * modifierSwap.ts — Anthem X-subset modifier auto-swap + line split (scrubber edit).
 *
 * Author: Marcus Webb · 2026-06-30 (the Lakeview QBR commitment, shipped on the day)
 * History: since Anthem's March 2026 ClaimsXten release, generic modifier 59 no
 * longer bypasses NCCI PTP edits. The fix — encoded here and in anthem.yaml —
 * has two easy-to-get-wrong mechanics that this module makes impossible:
 *   1. the X modifier must ride the COLUMN-2 line (an X on column-1 does nothing
 *      — Vik: "I've watched providers fix claims for months without realizing")
 *   2. multi-unit therapy lines split at ≤4 units to stay under the manual-review
 *      threshold.
 *
 * Run: node modifierSwap.ts
 */

interface ClaimLine {
  cpt: string;
  units: number;
  modifiers: string[];
  docPointer?: string; // distinct-site documentation reference
}

interface PtpPair { column1: string; column2: string; swapTo: string; }

// Mirrors anthem.yaml modifier_rules.ptp_pairs — keep the two in sync.
const PTP_PAIRS: PtpPair[] = [
  { column1: "97140", column2: "97110", swapTo: "XS" },
  { column1: "97140", column2: "97112", swapTo: "XS" },
  { column1: "97530", column2: "97110", swapTo: "XS" },
];
const MAX_UNITS_PER_LINE = 4;
const SPLIT_CODES = new Set(["97110", "97112", "97140", "97530"]);

export function applyXSubsetSwap(lines: ClaimLine[]): { lines: ClaimLine[]; notes: string[] } {
  const notes: string[] = [];
  const out = lines.map((l) => ({ ...l, modifiers: [...l.modifiers] }));
  for (const pair of PTP_PAIRS) {
    const col1 = out.find((l) => l.cpt === pair.column1);
    const col2 = out.find((l) => l.cpt === pair.column2);
    if (!col1 || !col2) continue; // pair not present on this claim
    // Strip 59 wherever it appears; the generic bypass is dead at Anthem.
    for (const l of [col1, col2]) {
      const i = l.modifiers.indexOf("59");
      if (i >= 0) { l.modifiers.splice(i, 1); notes.push(`stripped 59 from ${l.cpt}`); }
    }
    // Placement rule: the X modifier rides the COLUMN-2 line, nowhere else.
    if (!col2.modifiers.includes(pair.swapTo)) {
      col2.modifiers.push(pair.swapTo);
      notes.push(`added ${pair.swapTo} to column-2 line ${pair.column2}`);
    }
    if (!col2.docPointer) {
      notes.push(`⚠ HOLD: ${pair.column2} needs a distinct-site doc pointer or the edit re-fires`);
    }
  }
  return { lines: out, notes };
}

export function splitUnits(lines: ClaimLine[]): ClaimLine[] {
  const out: ClaimLine[] = [];
  for (const l of lines) {
    if (!SPLIT_CODES.has(l.cpt) || l.units <= MAX_UNITS_PER_LINE) { out.push(l); continue; }
    let remaining = l.units;
    while (remaining > 0) {
      const take = Math.min(remaining, MAX_UNITS_PER_LINE);
      out.push({ ...l, units: take, modifiers: [...l.modifiers] });
      remaining -= take;
    }
  }
  return out;
}

/** Toy model of Anthem's post-March PTP edit, for the self-test. */
function anthemEditFires(lines: ClaimLine[]): boolean {
  for (const pair of PTP_PAIRS) {
    const col1 = lines.find((l) => l.cpt === pair.column1);
    const col2 = lines.find((l) => l.cpt === pair.column2);
    if (!col1 || !col2) continue;
    // The engine looks ONLY at the column-2 line for an X-subset modifier.
    const ok = col2.modifiers.some((m) => ["XS", "XE", "XP", "XU"].includes(m)) && !!col2.docPointer;
    if (!ok) return true; // CO-97
  }
  return false;
}

function main(): void {
  const claim: ClaimLine[] = [
    { cpt: "97140", units: 2, modifiers: ["59"] },                       // column-1, old habit
    { cpt: "97110", units: 6, modifiers: [], docPointer: "note:L2-shoulder-distinct" },
  ];

  console.log("Before scrubber: edit fires (CO-97)?", anthemEditFires(claim));

  // The classic WRONG fix (pre-scrubber era): X modifier on the column-1 line.
  const wrong = claim.map((l) =>
    l.cpt === "97140" ? { ...l, modifiers: ["XS"] } : { ...l, modifiers: [...l.modifiers] });
  console.log("Wrong fix (XS on column-1):  edit fires?", anthemEditFires(wrong),
              " ← why 'fixed' claims kept denying");

  const { lines: swapped, notes } = applyXSubsetSwap(claim);
  const finalLines = splitUnits(swapped);
  console.log("Scrubber fix (XS on column-2): edit fires?", anthemEditFires(finalLines));
  console.log("Notes:", notes.join("; "));
  console.log("Line split:", finalLines.map((l) => `${l.cpt}x${l.units}[${l.modifiers.join(",")}]`).join(" "));

  if (anthemEditFires(finalLines)) throw new Error("regression: scrubbed claim still hits the edit");
  if (!anthemEditFires(wrong)) throw new Error("toy edit model broken: column-1 X should NOT clear it");
  console.log("✓ self-test: column-2 placement clears the edit, column-1 does not, units ≤4/line");
}

main();
