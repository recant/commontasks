---
id: src013
type: expert-call
date: 2026-04-14
title: "Expert call: Vik Malhotra — Anthem edit behavior & regional payer landscape"
participants: ["[[people/vik-malhotra]]", "[[people/priya-nair]]", "[[people/dana-ortiz]]", "[[people/tom-reyes]]"]
duration_min: 45
---

# Expert call: Vik Malhotra — 2026-04-14

**Attendees:** [[people/vik-malhotra]] (external, ex-Anthem payer ops), [[people/priya-nair]], [[people/dana-ortiz]], [[people/tom-reyes]]
**Context:** Retained for a quarterly payer-behavior review after the March [[payers/anthem]] denial wave. Agenda: Anthem edit engine, then regional payer API programs.

---

**Dana Ortiz:** Vik, the thing our clients keep asking us: why did Anthem PT claims that paid fine in February suddenly start denying in March, and is our fix the right one?

**Vik Malhotra:** Short answer, yes, it's real and it's permanent. Anthem runs ClaimsXten for clinical editing, and their Q1 release changed how the NCCI procedure-to-procedure edits treat bypass modifiers. Modifier 59 used to be a soft bypass — the edit saw it and stood down. In the March release, 59 alone stopped clearing PTP edits; the engine now wants one of the specific X modifiers, and for the therapy pairs you're describing that's XS, distinct structure. The claim also needs to show the payer *why* — a documentation pointer in the note segment. Plain 59 is effectively dead at Anthem for these pairs.

**Priya Nair:** That matches exactly what we saw in the remit pattern from March 12 on. One mechanical question — placement. We've been putting XS on the column-2 code.

**Vik Malhotra:** Correct, and it matters more than people think. The edit fires on the column-2 code of the pair, so the X modifier has to ride the column-2 line. An X modifier on the column-1 line does nothing — the engine doesn't look for it there. I've watched providers "fix" claims for months without realizing that's why nothing changed.

**Tom Reyes:** We got burned initially on multi-unit lines too — is that related?

**Vik Malhotra:** Related but separate. Anthem's engine auto-flags multi-unit therapy lines for manual review at certain unit thresholds. If you split units across separate claim lines instead of stacking them, you stay under the threshold and the edit hit-rate drops substantially. It's cosmetic from a coding standpoint but very real from an adjudication standpoint. If your platform can split lines automatically, turn that on for Anthem.

**Priya Nair:** It can — we're scoping exactly that config change. Good to have it validated.

**Vik Malhotra:** One forward-looking note: expect Anthem to extend the X-subset enforcement to more code pairs in the Q4 edit release. That's the pattern — they pilot on high-volume therapy pairs, then widen. Whatever automation you build, build it per-pair-configurable, not hardcoded to 97110/97140.

---

**Dana Ortiz:** Switching topics — regional payers. We're evaluating a pilot with [[payers/brightpath]]. Worth it?

**Vik Malhotra:** Of the New England regionals, BrightPath's API program is the most mature by a wide margin — it's real FHIR R4 for claim submission and status, not a portal scrape with an API label on it. They built it to attract exactly the kind of automation vendor you are. The caveats: it's a pilot program, so expect contract terms that let them change the API with 30 days' notice, and their claims-status latency SLA is aspirational. But if you want a payer to prove out API-first claims flow with, they're the one I'd pick.

**Dana Ortiz:** That's the direction we were leaning — helpful to hear it from the payer side.

**Vik Malhotra:** Send me the pilot terms when you get them, happy to flag anything unusual.

---

*Next steps recorded: (1) proceed with XS + line-split automation for Anthem (platform), (2) BrightPath pilot evaluation continues with Vik's endorsement noted for the decision discussion.*
