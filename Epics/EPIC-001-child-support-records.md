# EPIC-001: Child support records

- **Status:** draft
- **Owner:** Ignacio
- **Depends on:** F-1 User login, F-3 Google Drive integration, F-4 File storage and hashing, F-5 AI summaries (see `Epics/README.md`)
- **Related:** EPIC-002. Child support can appear as an expense category.

> **Not legal advice.** Confirm the evidence requirements with your lawyer before treating any output of this feature as legally sufficient.

## 1. Summary

Record every monthly child support payment for my son, attach proof of payment, and have my ex-spouse **digitally acknowledge** each payment through a secure link, without needing an account. Every signed receipt and every proof is filed automatically in **Google Drive**. At any time, I can produce a **lawyer-ready summary** for a date range: what was paid, what is pending, what is signed, and any adjustments.

## 2. Goals

- One trustworthy, chronological record of child support payments.
- Low-friction acknowledgment from the ex-spouse: open link → review → sign → done.
- Tamper-evident documents: a PDF receipt with an audit trail and a hash, stored in Drive.
- Instant summaries and exports for lawyers, mediators or court.
- Reminders, so nothing stays unsigned or unpaid without notice.

## 3. Non-goals (for this epic)

- Giving legal advice or calculating legally owed amounts beyond the agreed terms I enter.
- Moving money: the app records payments, it does not make them.
- A full account for the ex-spouse (signing works through one-time links only).
- Court e-filing.

## 4. Roles

| Role | Can do |
|---|---|
| **Payer (me)** | Everything: set terms, record payments, upload proof, request signatures, export summaries, manage Drive |
| **Recipient (ex-spouse)** | Only through a one-time link: view the specific payment, sign or dispute it with a comment. No access to anything else |
| **Lawyer (optional, later)** | Read-only access to a shared summary or an export link, time-limited |

## 5. User stories

1. As the payer, I set up the **agreement terms**, so each month is pre-filled: monthly amount, currency, due day, start date, annual adjustment rule, and the child's display name or initials.
2. As the payer, I **record a payment** with amount, date, method (SPEI, cash, deposit, other), reference/folio, and an attached proof (PDF/image).
3. As the payer, I **request an acknowledgment**, and the recipient gets a secure link by email or WhatsApp.
4. As the recipient, I open the link, see the payment details and proof, and **sign**. Or I **dispute** it with a short reason.
5. As the payer, I see each month's **status**: `unpaid` · `paid – awaiting signature` · `signed` · `disputed` · `partial`.
6. As the payer, I get **reminders** for unpaid months and for signatures pending more than N days.
7. As the payer, signed receipts and proofs are **filed in Google Drive** automatically, in a clear folder structure.
8. As the payer, I record **extraordinary expenses** (school, medical, other) separately from the monthly amount, with proof, and optionally request acknowledgment for them too.
9. As the payer, I generate a **summary for any date range**: totals per month, arrears, partial months, signature status, adjustments, and links to every document. It comes as a PDF plus a short plain-language summary.
10. As the payer, I can **ask questions** such as "Which months in 2026 are unsigned?" or "Total paid since the agreement started?", answered only from my records.
11. As the payer, I'm **told when the annual adjustment is due**, with the new suggested amount based on the rule I set.

## 6. Functional requirements

### 6.1 Agreement terms
- Fields:
  - monthly amount and currency;
  - due day (1–31);
  - start month;
  - optional end month;
  - adjustment rule (`none` · `fixed %` · `index-based (e.g. INPC)` with the adjustment month);
  - recipient's contact (email and/or phone);
  - optional notes or court case reference.
- Changing the terms creates a **new version** effective from a given month. History is kept, never overwritten.

### 6.2 Payments
- One expected obligation per month, generated from the terms. Several payments may cover one month (partial payments).
- Payment fields:
  - `amountCents`, `currency` and `paidAt`;
  - `method`, plus a `reference`/folio;
  - `period` (`YYYY-MM`) and a `note`;
  - `proofFileIds[]`.
