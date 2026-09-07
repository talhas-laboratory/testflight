from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.audit_testflight_product_routes import audit_routes, plan_route  # noqa: E402


def test_every_product_module_has_a_passing_route_case() -> None:
    report = audit_routes(REPO_ROOT)

    assert report["status"] == "pass"
    assert report["routing_error"] == 0
    assert report["no_hit_correctness"] == 1.0
    assert report["live_retrieval_certified"] is False


def test_out_of_domain_query_returns_honest_no_hit() -> None:
    trace = plan_route("weather temperature Neptune next Thursday")

    assert trace["selected_route"] == "NO_HITS"
    assert trace["status"] == "no_hit"
