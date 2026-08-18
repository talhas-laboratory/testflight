"""Minimal composition-root CLI for Brand workspaces."""

import argparse
import shutil
from pathlib import Path

from testflight_brand import load_brand_fixture, load_brand_ontology, validate_brand_fixture


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="brand-lab")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate the canonical Brand ontology")
    validate.add_argument("--root", type=Path, default=Path.cwd())

    certify = commands.add_parser("certify", help="certify the minimal Brand fixture")
    certify.add_argument("--root", type=Path, default=Path.cwd())
    certify.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="fixture path (defaults to domains/brand/fixtures/minimal-brand/brand.yaml)",
    )

    init = commands.add_parser("init", help="initialize a concrete Brand workspace")
    init.add_argument("slug")
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--template", type=Path, default=None)
    return parser


def _init_workspace(slug: str, output: Path, template: Path | None) -> int:
    if not slug or any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for character in slug
    ):
        raise SystemExit("slug must contain lowercase letters, numbers, hyphens, or underscores")
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing workspace: {output}")
    source = template or Path(__file__).resolve().parents[4] / "workspaces/brand-template"
    shutil.copytree(source, output)
    for path in output.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".yaml", ".json"}:
            text = path.read_text()
            text = text.replace("brand/template", f"brand/{slug}")
            text = text.replace("brand:template", f"brand:{slug}")
            text = text.replace("<workspace_slug>", slug)
            text = text.replace("<projection_version>", "1")
            text = text.replace("status: template", "status: active")
            path.write_text(text)
    print(f"initialized workspace: {output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate":
        ontology, sources = load_brand_ontology(args.root)
        print(
            f"valid: ontology={ontology.id} version={ontology.version} "
            f"components={len(ontology.component_types)} "
            f"relations={len(ontology.relationship_types)} "
            f"sources={len(sources)}"
        )
        return 0
    if args.command == "certify":
        ontology, sources = load_brand_ontology(args.root)
        fixture_path = args.fixture or (
            args.root / "domains/brand/fixtures/minimal-brand/brand.yaml"
        )
        fixture = load_brand_fixture(fixture_path)
        validate_brand_fixture(fixture, ontology)
        print(
            f"certified: workspace={fixture.system.workspace_id} "
            f"components={len(fixture.components)} assertions={len(fixture.assertions)} "
            f"ontology_sources={len(sources)}"
        )
        return 0
    return _init_workspace(args.slug, args.output, args.template)


if __name__ == "__main__":
    raise SystemExit(main())