- Derived month status:
  - `unpaid` when the payments total 0;
  - `partial` when the total is above 0 but below the obligation;
  - `paid` when the total reaches the obligation;
  - signature status shown alongside.
- Extraordinary expenses are their own record type (`category`: school/medical/other, amount, proof, optional split %).

### 6.3 Acknowledgment / digital signature
- **Level A (MVP): in-app acknowledgment**
  - One-time, single-use, expiring link (e.g. 7 days) with an unguessable token. No personal data in the URL.
  - The signing page shows the payment details, the proof preview and the text to acknowledge (editable template), e.g. *"I acknowledge receiving MXN $X as child support for November 2026."*
  - The recipient signs by drawing or typing their full name and ticking a consent checkbox.
  - Audit trail captured:
    - signer name;
    - timestamp (UTC);
    - IP;
    - user agent;
    - link ID;
    - the document hash before and after signing.
  - Dispute option: a required reason, which notifies the payer.
- **Level B (optional): signature provider** (Dropbox Sign / DocuSign) behind the same interface. The provider's audit certificate is filed with the receipt.
- **Level C (future): Mexican e.firma with NOM-151 conservation** through a certified provider.
- After signing, generate a **sealed PDF receipt**:
  - payment details;
  - signature image or typed name;
  - the audit trail;
  - a QR code or verification ID;
  - the SHA-256 of the PDF stored in the database.

### 6.4 Google Drive filing
- Uses F-3 (`drive.file` scope only).
- Folder structure: `Child support/<YYYY>/<MM - Month>/` containing:
  - `proof-<date>.<ext>`;
  - `receipt-signed-<YYYY-MM>.pdf`;
  - `audit-<YYYY-MM>.json`.
- The database stores Drive file IDs, names, MIME types and hashes, never the file contents.
- If Drive is unreachable, queue the upload and retry. The UI shows "Not yet filed".

### 6.5 Reminders and notifications
- **To me (payer):**
  - payment due in 3 days;
  - overdue payment;
  - signature pending more than N days;
  - a dispute was received;
  - the annual adjustment is due.
- **To the recipient:** the signing request, and one reminder after N days (configurable, max 2).
- Channels: email first; WhatsApp or Telegram later.

### 6.6 Summaries and exports ("lawyer pack")
- Choose a date range, then generate:
  1. **A PDF report:** agreement terms (with versions), a month-by-month table (expected, paid, difference, method, signature status), extraordinary expenses, totals per currency, and an arrears section.
  2. **A plain-language summary**, about 1 page, generated by F-5 from the structured data only, with a note on any data gaps.
  3. **A ZIP or Drive folder link** with every proof and signed receipt in the range.
- **Q&A:** ask natural-language questions. Answers cite the months and documents they come from. The service never answers beyond the data.

## 7. Data model (draft)

| Entity | Key fields |
|---|---|
| `SupportAgreement` | id, version, effectiveFrom (`YYYY-MM`), endMonth?, amountCents, currency, dueDay, adjustmentRule, recipientContact, notes |
| `SupportObligation` | agreementId, period (`YYYY-MM`), expectedCents (derived; stored once the month closes) |
| `SupportPayment` | id, period, amountCents, currency, paidAt, method, reference, note, proofFileIds[] |
| `ExtraordinaryExpense` | id, date, category, amountCents, currency, splitPercent?, note, proofFileIds[] |
| `AcknowledgmentRequest` | id, targetType (payment/expense/month), targetId, tokenHash, expiresAt, sentVia, status (pending/signed/disputed/expired), createdAt |
| `Acknowledgment` | requestId, signerName, signatureImageFileId?, typedName?, signedAt, ip, userAgent, statementText, documentHashBefore, receiptFileId, receiptHash |
| `Dispute` | requestId, reason, createdAt |
| `StoredFile` | id, driveFileId, name, mimeType, sha256, uploadedAt, status (queued/filed/failed) |

## 8. Key flows

