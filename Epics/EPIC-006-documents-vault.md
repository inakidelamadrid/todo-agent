# EPIC-006: Documents vault

- **Status:** draft
- **Owner:** Ignacio
- **Depends on:**
  - F-1 User login;
  - F-3 Google Drive integration;
  - F-4 File storage and hashing;
  - F-5 AI (extraction);
  - F-6 Scheduler & notifications.
- **Feeds:**
  - EPIC-004 Deadline radar: expiry dates and renewal lead times;
  - EPIC-001 Child support: can reference vault documents (e.g. the custody agreement).

> **Design principle (ADHD):** important papers get lost and renewals sneak up. The vault makes every key document **findable in seconds** and **warns early** when it's about to expire.

## 1. Summary

A secure index of my important documents:
- passport, INE, driver's licence;
- car documents;
- insurance policies;
- the custody or child support agreement;
- tax documents (SAT, RFC), deeds, contracts, medical records, school records.

The files live in **Google Drive** (`drive.file` scope). The app stores **metadata**: type, owner, number (masked), issue and expiry dates, tags, and a hash. I add a document by uploading it, or by photo or PDF through Telegram. AI **extracts** the key fields (expiry date, document number) for me to confirm. Expiry dates feed the **Deadline radar** with per-type renewal lead times, and each type has a **renewal checklist**.

## 2. Goals

- Every important document is findable in under 10 seconds: search by name, type, person or tag.
- No surprise expirations: renewals surface months ahead, depending on type.
- Fast to add: a photo by Telegram becomes a filed document with extracted fields.
- Safe: minimal app permissions on Drive, masked numbers, strict access, audit of who opened what.

## 3. Non-goals (for this epic)

- Being a general file manager or Drive replacement.
- Automating government renewals.
- Sharing documents with others (later: time-limited share links, e.g. to the lawyer from EPIC-001).
- Storing files outside Drive.

## 4. User stories

1. I upload my passport scan in the web app.
   - AI extracts the type (passport), name, number (stored masked, e.g. `•••••4821`), issue date and expiry date.
   - I confirm, and it's filed in Drive under `Vault/Identity/`.
2. I send a photo of my car insurance policy to Telegram with "vault".
   - It's parsed and filed under `Vault/Car/`.
   - I get a confirm card with the extracted expiry date.
