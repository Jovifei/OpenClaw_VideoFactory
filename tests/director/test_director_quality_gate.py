from __future__ import annotations

from generate_video import _build_director_quality_report


def test_quality_gate_fails_closed_without_probe_media() -> None:
    report = _build_director_quality_report(
        job_id="director_quality",
        score={"score": 93},
        factual_brief=None,
        render_report_ref="render_report.json",
        render_report=None,
    )
    assert report["status"] == "failed"
    assert report["error"]["code"] == "director_quality_failed"