1. **Monthly:** obligation generated → I record the payment and proof → proof filed in Drive → I request the acknowledgment → the recipient signs → the sealed receipt is generated, hashed and filed → status `signed`.
2. **Dispute:** the recipient disputes → I'm notified → the month shows `disputed` with the reason → I can add evidence and re-request.
3. **Lawyer pack:** choose a range → PDF, summary and folder link → share (manually, or with a time-limited read-only link later).

## 9. Security and privacy

- This is **highly sensitive data**: a minor, a third party's personal information, and financial records.
- Require F-1 login for everything except the signing page. The signing page is public but token-gated, single-use and expiring, with rate limits.
- Store token **hashes** only. Links reveal no names.
- Keep the recipient's personal data to the minimum: name and contact. Store the child's initials or display name only.
- Encrypt files at rest (Drive) and use TLS everywhere. No personal data in logs.
- Make the audit trail append-only: acknowledgments are never edited, only superseded.
- **Retention:** keep records until the obligation ends + N years (decide with the lawyer). Export everything at any time.
- **AI summaries:** send only the needed fields, never documents or images, to the model provider. Record which provider and model were used.

## 10. UX notes

- **Same design system** (Midnight Transit, `DESIGN.md`). Child support could be its own **line** (its own colour) on a dedicated timeline, with one station per month that fills when paid and is ringed when signed.
- **Status chips:** unpaid · partial · awaiting signature · signed · disputed.
- **Signing page:** minimal and calm. Mobile-first, readable, no app chrome. Spanish and English.

## 11. Epic acceptance criteria

- [ ] I can set up terms, record monthly payments with proof, and see the correct status per month (including partial).
- [ ] The recipient signs from a one-time link on their phone without creating an account. The link can't be reused, and it expires.
- [ ] Every signed month has a sealed PDF receipt in Drive whose hash matches the database.
- [ ] Disputes notify me and show in the month's status.
- [ ] A lawyer pack for any range is generated in under a minute, with totals matching the records exactly.
- [ ] Every endpoint except the signing page requires login, and the signing page leaks no data without a valid token.

## 12. Proposed ticket breakdown (draft)

- **Backend:**
  - BE: F-1 user login.
  - BE: F-3 Drive integration.
  - BE: agreement + obligations + payments API.
  - BE: acknowledgment requests, signing endpoint, PDF receipt and hashing.
  - BE: notifications (email).
  - BE: lawyer pack (PDF + ZIP/folder).
  - BE: F-5 summaries + Q&A.
- **Frontend:**
  - FE: terms setup.
  - FE: payments timeline and month detail.
  - FE: public signing page (mobile-first, ES/EN).
  - FE: lawyer pack and Q&A UI.

## 13. Risks

- **Legal sufficiency** of Level A signatures. Mitigation: bank proof is the primary evidence, and Level B/C stay pluggable.
- **The recipient doesn't sign.** Mitigation: reminders, a recorded "not acknowledged" state, and evidence still filed.
- **Drive token expiry or revocation.** Mitigation: upload queue, health indicator, re-auth prompt.
- **AI summary errors.** Mitigation: summaries are generated only from structured data, cite their sources, and come with the exact numeric tables.

## 14. Open questions (answer in place)

1. What are the exact agreement terms: amount, currency, due day, start date, end condition?
   - Answer:
2. What is the annual adjustment rule (none / fixed % / INPC), and in which month?
   - Answer:
3. Which signature level does your lawyer require (A, B or C)?
   - Answer:
4. How should the recipient be contacted: email, WhatsApp or both? Spanish, English or both?
   - Answer:
5. Do you track extraordinary expenses (school, medical)? Shared at what %?
   - Answer:
6. Should arrears or partial payments roll over to the next month, or stay tied to their month?
   - Answer:
7. How long should records be kept, and who else may receive a summary (lawyer, mediator)?
   - Answer:
8. Which AI provider is OK for summaries, given the data's sensitivity?
   - Answer:
