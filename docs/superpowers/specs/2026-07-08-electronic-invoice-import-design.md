# Electronic Invoice Import Design

## Summary

Add an independent electronic invoice import module for upstream and downstream contract invoicing. Operators upload one top-level zip archive. The archive contains one nested archive per invoice, and each nested archive contains the invoice PDF, OFD, and XML files. The system extracts the XML as the structured source of truth, stores all original files, detects duplicate invoices, recommends matching contracts, and creates draft allocation records. Operators confirm the allocations before the system writes formal invoice records into the existing upstream and downstream contract invoice tables.

The first release covers:

- Upstream invoices: our company issues invoices to Party A, then the confirmed allocation writes to `finance_upstream_invoices`.
- Downstream invoices: suppliers or subcontractors issue invoices to our company, then the confirmed allocation writes to `finance_downstream_invoices`.

The first release does not cover:

- Non-contract expense invoices.
- OCR for image-only or scanned invoices.
- Automatic amount splitting across contracts.
- Fully automatic posting without operator confirmation.

## Existing System Fit

The current system already has:

- `ContractUpstream` with `FinanceUpstreamInvoice` for upstream invoicing.
- `ContractDownstream` with `FinanceDownstreamInvoice` for downstream invoicing.
- MinIO-backed protected file storage through `/api/v1/common/upload` and `/api/v1/common/files/{path}`.
- Role and permission checks for invoice creation and viewing.
- Vue + Element Plus contract detail pages that display invoice subresources.

The import module should not replace the existing manual invoice dialogs. It should create a batch workbench that feeds confirmed records into the same invoice tables used by the current contract detail pages and reports.

## Business Rules

### Company Identity

The system has one fixed company identity for the first release:

- `COMPANY_NAME`
- `COMPANY_TAX_NO`

Both values should be configured through environment variables and surfaced in system settings or deployment docs. Invoice direction is determined by comparing XML buyer/seller tax numbers with `COMPANY_TAX_NO`.

### Direction Rules

- If `seller_tax_no == COMPANY_TAX_NO`, the invoice direction is `upstream`.
- If `buyer_tax_no == COMPANY_TAX_NO`, the invoice direction is `downstream`.
- If neither side matches, the item status is `needs_review` with reason `COMPANY_TAX_NO_NOT_FOUND`.
- If both sides match, the item status is `needs_review` with reason `COMPANY_ON_BOTH_SIDES`.

### One Invoice To Many Contracts

One source invoice may be allocated to multiple contracts.

- One source invoice maps to one `invoice_import_items` row.
- The source invoice may have multiple `invoice_import_allocations` rows.
- Each allocation maps to exactly one upstream or downstream contract.
- Confirmation creates one formal invoice row per allocation.
- The sum of allocation amounts must be greater than zero and must not exceed the invoice total amount.

### Manual Amount Splitting

The first release requires operators to enter allocation amounts manually. The system recommends candidate contracts, but it does not split invoice amounts automatically.

### Duplicate Handling

The system computes a dedupe key from normalized invoice fields:

```text
invoice_number | seller_tax_no | buyer_tax_no | invoice_date | total_amount
```

Duplicate detection happens twice:

- During import parsing, duplicate items are marked before operators work on them.
- During confirmation, the service rechecks duplicates inside the transaction before creating formal invoice rows.

Duplicate items are retained in the import workbench with links to the original item when possible. They are not confirmed unless an operator with invoice management permission explicitly overrides the duplicate flag.

## Data Model

### Contract Tax Number Columns

Add nullable tax number fields to improve matching:

- `contracts_upstream.party_a_tax_no`
- `contracts_upstream.party_b_tax_no`
- `contracts_downstream.party_a_tax_no`
- `contracts_downstream.party_b_tax_no`

Existing contracts can leave these fields empty. Matching still falls back to company-name and keyword signals.

### Formal Invoice Trace Columns

Add nullable trace columns to the existing invoice tables:

- `finance_upstream_invoices.source_import_item_id`
- `finance_upstream_invoices.source_import_allocation_id`
- `finance_downstream_invoices.source_import_item_id`
- `finance_downstream_invoices.source_import_allocation_id`

These fields make confirmed invoice records traceable back to the source import item and the exact allocation row.

### `invoice_import_batches`

Represents one uploaded top-level archive.

Required fields:

- `id`
- `batch_code`
- `original_filename`
- `archive_file_path`
- `archive_file_key`
- `storage_provider`
- `status`
- `total_items`
- `parsed_items`
- `duplicate_items`
- `error_items`
- `confirmed_items`
- `created_by`
- `created_at`
- `updated_at`
- `completed_at`
- `error_message`

