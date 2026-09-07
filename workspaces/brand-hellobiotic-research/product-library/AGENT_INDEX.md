# Product library

## Mission

Route a stable product UID to the smallest product space that can answer the request without
turning an image asset, a product claim, or an end-user hypothesis into another kind of truth.

## Routes

| Need | Route | Returns |
| --- | --- | --- |
| Find a product or SKU | `product-index` | Stable product UID and linked spaces only |
| Product facts, variants, or physical specification | `product-knowledge-space` | Evidence-scoped product metadata |
| Product pack shot, angle, 3D file, or rights | `product-image-space` | Approved asset references and coverage status |
| Product purpose or pain-point relation | `product-purpose-space` | Typed relation with evidence/claim status |
| Product-to-end-user context | `product-end-user-connection-space` | Bounded context or held hypothesis |

## Retrieval

Resolve a product UID exactly first, then use BM25 only within the selected space. Use bounded
same-child hybrid retrieval only after an in-domain lexical no-hit. Never use an index or a
navigation contract as a factual answer. Return `NO_HITS`, `partial`, `hold`, or `branch` when
there is no appropriate approved record.

## Generation gate

An image workflow may use only an asset with `generation_allowed: true`, an active rights record,
and sufficient requested-angle coverage. Metadata alone cannot establish exact package likeness;
return `hold` when the required approved angle, multi-view reference, or 3D/CAD representation is
absent.
