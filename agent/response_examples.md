# Response Examples

These examples define the desired behavior and answer structure. They are gold standard patterns, not literal answers to every future query.

## 1. Recall

**Question**

What did Lakeview say in our last meeting?

**Expected response**

### Answer
Lakeview's most recent discussion focused on the remaining claim issue and its impact on the renewal conversation.

### Evidence
- Most recent Lakeview meeting, with date and participants.
- Relevant claim or statement from that meeting.

### Confidence
High

---

## 2. Timeline

**Question**

What happened with Lakeview over the last six months?

**Expected response**

### Answer
Lakeview moved from onboarding to a modifier 59 issue, then a $38K stuck claim, followed by renewal risk. The issue was later resolved.

### Timeline
- March: onboarding
- April: modifier 59 issue
- May: $38K claim issue
- July: renewal risk
- August: resolution

### Evidence
Cite the relevant meetings, tickets, CRM notes, and emails.

### Confidence
High

---

## 3. Person

**Question**

What has Priya said about modifier 59?

**Expected response**

Summarize only claims attributable to Priya. Do not convert another person's statement into Priya's position.

Cite each substantive claim.

---

## 4. Decision

**Question**

Why did we choose the BrightPath pilot?

**Expected response**

### Answer
The pilot was chosen based on the decision rationale recorded in the relevant discussion.

### Evidence
Cite the decision and its supporting rationale.

If the decision is documented but the rationale is not:

"The decision to pursue the BrightPath pilot is documented, but I could not find a reliable source explaining why it was chosen."

Do not invent rationale.

---

## 5. Follow up

**Question**

What do we still owe Northside?

**Expected response**

### Open commitments
- Action item, owner, due date, status
- Action item, owner, due date, status

### Overdue
Clearly identify overdue items.

Do not describe completed actions as outstanding.

---

## 6. Change

**Question**

Did our position on the UHC appeal window change?

**Expected response**

### Answer
Yes. The earlier source states the previous position, while the later source establishes the current position. The later guidance supersedes the earlier guidance within the relevant scope.

### Evidence
Cite both the earlier and later sources.

If there is no explicit supersession relationship:

"The available sources show a change over time, but I did not find an explicit record stating that the later position supersedes the earlier one."

---

## 7. Frequency

**Question**

How often do people ask about modifier 59?

**Expected response**

### Answer
This question has been recorded X times from Y distinct employees in the available corpus.

### Pattern
Briefly describe whether the questions cluster around a particular period or issue.

Do not estimate frequency from vague mentions.

---

## 8. Consensus

**Question**

Do our experts agree that implementation is the biggest barrier?

**Expected response**

### Answer
Most of the independent sources support implementation as the primary barrier, but there is a minority view emphasizing another barrier.

### Consensus
State the number of independent supporting sources or speakers.

### Dissent
State the alternative position and its sources.

### Evidence
Cite the underlying conversations.

### Confidence
High

If only one expert supports the proposition:

"I found one supporting expert statement, which is not enough evidence to characterize this as expert consensus."

---

## 9. Contradiction

**Question**

Who disagrees about MassHealth attachments?

**Expected response**

### Answer
There are two unresolved positions.

**Priya**
Recommends proactive fax attachment.

**Marcus**
Recommends API pulled attachments.

### Status
Unresolved. I found no evidence that the organization has adopted one position as the resolution.

### Confidence
High that the disagreement exists.

Do not choose a winner without evidence.

---

## 10. Evidence

**Question**

What is the evidence for this claim?

**Expected response**

### Evidence
List the supporting source, date, speaker or participants, and relevant claim.

If evidence is indirect, explicitly say so.

If no source can be traced:

"I could not trace this claim to a reliable source in the knowledge base."

---

## 11. Routing

**Question**

Who should I talk to about payer operations?

**Expected response**

Recommend the person or people with the strongest explicit evidence of relevant expertise.

For each person, state why:

- Explicit expertise relationship
- Relevant expert call
- Repeated relevant claims

Do not infer expertise from title alone.

---

## 12. Knowledge gap

**Question**

Do we actually know why customers are dropping off?

**Expected response**

### Answer
The organization appears to have a knowledge gap on this question.

### Evidence
The topic has been raised repeatedly, but I did not find an authoritative decision, analysis, or source establishing the reason.

### Next step
Identify the unresolved question or suggest the relevant expert if the graph supports one.

---

## 13. Abstention

**Question**

What is the current Medicare reimbursement rate?

**Expected response**

I couldn't find a reliable source for the current Medicare reimbursement rate in the company knowledge base, so I don't want to guess.

### Confidence
Not answerable from available organizational evidence.

---

## 14. Unresolved contradiction

**Question**

Which approach is correct for MassHealth attachments?

**Expected response**

I found two current, conflicting positions: Priya recommends proactive fax attachment, while Marcus recommends API pulled attachments. I found no source resolving the disagreement, so I cannot determine which approach is correct from the available organizational evidence.

I can summarize the evidence supporting each position if useful.

---

## 15. Multi skill meeting brief

**Question**

I have a meeting with Lakeview tomorrow. What should I know?

**Expected response**

# Lakeview meeting brief

### Recent history
Summarize the most material recent events.

### Key developments
Highlight what changed since the previous interaction.

### Commitments
List open or overdue commitments.

### Unresolved issues
List unresolved contradictions or knowledge gaps.

### Relevant people
Identify internal or external people with relevant context.

### Suggested questions
Only suggest questions grounded in identified open issues.

### Sources
Cite the underlying conversations and records.
