import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = "Dependencies point inward"
PROBE = ROOT / "extractlayer" / "service" / "probe.py"


def lint_imports() -> subprocess.CompletedProcess[str]:
    executable = shutil.which("lint-imports")
    assert executable is not None, "import-linter is absent, so the layer map is unenforced"
    return subprocess.run(
        [executable, "--no-cache"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def service_importing_repo() -> Iterator[None]:
    PROBE.write_text("import extractlayer.repo\n\n__all__ = [\"extractlayer\"]\n")
    try:
        yield
    finally:
        PROBE.unlink()


def test_the_tree_holds_the_layer_map() -> None:
    result = lint_imports()
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.usefixtures("service_importing_repo")
def test_a_service_importing_repo_breaks_the_contract() -> None:
    result = lint_imports()
    assert result.returncode != 0, result.stdout + result.stderr
    assert CONTRACT in result.stdout
    assert "extractlayer.service.probe -> extractlayer.repo" in result.stdout
