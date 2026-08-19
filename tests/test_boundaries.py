import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = "Dependencies point inward"
SERVICE_PROBE = ROOT / "extractlayer" / "service" / "probe.py"
DOMAIN_PROBE = ROOT / "extractlayer" / "domain" / "probe.py"


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
    SERVICE_PROBE.write_text("import extractlayer.repo\n\n__all__ = [\"extractlayer\"]\n")
    try:
        yield
    finally:
        SERVICE_PROBE.unlink()


@pytest.fixture
def domain_importing_config() -> Iterator[None]:
    DOMAIN_PROBE.write_text("import extractlayer.config\n\n__all__ = [\"extractlayer\"]\n")
    try:
        yield
    finally:
        DOMAIN_PROBE.unlink()


def test_the_tree_holds_the_layer_map() -> None:
    result = lint_imports()
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.usefixtures("service_importing_repo")
def test_a_service_importing_repo_breaks_the_contract() -> None:
    result = lint_imports()
    assert result.returncode != 0, result.stdout + result.stderr
    assert CONTRACT in result.stdout
    assert "extractlayer.service.probe -> extractlayer.repo" in result.stdout


@pytest.mark.usefixtures("domain_importing_config")
def test_a_domain_module_importing_config_breaks_the_contract() -> None:
    result = lint_imports()
    assert result.returncode != 0, result.stdout + result.stderr
    assert CONTRACT in result.stdout
    assert "extractlayer.domain.probe -> extractlayer.config" in result.stdout
