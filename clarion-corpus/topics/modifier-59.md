---
id: top_modifier59
type: topic
label: Anthem modifier 59 / X-subset edits
---

# Modifier 59 / X-subset (Anthem)

Since [[payers/anthem]]'s March 2026 ClaimsXten update, generic modifier 59 no longer bypasses NCCI PTP edits on therapy pairs (97140 + 97110 same DOS). The working fix — X-subset modifier (usually XS) on the column-2 line, plus `anthem_line_split` in [[payer_configs/anthem-config]] — lives in people's heads: [[people/priya-nair]] (internal) and [[people/vik-malhotra]] (external, independently confirmed).

Asked four times ([[people/tom-reyes]], [[people/karen-doyle]], [[people/dana-ortiz]], [[people/nina-park]]); still not in any SOP — [[docs/sop-denial-management]] predates the change and still says "append modifier 59".