Allowed statuses:

- `uploaded`
- `processing`
- `completed`
- `completed_with_errors`
- `failed`

### `invoice_import_items`

Represents one source electronic invoice extracted from one nested archive.

Required fields:

- `id`
- `batch_id`
- `source_archive_name`
- `invoice_number`
- `invoice_code`
- `invoice_date`
- `seller_name`
- `seller_tax_no`
- `buyer_name`
- `buyer_tax_no`
- `amount_without_tax`
- `tax_amount`
- `total_amount`
- `invoice_type`
- `remarks`
- `dedupe_key`
- `duplicate_of_item_id`
- `direction`
- `parse_status`
- `match_status`
- `confirmation_status`
- `pdf_file_path`
- `pdf_file_key`
- `ofd_file_path`
- `ofd_file_key`
- `xml_file_path`
- `xml_file_key`
- `raw_xml`
- `parsed_payload`
- `error_code`
- `error_message`
- `created_at`
- `updated_at`

Allowed directions:

- `upstream`
- `downstream`
- `unknown`

Allowed parse statuses:

- `parsed`
- `parse_failed`
- `duplicate`
- `needs_review`

Allowed match statuses:

- `not_matched`
- `single_candidate`
- `multiple_candidates`
- `matched_manually`

Allowed confirmation statuses:

- `draft`
- `ready`
- `confirmed`
- `ignored`

### `invoice_import_allocations`

Represents one draft or confirmed posting allocation for a source invoice.

Required fields:

- `id`
- `item_id`
- `direction`
- `upstream_contract_id`
- `downstream_contract_id`
- `amount`
- `tax_amount`
- `description`
- `status`
- `confirmed_by`
- `confirmed_at`
- `formal_invoice_id`
- `created_by`
- `created_at`
- `updated_at`

Allowed statuses:

- `draft`
- `confirmed`
- `cancelled`

For `upstream` allocations, `upstream_contract_id` must be set and `downstream_contract_id` must be null. For `downstream` allocations, `downstream_contract_id` must be set and `upstream_contract_id` must be null.

### `invoice_import_match_candidates`

Stores ranked contract recommendations for an item.

Required fields:

- `id`
- `item_id`
- `direction`
- `upstream_contract_id`
- `downstream_contract_id`
- `score`
- `matched_signals`
- `created_at`

`matched_signals` is JSON containing matched tax number, company name, contract code, project name, contract name, amount headroom, and keyword scores.

## Archive Processing

### Accepted Archive Shape

The import endpoint accepts `.zip` only.

Top-level archive:

```text
invoice_batch.zip
  invoice_001.zip
    invoice.pdf
    invoice.ofd
    invoice.xml
  invoice_002.zip
    invoice.pdf
    invoice.ofd
    invoice.xml
```

Each nested archive must contain exactly one XML file. PDF and OFD are stored when present. Missing PDF or OFD does not block parsing if XML is valid.

### Safe Extraction

Extraction must reject:

- Absolute paths.
- `..` path traversal.
- Symlinks.
- Nested archives deeper than one invoice subarchive.
- Individual files larger than configured limits.
- Batch archives larger than configured limits.

### XML Parsing

XML is the first release source of truth. The parser extracts:

- Invoice number.
- Invoice code or electronic invoice number when present.
- Invoice date.
- Seller name and tax number.
- Buyer name and tax number.
- Amount without tax.
- Tax amount.
- Total amount.
- Invoice type.
- Remarks.
- Line item names and amounts when available.

The parser should support multiple field aliases because electronic invoice XML variants may use different element names. Unknown XML fields should be preserved in `parsed_payload`.

## Contract Matching

Matching returns candidate contracts, not final postings.

### Scoring Signals

For upstream candidates:

- Exact match between invoice buyer tax number and `contracts_upstream.party_a_tax_no`.
- Fuzzy match between invoice buyer name and `contracts_upstream.party_a_name`.
- Contract code found in invoice remarks or line item text.
- Project name found in invoice remarks or line item text.
- Contract name found in invoice remarks or line item text.
- Invoice amount does not exceed remaining uninvoiced contract amount.

For downstream candidates:

- Exact match between invoice seller tax number and `contracts_downstream.party_b_tax_no`.
- Fuzzy match between invoice seller name and `contracts_downstream.party_b_name`.
- Contract code found in invoice remarks or line item text.
- Project name or contract name found in invoice remarks or line item text.
- Invoice amount does not exceed remaining uninvoiced contract amount.

