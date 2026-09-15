# Ingestion Guide

This bundle is designed for deterministic reconstruction by another system.

## Source Of Truth

- `manifest.json` is the bundle entrypoint.
- `messages.json` is the source of truth for conversation reconstruction.
- `artifacts/` is the source of truth for binary and file assets.
- `transcript.md` is human-readable only.

## Ingestion Steps

1. Read `manifest.json`.
2. Verify `schema_version`.
3. Load `messages.json`.
4. Load `artifacts.json`.
5. Render messages in listed order.
6. Resolve `artifact_refs` against artifact IDs and files under `artifacts/`.
7. Treat artifacts with `download_status != "downloaded"` as metadata-only references.
8. Use `transcript.md` only as fallback display text.

## Embedded Spec Reference

The following project spec was used to produce this bundle:

# Conversation Bundle v1

## Purpose

This bundle format preserves a multimodal conversation in a portable folder layout that can be reconstructed by another system without scraping human-readable markdown.

## Canonical Layout

```text
conversation_bundle/
  manifest.json
  messages.json
  artifacts.json
  transcript.md
  INGESTION.md
  artifacts/
```

## Source Of Truth

- `manifest.json` is the bundle entrypoint.
- `messages.json` is the source of truth for conversation reconstruction.
- `artifacts.json` is the source of truth for artifact metadata and cross references.
- `artifacts/` is the source of truth for binary and file assets.
- `transcript.md` is a human-readable rendering and must not override structured data.

## manifest.json

Required fields:

- `schema_version`
- `bundle_type`
- `conversation_id`
- `title`
- `created_at`
- `files`
- `counts`

Example:

```json
{
  "schema_version": "1.0",
  "bundle_type": "conversation",
  "conversation_id": "conv_test_001",
  "title": "Smooth Microgestures on Mobile",
  "created_at": "2026-06-27T13:30:00Z",
  "source_url": "https://chatgpt.com/share/example",
  "files": {
    "messages": "messages.json",
    "artifacts_index": "artifacts.json",
    "transcript": "transcript.md",
    "ingestion": "INGESTION.md",
    "artifacts_dir": "artifacts"
  },
  "counts": {
    "messages": 2,
    "artifacts": 0
  }
}
```

## messages.json

`messages.json` stores a flat chronological message list.

Required message fields:

- `id`
- `role`
- `blocks`

Recommended message fields:

- `created_at`
- `text`
- `artifact_refs`
- `metadata`

Example:

```json
{
  "conversation_id": "conv_test_001",
  "messages": [
    {
      "id": "msg_0001",
      "role": "user",
      "created_at": "2026-06-27T13:30:00Z",
      "text": "Use this layout style.",
      "blocks": [
        {
          "type": "paragraph",
          "text": "Use this layout style."
        }
      ],
      "artifact_refs": [],
      "metadata": {}
    }
  ]
}
```

## Initial Block Schema

Supported initial block types:

- `paragraph`
- `heading`
- `list`
- `code`
- `table`
- `blockquote`
- `artifact_ref`

Unknown block types should be ignored safely or rendered via fallback.

## Artifact Schema

Artifacts are first-class bundle objects and must be stored separately from transcript text.

Required artifact fields:

- `id`
- `type`
- `role`
- `filename`
- `path`
- `mime_type`
- `source_message_id`
- `derived_from`

Recommended artifact fields:

- `sha256`
- `download_status`
- `public_url`
- `provider`
- `provider_ref`
- `metadata`

`path` and `sha256` may be `null` when the shared link exposes artifact metadata but not a public binary download.

Recommended `download_status` values:

- `downloaded`
- `downloadable`
- `metadata_only`

Example:

```json
{
  "id": "art_0001",
  "type": "image",
  "role": "uploaded",
  "filename": "art_0001_reference.png",
  "path": "artifacts/art_0001_reference.png",
  "mime_type": "image/png",
  "sha256": "abc123",
  "source_message_id": "msg_0001",
  "derived_from": [],
  "metadata": {
    "width": 512,
    "height": 512
  }
}
```

## Relationship Rules

- A message may reference zero or more artifacts via `artifact_refs`.
- An artifact may be referenced by multiple messages.
- An artifact must point back to its origin via `source_message_id`.
- Derived artifacts must declare lineage via `derived_from`.
- `derived_from` contains artifact IDs, not filenames.

This allows systems to reconstruct provenance, reuse assets across messages, and track generated outputs from earlier inputs.

## Ingestion Rules

1. Read `manifest.json`.
2. Verify `schema_version`.
3. Load `messages.json`.
4. Treat message order in `messages.json` as canonical conversation order.
5. Resolve `artifact_refs` against IDs in `artifacts/` and future artifact manifests.
6. If an artifact has `download_status != "downloaded"`, treat it as a metadata-only reference.
7. Use `transcript.md` only as a human-readable fallback.
