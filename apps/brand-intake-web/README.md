# Brand Intake Web — experience prototype

This dependency-free shell tests the founder-facing look and feel before the production Ionic React
application is scaffolded. It contains interactive notebook, clarification, and provisional World
review views. It does not call a backend or record real audio.

Run it from the repository root:

```bash
python3 -m http.server 4317 --bind 127.0.0.1 --directory apps/brand-intake-web
```

Then open `http://localhost:4317/`. Use the root path; the shell changes views in place and does not
define routes such as `/capture`.

The notebook text is stored only in browser `localStorage`. The voice control simulates recording
state and timing. Attachments remain browser-only display chips.

Production implementation should preserve this interaction model while replacing the shell with
the planned Ionic/React, Dexie, FastAPI, Supabase, Uppy, Docling, and transcription modules.