### Candidate Outcomes

- Score >= 85 and only one clear candidate: `single_candidate`.
- Multiple candidates above threshold: `multiple_candidates`.
- No candidate above threshold: `not_matched`.

Even `single_candidate` items still require operator confirmation.

## API Design

Base prefix: `/api/v1/invoice-imports`

Endpoints:

- `POST /batches` uploads a top-level zip and starts processing.
- `GET /batches` lists import batches.
- `GET /batches/{batch_id}` returns batch summary and counters.
- `GET /batches/{batch_id}/items` lists source invoices in a batch.
- `GET /items/{item_id}` returns one item, attachments, candidates, and allocations.
- `POST /items/{item_id}/allocations` creates a draft allocation.
- `PUT /allocations/{allocation_id}` updates amount, target contract, or description.
- `DELETE /allocations/{allocation_id}` cancels a draft allocation.
- `POST /items/{item_id}/confirm` confirms all draft allocations for an item.
- `POST /items/{item_id}/ignore` marks an item ignored with a required reason.
- `POST /items/{item_id}/reprocess-match` recalculates candidate matches.

Permissions should use existing invoice permissions:

- Upload and view import batches: invoice view permission.
- Create or edit draft allocations: invoice create or edit permission.
- Confirm allocations: invoice create permission.
- Ignore imported invoice: invoice edit permission.

## Frontend Design

Add an `电子发票导入` page under the finance or contract management navigation.

Main views:

- Batch upload panel.
- Batch list with status counters.
- Import item table with filters for status, direction, duplicate, and matching result.
- Item detail drawer showing invoice fields, PDF/OFD/XML attachments, match candidates, and allocation rows.
- Allocation editor for choosing upstream/downstream contract and entering amount.
- Confirmation action that shows allocation sum, invoice total, and target contracts.

The UI should make unposted data visually distinct from formal invoice records. Confirmed imported invoices should remain visible in the workbench with links to the generated formal contract invoice rows.

## Error Handling

Each failed invoice item should remain visible with an actionable error code:

- `MISSING_XML`
- `MULTIPLE_XML_FILES`
- `INVALID_XML`
- `MISSING_COMPANY_TAX_NO`
- `UNKNOWN_DIRECTION`
- `DUPLICATE_INVOICE`
- `NO_MATCH_CANDIDATE`
- `ALLOCATION_AMOUNT_EXCEEDED`
- `CONFIRMATION_CONFLICT`

Batch-level failure should be reserved for upload failure, unsafe archive structure, or storage failure before any invoice item can be created.

## Security And Compliance

- Store original PDF, OFD, XML, and batch zip in MinIO under an `invoices/imports/` prefix.
- Serve attachments only through the existing protected file endpoint.
- Preserve raw XML for auditability.
- Record `created_by`, `confirmed_by`, and timestamps.
- Create audit log entries when a batch is uploaded and when an item is confirmed.
- Do not expose XML download to users without invoice view permission.
- Reject query-token file access, consistent with current protected file behavior.

## Testing Requirements

Backend tests:

- Safe archive extraction rejects traversal and unsafe nested paths.
- XML parser handles representative electronic invoice XML.
- Direction detection works for upstream, downstream, and unknown cases.
- Dedupe key generation is stable.
- Matching ranks tax number matches above fuzzy name matches.
- Allocation confirmation rejects over-allocation.
- Confirmation creates formal upstream and downstream invoice rows.
- Confirmation is idempotent for already confirmed items.

Frontend tests:

- Upload page renders batch status.
- Item table shows duplicate, unmatched, and ready states.
- Allocation editor validates amount totals before submit.
- Confirmation calls the correct API and refreshes the item state.

## Acceptance Criteria

- A top-level zip with multiple nested invoice zips can be uploaded.
- Valid XML invoices are parsed into source invoice items.
- PDF, OFD, and XML files are stored and linked to each import item.
- Duplicates are visible and blocked from normal confirmation.
- The system classifies invoices as upstream or downstream using fixed company tax number.
- The system recommends candidate contracts using tax number, names, keywords, and amount headroom.
- Operators can split one invoice across multiple contracts by entering allocation rows.
- Confirmation writes formal records into existing upstream or downstream invoice tables.
- Contract invoice totals and existing reports include confirmed imported invoices.
- All unconfirmed items remain outside formal contract financial totals.
