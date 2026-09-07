import importlib.util
import json
import sys
from pathlib import Path


def _script_module():
    path = Path(__file__).resolve().parents[1] / "scripts/project_creative_field.py"
    spec = importlib.util.spec_from_file_location("project_creative_field_script", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_projection_cli_dry_run_rebuild_and_drift(tmp_path, capsys, monkeypatch) -> None:
    module = _script_module()
    records_path = tmp_path / "records.json"
    records_path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "record_type": "ReferenceAsset",
                        "payload": {
                            "asset_id": "asset:cli",
                            "project_id": "project:cli",
                            "source_id": "upload:cli",
                            "media_type": "image/jpeg",
                            "label": "cli reference",
                            "content_hash": "sha256:cli",
                            "source_uri": "blob://cli",
                            "recorded_at": "2026-09-03T00:00:00Z",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    common = [
        "--records-file",
        str(records_path),
        "--child-workspace-id",
        "child:cli",
        "--parent-workspace-id",
        "parent:cli",
        "--project-id",
        "project:cli",
        "--dataset-name",
        "creative_field_cli_staging",
    ]
    monkeypatch.setattr(sys, "argv", ["project_creative_field.py", *common, "--dry-run"])
    assert module.main() == 0
    assert json.loads(capsys.readouterr().out)["status"] == "dry_run"

    manifest_path = tmp_path / "manifest.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["project_creative_field.py", *common, "--rebuild", str(manifest_path)],
    )
    assert module.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "rebuilt"
    assert manifest_path.is_file()
    assert report["drift"]["status"] == "missing"