3. I search **"insurance"** or **"Mateo"** (a family member's tag) and find the documents instantly.
4. I open a document. I see its details, a preview (opened from Drive) and its **renewal checklist**, e.g. passport: appointment, photos, fees, old passport.
5. My passport expires in 7 months, so it appears on the **Deadline radar** 6 months ahead, with "Start renewal".
6. When I renew, I upload the new document. The old one becomes **superseded**: kept for history, out of the radar.
7. I record documents for **family members** (e.g. my son's birth certificate, CURP, school documents) with an owner tag.
8. I see a **vault overview**: counts by category, and anything expiring in the next 90 days.

## 5. Functional requirements

### 5.1 Documents
- **Types (starter set; editable):**
  - Identity: passport, INE, driver's licence, CURP, birth certificate.
  - Tax: RFC / constancia de situación fiscal, SAT documents.
  - Car: registration (tarjeta de circulación), verification, insurance, tenencia receipts.
  - Insurance: health, life, home.
  - Home: deed, lease, utility contracts.
  - Legal: custody and child support agreement, contracts.
  - Medical and school records.
  - Other.
- **Fields:**
  - title, type, category, owner (me or a family member);
  - number (stored encrypted, displayed masked), issuer;
  - `issuedAt`, `expiresAt`;
  - tags, notes;
  - files (front, back, pages);
  - status: `active` · `superseded` · `archived`.
- **Versioning:** a renewal links the new document to the previous one (`supersedesId`).

### 5.2 Adding documents
- **Web:** drag-and-drop or file picker (PDF / JPG / PNG / HEIC), multi-page.
- **Telegram:** a photo or PDF with the caption "vault" (or `/vault`) goes to the vault flow, not brain dump or expenses (F-7 routing).
- **Extraction (F-5):** a vision model reads the type, number, dates and name, with a confidence score per field.
  - I always confirm before saving.
  - Low-confidence fields are highlighted.
  - The raw extracted text is not stored by default.
- **Duplicate detection:** the same file hash, or the same type + number, triggers a warning.

### 5.3 Google Drive filing (F-3)
- Folder layout: `Vault/<Category>/<Owner>/<Type> - <Title> - <YYYY-MM-DD>.<ext>`.
- The database stores the Drive file ID, MIME type, SHA-256 and size. The file content never lives in the app database.
- Previews and downloads open through short-lived authorised links, not public links.

### 5.4 Expiry and renewal
- **Per-type lead times** (defaults, editable):
  - passport 180 days; INE 60; driver's licence 60;
  - car insurance 30; health insurance 30; car verification 30;
  - other 30.
- Each document with `expiresAt` appears in EPIC-004 at `expiresAt − leadDays`, with its reminder stages (e.g. 90/30/7 days).
- **Renewal checklists:**
  - a template per type (editable);
  - starting a renewal can create EPIC-003 tasks from the checklist ("Book passport appointment", "Get photos") with due dates before expiry.
- **Mark renewed:** upload the new version, and the old one becomes `superseded` and leaves the radar.

### 5.5 Search and browse
- Full-text search over title, type, tags, owner, issuer and notes. Numbers are searchable only by their last 4 digits.
- Filters: category, owner, status, and "expiring in N days".
- **Overview:** categories with counts, plus an "Expiring soon" list.

### 5.6 Access log
- Every open, preview or download is recorded (`DocumentAccess`: who, when, action).
- Shown on each document as "Last opened Nov 14".

## 6. UX notes

- **Design:** Midnight Transit.
  - The vault is a calm, dense **index**: a table on desktop, cards on mobile, with type chips and owner tags.
  - Expiry shows as "Expires in 7 months" with a subtle progress line toward expiry, in the transit idiom.
  - It is **not** a gallery of scans; previews appear only on demand.
- **Masked numbers:** shown masked with a "Reveal" tap. Reveals are logged and re-mask after 30 seconds.
- **Confirm card** (after extraction): side-by-side document thumbnail and fields, with low-confidence fields highlighted and a single "Save to vault".
- **Empty state:** "Start with the 3 documents you'd panic about losing: passport, INE, car insurance."

## 7. Data model (draft)

| Entity | Key fields |
|---|---|
| `Document` | id, title, type, category, ownerId, numberEncrypted?, numberLast4?, issuer?, issuedAt?, expiresAt?, tags[], notes, status, supersedesId?, createdAt, updatedAt |
| `DocumentFile` | documentId, storedFileId (F-4: driveFileId, sha256, mimeType, size), page/side, order |
| `DocumentType` | slug, name, category, leadDays, reminderStages[], checklistTemplate[] |
| `Person` | id, name/label, relation (`me`/`child`/`other`) |
| `DocumentAccess` | documentId, action (`view`/`preview`/`download`/`reveal-number`), at, client |
| `ExtractionResult` (transient) | fields with confidences; discarded after confirm |

## 8. API (draft)

- `POST /documents/extract` (multipart; returns proposed fields, nothing saved yet) → `POST /documents` (confirm + file IDs).
- `GET /documents` with `q`, `category`, `owner`, `status`, `expiringWithinDays`. Also `GET / PATCH / DELETE /documents/{id}`.
- `POST /documents/{id}/renew` (links the new document and supersedes the old one), `POST /documents/{id}/renewal-tasks` (creates EPIC-003 tasks).
- `GET /documents/{id}/preview-link` (short-lived), `POST /documents/{id}/reveal-number` (logged).
- `GET/PATCH /document-types`, `GET/POST /people`.
- **Radar adapter (EPIC-004):** documents whose `expiresAt − leadDays ≤ window`.

## 9. Security and privacy

- **The most sensitive data in the app:** identity documents for me and my son.
- F-1 login is required, and step-up re-auth (passkey) is required to **reveal numbers** or **download**.
- Document numbers are encrypted at rest (an app-level key from the environment, never in the repo). Only the last 4 digits are stored in clear for search.
- Drive uses the `drive.file` scope only, so the app can't see the rest of my Drive. Files are never made public.
- **AI extraction:** send only the image or PDF needed, to a provider I approve. Never store raw OCR text, and never send numbers back out in summaries or Telegram.
- Telegram confirmations show the type and expiry only, never full numbers.
- The access log is append-only.

## 10. Epic acceptance criteria

- [ ] Uploading (web) or sending (Telegram) a document produces a confirm card with correctly extracted type and expiry for common Mexican documents (passport, INE, licence, car insurance).
- [ ] Files are filed in Drive in the defined layout, and the database stores only metadata, file IDs and hashes.
- [ ] Search finds documents by title, type, tag or owner in under 1 s, and numbers by last 4 only.
- [ ] Expiring documents appear on the Deadline radar at the type's lead time, with the reminder stages.
- [ ] Renewal creates checklist tasks and supersedes the old document correctly.
- [ ] Revealing a number or downloading requires re-auth and is logged. Masked numbers re-mask automatically.

## 11. Proposed ticket breakdown (draft)

- **Backend:**
  - People + document types (seeded).
  - Documents API + Drive filing (F-3/F-4).
  - Extraction endpoint (F-5 vision).
  - Encryption of numbers + step-up auth for reveal/download.
  - Renewal + checklist → tasks.
  - Radar adapter.
  - Access log.
- **Frontend:**
  - Vault index + search/filters.
  - Upload + confirm card.
  - Document detail (preview, checklist, history).
  - Renew flow.
  - Settings (types, lead times, people).
- **Ops:** n8n / Telegram `/vault` branch.

## 12. Risks

- **A data breach of identity documents.** Mitigation: Drive-only storage, encrypted numbers, step-up auth, minimal scopes, access log.
- **Extraction errors on dates** (DD/MM vs MM/DD). Mitigation: Mexican date conventions by default, confirm card, low-confidence highlighting.
- **Drive auth expiry.** Mitigation: the shared F-3 health indicator and re-auth prompt.

## 13. Open questions (answer in place)

1. Which documents do you want in the first version (list the top 10)?
   - Answer:
2. Who are the people/owners (you, your son, others)?
   - Answer:
3. Lead times per type: are the defaults right?
   - Answer:
4. Should renewal checklists create tasks automatically, or only when you tap "Start renewal"?
   - Answer:
5. Is step-up re-auth (passkey/Face ID) OK for reveal and download?
   - Answer:
6. Which AI provider is acceptable for extracting from identity documents (or local-only OCR)?
   - Answer:
7. Should the custody/child support agreement live here and be linked from EPIC-001?
   - Answer:
