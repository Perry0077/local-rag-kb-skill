from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


class LocalRagKbSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(ROOT / "tools" / "rebuild_fixtures.py")], check=True)

    def run_command(self, args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=str(ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )

    def base_env(self, data_root: Path) -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "core" / "runtime")
        env["LOCAL_RAG_KB_HOST"] = "codex"
        env["LOCAL_RAG_KB_DATA_DIR"] = str(data_root)
        env["CHAT_BACKEND"] = "host"
        return env

    def test_ingest_and_query_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            data_root = Path(temp_dir) / "data"
            env = self.base_env(data_root)

            ingest_basic = self.run_command(
                [
                    sys.executable,
                    str(ROOT / "core" / "skill" / "scripts" / "kb_ingest.py"),
                    "--input",
                    str(FIXTURES / "sources" / "basic" / "launch_notes.md"),
                    "--local-test-embeddings",
                ],
                env,
            )
            self.assertIn("Updated docs: 1", ingest_basic.stdout)

            ingest_zip = self.run_command(
                [
                    sys.executable,
                    str(ROOT / "core" / "skill" / "scripts" / "kb_ingest.py"),
                    "--input",
                    str(FIXTURES / "input" / "nested_docs.zip"),
                    "--local-test-embeddings",
                ],
                env,
            )
            self.assertIn("Supported files: 2", ingest_zip.stdout)

            ingest_tar = self.run_command(
                [
                    sys.executable,
                    str(ROOT / "core" / "skill" / "scripts" / "kb_ingest.py"),
                    "--input",
                    str(FIXTURES / "input" / "mixed_docs.tar.gz"),
                    "--local-test-embeddings",
                ],
                env,
            )
            self.assertIn("Supported files: 2", ingest_tar.stdout)
            self.assertIn("Skipped files: 1", ingest_tar.stdout)

            ingest_txt = self.run_command(
                [
                    sys.executable,
                    str(ROOT / "core" / "skill" / "scripts" / "kb_ingest.py"),
                    "--input",
                    str(FIXTURES / "sources" / "basic" / "revenue_notes.txt"),
                    "--local-test-embeddings",
                ],
                env,
            )
            self.assertIn("Updated docs: 1", ingest_txt.stdout)

            ingest_repeat = self.run_command(
                [
                    sys.executable,
                    str(ROOT / "core" / "skill" / "scripts" / "kb_ingest.py"),
                    "--input",
                    str(FIXTURES / "sources" / "basic" / "revenue_notes.txt"),
                    "--local-test-embeddings",
                ],
                env,
            )
            self.assertIn("Unchanged docs: 1", ingest_repeat.stdout)

            query = self.run_command(
                [
                    sys.executable,
                    str(ROOT / "core" / "skill" / "scripts" / "kb_query.py"),
                    "--question",
                    "Why can one broken provider affect many products at once?",
                    "--emit-host-bundle",
                    "--local-test-embeddings",
                ],
                env,
            )
            bundle = json.loads(query.stdout)
            self.assertEqual(bundle["kb_name"], "default")
            self.assertIn("instructions", bundle)
            self.assertTrue(bundle["contexts"])
            self.assertTrue(bundle["references"])

            host_answer_error = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "core" / "skill" / "scripts" / "kb_query.py"),
                    "--question",
                    "Why can one broken provider affect many products at once?",
                    "--answer",
                    "--local-test-embeddings",
                ],
                cwd=str(ROOT),
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(host_answer_error.returncode, 0)
            self.assertIn("CHAT_BACKEND=host is handled by the host orchestration layer", host_answer_error.stderr)

            status = self.run_command(
                [
                    sys.executable,
                    str(ROOT / "core" / "skill" / "scripts" / "kb_status.py"),
                ],
                env,
            )
            self.assertIn("Documents:", status.stdout)
            self.assertIn("Chunks:", status.stdout)

            rebuild = self.run_command(
                [
                    sys.executable,
                    str(ROOT / "core" / "skill" / "scripts" / "kb_rebuild.py"),
                    "--local-test-embeddings",
                ],
                env,
            )
            self.assertIn("Rebuilt KB: default", rebuild.stdout)

    def test_build_targets(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_targets.py"), "--host", "all"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("Built openclaw", result.stdout)
        self.assertTrue((ROOT / "dist" / "codex" / "local-rag-kb" / "SKILL.md").exists())
        self.assertTrue((ROOT / "dist" / "openclaw" / "local-rag-kb" / "agents" / "openai.yaml").exists())
        self.assertTrue((ROOT / "dist" / "claude-code" / "local-rag-kb" / "SKILL.md").exists())
        self.assertIn(
            "LOCAL_RAG_KB_HOST=openclaw",
            (ROOT / "dist" / "openclaw" / "local-rag-kb" / ".env.example").read_text(encoding="utf-8"),
        )

    def test_openclaw_dist_package_smoke(self) -> None:
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_targets.py"), "--host", "openclaw"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        )

        skill_root = ROOT / "dist" / "openclaw" / "local-rag-kb"
        paths_module_path = skill_root / "runtime" / "local_rag_kb" / "paths.py"
        spec = importlib.util.spec_from_file_location("local_rag_kb_dist_paths", paths_module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.PROJECT_ROOT, skill_root.resolve())

        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["LOCAL_RAG_KB_DATA_DIR"] = str(Path(temp_dir) / "openclaw-data")
            env["CHAT_BACKEND"] = "host"

            ingest = self.run_command(
                [
                    sys.executable,
                    str(skill_root / "scripts" / "kb_ingest.py"),
                    "--host",
                    "openclaw",
                    "--input",
                    str(FIXTURES / "input" / "nested_docs.zip"),
                    "--local-test-embeddings",
                ],
                env,
            )
            self.assertIn("Updated docs: 2", ingest.stdout)

            query = self.run_command(
                [
                    sys.executable,
                    str(skill_root / "scripts" / "kb_query.py"),
                    "--host",
                    "openclaw",
                    "--question",
                    "Why can one outage hit many products at once?",
                    "--emit-host-bundle",
                    "--local-test-embeddings",
                ],
                env,
            )
            bundle = json.loads(query.stdout)
            self.assertEqual(bundle["kb_name"], "default")
            self.assertTrue(bundle["references"])


if __name__ == "__main__":
    unittest.main()
