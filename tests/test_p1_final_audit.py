from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.p1_final_audit import AuditFailure, REQUIRED_ARTIFACTS, _fixed_report_outputs, audit_candidate, main
from src.factory.db import CandidateStore
from src.factory.state import next_state


class FinalAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.jobs_root = self.root / "jobs" / "p1_candidate"
        self.jobs_root.mkdir(parents=True)
        (self.root / "reports").mkdir()
        self.store = CandidateStore(self.root / "state" / "candidate.sqlite3")
        self.store.initialize()
        self.roles = {
            "fix001_nvenc": ("FIX-001", "protocol-frame", "h264_nvenc"),
            "fix001_cpu": ("FIX-001", "protocol-frame", "libx264"),
            "engineering_case": ("FIX-002", "engineering-case", None),
            "flow_diagram": ("FIX-003", "flow-diagram", None),
            "code_explainer": ("SAMPLE-CODE-001", "code-explainer", None),
        }
        self.job_ids: dict[str, str] = {}
        packages = []
        for index, (role, (fixture, template, encoder)) in enumerate(self.roles.items()):
            job = self.store.create_job(fixture, f"audit-{index}", template, role)["job_id"]
            state = "NEW"
            while state != "PENDING_REVIEW":
                state = next_state(state) or "PENDING_REVIEW"
                self.store.advance(job, state)
            self.job_ids[role] = job
            self._write_job(job, fixture, template, encoder)
            item = {"fixture": fixture, "job_id": job}
            if encoder:
                item["encoder"] = encoder
            else:
                item["template"] = template
            packages.append(item)
        self.selection = self.root / "reports" / "selection.json"
        self.selection.write_text(json.dumps({"packages": packages}), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_job(self, job_id: str, fixture: str, template: str, encoder: str | None) -> None:
        package = self.jobs_root / job_id
        package.mkdir()
        for name in REQUIRED_ARTIFACTS:
            if name.endswith(".json"):
                payload: object = {}
                if name == "quality_report.json":
                    payload = {"status": "pass", "checks": {"media": True}}
                elif name == "render_input.json":
                    payload = {"template": template}
                elif name == "run_metrics.json":
                    payload = {"render": {"peak_cpu_percent": 1.0}}
                elif name == "job.json":
                    payload = {"fixture_id": fixture, "job_id": job_id, "state": "PENDING_REVIEW"}
                (package / name).write_text(json.dumps(payload), encoding="utf-8")
            else:
                (package / name).write_bytes(b"candidate")
        (package / "render_manifest.json").write_text(
            json.dumps({"renderer": "remotion", "network_called": False, "width": 1080, "height": 1920, "fps": 30, "resolved_duration_seconds": 40.0, "master": {"encoder": encoder or "libx264"}}),
            encoding="utf-8",
        )
        delivery = {"schema_version": "2.0", "mode": "dry-run", "network_called": False, "lark_cli_called": False, "job_id": job_id, "candidate_state": "QUALITY_CHECK", "delivery_key": hashlib.sha256(f"{job_id}|offline-dry-run|v2".encode("utf-8")).hexdigest(), "artifacts": []}
        for name in ("final_master.mp4", "feishu_preview.mp4", "cover.png", "captions.srt", "quality_report.json"):
            path = package / name
            delivery["artifacts"].append({"name": name, "relative_path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size_bytes": path.stat().st_size})
        delivery["preview"] = next(item for item in delivery["artifacts"] if item["name"] == "feishu_preview.mp4")
        delivery["quality_report"] = next(item for item in delivery["artifacts"] if item["name"] == "quality_report.json")
        (package / "delivery_manifest.json").write_text(json.dumps(delivery), encoding="utf-8")
        self.store.create_delivery(
            delivery["delivery_key"],
            job_id,
            {key: value for key, value in delivery.items() if key != "delivery_key"},
        )
        proof = {
            "schema_version": "1.0",
            "mode": "offline-dry-run",
            "status": "completed",
            "job_id": job_id,
            "delivery_key": delivery["delivery_key"],
            "delivery_manifest_sha256": hashlib.sha256(
                (package / "delivery_manifest.json").read_bytes()
            ).hexdigest(),
            "runner_source_sha256": hashlib.sha256(
                (Path(__file__).resolve().parents[1] / "scripts" / "p1_dry_run_delivery_runner.py").read_bytes()
            ).hexdigest(),
            "guard": {
                "policy": "deny_transport_runtime_v1",
                "socket_events": 0,
                "process_events": 0,
            },
            "evidence_level": "local_self_attestation",
            "artifacts": delivery["artifacts"],
            "completed_at": "2026-07-29T00:00:00Z",
        }
        (package / "dry_run_execution_proof.json").write_text(json.dumps(proof), encoding="utf-8")
        for name in REQUIRED_ARTIFACTS:
            path = package / name
            self.store.record_artifact(job_id, name, f"jobs/p1_candidate/{job_id}/{name}", hashlib.sha256(path.read_bytes()).hexdigest())

    @staticmethod
    def _media(_: Path) -> dict[str, object]:
        return {"width": 1080, "height": 1920, "fps": 30.0, "duration_seconds": 40.0, "audio_codec": "aac"}

    def _audit(self) -> dict[str, object]:
        return audit_candidate(self.selection, self.store, project_root=self.root, candidate_jobs_root=self.jobs_root, media_validator=self._media)

    def test_valid_selection_passes_with_all_five_roles(self) -> None:
        result = self._audit()
        self.assertEqual(result["status"], "P1_OFFLINE_REVIEW_PACKAGE_LIMITED_SELF_ATTESTATION")
        self.assertEqual(set(result["jobs"]), set(self.roles))

    def test_repository_relative_selection_path_passes(self) -> None:
        result = audit_candidate(
            Path("reports/selection.json"),
            self.store,
            project_root=self.root,
            candidate_jobs_root=self.jobs_root,
            media_validator=self._media,
        )
        self.assertEqual(result["candidate_selection"], "reports/selection.json")

    def test_missing_artifact_fails_closed(self) -> None:
        (self.jobs_root / self.job_ids["fix001_nvenc"] / "voice.wav").unlink()
        with self.assertRaisesRegex(AuditFailure, "artifact_missing"):
            self._audit()

    def test_database_hash_mismatch_fails_closed(self) -> None:
        path = self.jobs_root / self.job_ids["fix001_nvenc"] / "voice.wav"
        path.write_bytes(b"changed")
        with self.assertRaisesRegex(AuditFailure, "artifact_hash_mismatch"):
            self._audit()

    def test_render_manifest_database_record_is_required(self) -> None:
        job = self.job_ids["fix001_nvenc"]
        with self.store._transaction() as connection:
            connection.execute(
                "DELETE FROM artifacts WHERE job_id = ? AND artifact_type = ?",
                (job, "render_manifest.json"),
            )
        with self.assertRaisesRegex(AuditFailure, "artifact_database_missing"):
            self._audit()

    def test_render_manifest_tamper_fails_at_hash_boundary(self) -> None:
        path = self.jobs_root / self.job_ids["fix001_nvenc"] / "render_manifest.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["audit_note"] = "tampered"
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(AuditFailure, "artifact_hash_mismatch"):
            self._audit()

    def test_unsafe_database_path_fails_closed(self) -> None:
        job = self.job_ids["fix001_nvenc"]
        self.store.record_artifact(job, "voice.wav", "C:/private/voice.wav", "0" * 64)
        with self.assertRaisesRegex(AuditFailure, "unsafe_artifact_path"):
            self._audit()

    def test_live_delivery_flag_fails_closed(self) -> None:
        path = self.jobs_root / self.job_ids["fix001_nvenc"] / "delivery_manifest.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["network_called"] = True
        path.write_text(json.dumps(value), encoding="utf-8")
        self.store.record_artifact(self.job_ids["fix001_nvenc"], "delivery_manifest.json", f"jobs/p1_candidate/{self.job_ids['fix001_nvenc']}/delivery_manifest.json", hashlib.sha256(path.read_bytes()).hexdigest())
        with self.assertRaisesRegex(AuditFailure, "delivery_not_dry_run"):
            self._audit()

    def test_delivery_manifest_unknown_or_unsafe_nested_field_fails_closed(self) -> None:
        job = self.job_ids["fix001_nvenc"]
        path = self.jobs_root / job / "delivery_manifest.json"
        for mutation in (
            lambda value: value.__setitem__("unexpected", "value"),
            lambda value: value["artifacts"][0].__setitem__("unexpected", "value"),
            lambda value: value["artifacts"][0].__setitem__("sha256", "not-a-hash"),
            lambda value: value["artifacts"][0].__setitem__("size_bytes", True),
            lambda value: value.__setitem__("preview", value["artifacts"][0]),
        ):
            with self.subTest(mutation=mutation):
                original = json.loads(path.read_text(encoding="utf-8"))
                value = json.loads(json.dumps(original))
                mutation(value)
                path.write_text(json.dumps(value), encoding="utf-8")
                self.store.record_artifact(job, "delivery_manifest.json", f"jobs/p1_candidate/{job}/delivery_manifest.json", hashlib.sha256(path.read_bytes()).hexdigest())
                with self.assertRaisesRegex(AuditFailure, "delivery_contract_invalid"):
                    self._audit()
                path.write_text(json.dumps(original), encoding="utf-8")
                self.store.record_artifact(job, "delivery_manifest.json", f"jobs/p1_candidate/{job}/delivery_manifest.json", hashlib.sha256(path.read_bytes()).hexdigest())

    def test_dry_run_proof_unknown_nested_or_non_utc_value_fails_closed(self) -> None:
        job = self.job_ids["fix001_nvenc"]
        path = self.jobs_root / job / "dry_run_execution_proof.json"
        for mutation, code in (
            (lambda value: value.__setitem__("unexpected", "value"), "dry_run_proof_unsafe"),
            (lambda value: value["artifacts"][0].__setitem__("unexpected", "value"), "dry_run_proof_artifact_mismatch"),
            (lambda value: value.__setitem__("completed_at", "2026-07-29T00:00:00"), "dry_run_proof_invalid"),
        ):
            with self.subTest(code=code):
                original = json.loads(path.read_text(encoding="utf-8"))
                value = json.loads(json.dumps(original))
                mutation(value)
                path.write_text(json.dumps(value), encoding="utf-8")
                self.store.record_artifact(job, "dry_run_execution_proof.json", f"jobs/p1_candidate/{job}/dry_run_execution_proof.json", hashlib.sha256(path.read_bytes()).hexdigest())
                with self.assertRaisesRegex(AuditFailure, code):
                    self._audit()
                path.write_text(json.dumps(original), encoding="utf-8")
                self.store.record_artifact(job, "dry_run_execution_proof.json", f"jobs/p1_candidate/{job}/dry_run_execution_proof.json", hashlib.sha256(path.read_bytes()).hexdigest())

    def test_dry_run_proof_requires_local_self_attestation_label(self) -> None:
        job = self.job_ids["fix001_nvenc"]
        path = self.jobs_root / job / "dry_run_execution_proof.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["evidence_level"] = "guarded_local_runner"
        path.write_text(json.dumps(value), encoding="utf-8")
        self.store.record_artifact(job, "dry_run_execution_proof.json", f"jobs/p1_candidate/{job}/dry_run_execution_proof.json", hashlib.sha256(path.read_bytes()).hexdigest())
        with self.assertRaisesRegex(AuditFailure, "dry_run_proof_invalid"):
            self._audit()

    def test_delivery_manifest_database_mismatch_fails_closed(self) -> None:
        path = self.jobs_root / self.job_ids["fix001_nvenc"] / "delivery_manifest.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["artifacts"][0]["sha256"] = "0" * 64
        path.write_text(json.dumps(value), encoding="utf-8")
        self.store.record_artifact(
            self.job_ids["fix001_nvenc"],
            "delivery_manifest.json",
            f"jobs/p1_candidate/{self.job_ids['fix001_nvenc']}/delivery_manifest.json",
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        with self.assertRaisesRegex(AuditFailure, "delivery_database_manifest_mismatch"):
            self._audit()

    def test_delivery_database_mode_or_status_tamper_fails_closed(self) -> None:
        job = self.job_ids["fix001_nvenc"]
        manifest = json.loads(
            (self.jobs_root / job / "delivery_manifest.json").read_text(encoding="utf-8")
        )
        for column, value in (("mode", "live"), ("status", "sent")):
            with self.subTest(column=column):
                with self.store._transaction() as connection:
                    connection.execute(
                        f"UPDATE deliveries SET {column} = ? WHERE delivery_key = ?",
                        (value, manifest["delivery_key"]),
                    )
                with self.assertRaisesRegex(AuditFailure, "delivery_database_state_invalid"):
                    self._audit()
                with self.store._transaction() as connection:
                    connection.execute(
                        f"UPDATE deliveries SET {column} = ? WHERE delivery_key = ?",
                        ("dry-run" if column == "mode" else "recorded", manifest["delivery_key"]),
                    )

    def test_delivery_database_duplicate_json_key_maps_to_audit_failure(self) -> None:
        job = self.job_ids["fix001_nvenc"]
        manifest = json.loads(
            (self.jobs_root / job / "delivery_manifest.json").read_text(encoding="utf-8")
        )
        database_manifest = {key: value for key, value in manifest.items() if key != "delivery_key"}
        tampered = json.dumps(database_manifest, ensure_ascii=False)
        tampered = tampered.replace(
            '"candidate_state": "QUALITY_CHECK"',
            '"candidate_state": "C:/private", "candidate_state": "QUALITY_CHECK"',
            1,
        )
        with self.store._transaction() as connection:
            connection.execute(
                "UPDATE deliveries SET manifest_json = ? WHERE delivery_key = ?",
                (tampered, manifest["delivery_key"]),
            )
        with self.assertRaisesRegex(AuditFailure, "delivery_database_json_invalid"):
            self._audit()

    def test_dry_run_proof_guard_counter_fails_closed(self) -> None:
        job = self.job_ids["fix001_nvenc"]
        path = self.jobs_root / job / "dry_run_execution_proof.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["guard"]["socket_events"] = 1
        path.write_text(json.dumps(value), encoding="utf-8")
        self.store.record_artifact(
            job,
            "dry_run_execution_proof.json",
            f"jobs/p1_candidate/{job}/dry_run_execution_proof.json",
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        with self.assertRaisesRegex(AuditFailure, "dry_run_proof_guard_invalid"):
            self._audit()

    def test_sensitive_metrics_field_fails_closed(self) -> None:
        path = self.jobs_root / self.job_ids["fix001_nvenc"] / "run_metrics.json"
        path.write_text(json.dumps({"token": "redacted"}), encoding="utf-8")
        self.store.record_artifact(self.job_ids["fix001_nvenc"], "run_metrics.json", f"jobs/p1_candidate/{self.job_ids['fix001_nvenc']}/run_metrics.json", hashlib.sha256(path.read_bytes()).hexdigest())
        with self.assertRaisesRegex(AuditFailure, "metrics_sensitive_field"):
            self._audit()

    def test_wrong_encoder_fails_closed(self) -> None:
        job = self.job_ids["fix001_nvenc"]
        path = self.jobs_root / job / "render_manifest.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["master"]["encoder"] = "libx264"
        path.write_text(json.dumps(value), encoding="utf-8")
        self.store.record_artifact(
            job,
            "render_manifest.json",
            f"jobs/p1_candidate/{job}/render_manifest.json",
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        with self.assertRaisesRegex(AuditFailure, "encoder_mismatch"):
            self._audit()

    def test_artifact_index_includes_render_manifest_hash(self) -> None:
        result = self._audit()
        evidence = result["jobs"]["fix001_nvenc"]["artifacts"]
        entry = next(item for item in evidence if item["artifact_type"] == "render_manifest.json")
        path = self.jobs_root / self.job_ids["fix001_nvenc"] / "render_manifest.json"
        self.assertEqual(entry["relative_path"], f"jobs/p1_candidate/{self.job_ids['fix001_nvenc']}/render_manifest.json")
        self.assertEqual(entry["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_duplicate_role_selection_fails_closed(self) -> None:
        value = json.loads(self.selection.read_text(encoding="utf-8"))
        value["packages"].append(dict(value["packages"][0]))
        self.selection.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(AuditFailure, "candidate_selection"):
            self._audit()

    def test_forbidden_promotion_artifact_fails_closed(self) -> None:
        (self.root / "reports" / "P1_READY.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(AuditFailure, "forbidden_promotion_artifact"):
            self._audit()

    def test_final_audit_cli_rejects_arbitrary_output_override(self) -> None:
        with self.assertRaises(SystemExit):
            main(["--output-json", "PROJECT_STATUS.yaml"])

    def test_fixed_report_outputs_stay_under_canonical_reports_root(self) -> None:
        with patch("scripts.p1_final_audit.ROOT", self.root):
            outputs = _fixed_report_outputs()
        self.assertEqual({path.name for path in outputs}, {
            "P1_FINAL_AUDIT_059.json",
            "P1_FINAL_AUDIT_059.md",
            "P1_FINAL_ARTIFACT_INDEX_059.json",
        })
        self.assertTrue(all(path.parent == (self.root / "reports").resolve() for path in outputs))

    def test_symlinked_reports_root_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            root = Path(temporary_root)
            alternate = root / "alternate_reports"
            alternate.mkdir()
            reports = root / "reports"
            try:
                reports.symlink_to(alternate, target_is_directory=True)
            except OSError:
                self.skipTest("symbolic links unavailable")
            with patch("scripts.p1_final_audit.ROOT", root):
                with self.assertRaisesRegex(AuditFailure, "report_output_root_unsafe"):
                    _fixed_report_outputs()

    def test_dangling_output_symlink_fails_closed_without_symlink_privilege(self) -> None:
        original_is_symlink = Path.is_symlink

        def simulated_is_symlink(path: Path) -> bool:
            return path.name == "P1_FINAL_AUDIT_059.json" or original_is_symlink(path)

        with patch.object(Path, "is_symlink", new=simulated_is_symlink):
            with patch("scripts.p1_final_audit.ROOT", self.root):
                with self.assertRaisesRegex(AuditFailure, "report_output_path_unsafe"):
                    _fixed_report_outputs()


if __name__ == "__main__":
    unittest.main()
