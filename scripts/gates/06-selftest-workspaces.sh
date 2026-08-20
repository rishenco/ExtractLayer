#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
. scripts/lib/files.sh
. scripts/lib/selftest.sh

[ "${1:-}" = "--describe" ] && { echo "Workspace gates still fire on known violations."; exit 0; }

fixture ws1/package.json '{"name":"fixture","scripts":{}}'
expect 50-architecture.sh 1 "workspace without boundary config is caught"
expect 60-workspaces.sh 1 "workspace without a check script is caught"

add_file ws2/.dependency-cruiser.js 'module.exports = { forbidden: [] }'
fixture ws2/package.json '{"name":"fixture","scripts":{"check":"true"}}'
expect 50-architecture.sh 0 "node workspace with a boundary config passes"

add_file gows/.go-arch-lint.yml 'version: 3'
fixture gows/go.mod 'module fixture'
expect 50-architecture.sh 0 "go workspace with a boundary config passes"

add_file pyws/pyproject.toml '[tool.importlinter]
root_package = "fixture"
[tool.ruff]
[tool.mypy]'
fixture pyws/pyproject.toml "$(cat "$WORK/pyws/pyproject.toml")"
expect 50-architecture.sh 0 "python workspace with importlinter contracts passes"
expect 60-workspaces.sh 0 "python workspace with no sources and configured tooling passes"

LAYERS='
contracts = [{name = "Dependencies point inward", type = "layers", layers = ["fixture.high", "fixture.low"]}]'

py_boundary() {
  local dir="$1" contracts="$2" high="$3" low="$4"
  add_file "$dir/fixture/__init__.py" ''
  add_file "$dir/fixture/high/__init__.py" "$high"
  add_file "$dir/fixture/mid/__init__.py" ''
  add_file "$dir/fixture/low/__init__.py" "$low"
  add_file "$dir/pyproject.toml" "[tool.importlinter]
root_packages = [\"fixture\"]$contracts"
  printf '%s\n' "$WORK/$dir/pyproject.toml" >"$WORK/list"
}

py_boundary pybound "$LAYERS" 'import fixture.low' ''
expect 50-architecture.sh 0 "a layer map the tree obeys passes"

py_boundary pycontainer '
contracts = [{name = "Inward", type = "layers", containers = ["fixture"], layers = ["high", "low"]}]' 'import fixture.low' ''
expect 50-architecture.sh 0 "layers named relative to a container pass"

py_boundary pyloose "$LAYERS" '' 'import fixture.high'
expect 50-architecture.sh 1 "a module importing the layer above it is caught"

py_boundary pypartial '
contracts = [{name = "Inward", type = "layers", layers = ["fixture.high"]}]' '' ''
expect 50-architecture.sh 1 "a contract naming one layer forbids nothing"

py_boundary pytyped '
contracts = [{name = "Inward", type = "forbidden", source_modules = ["fixture.high"], forbidden_modules = ["fixture.absent"]}]' '' ''
expect 50-architecture.sh 1 "a contract of another type does not stand in for the layer map"

py_boundary pystray '
contracts = [{name = "Inward", type = "forbidden", layers = ["fixture.high", "fixture.low"], source_modules = ["fixture.high"], forbidden_modules = ["fixture.absent"]}]' '' ''
expect 50-architecture.sh 1 "a layers key on a contract of another type is not a layer map"

py_boundary pycolon '
contracts = [{name = "Inward", type = "layers", layers = ["fixture.high : fixture.mid", "fixture.low"]}]' 'import fixture.low' ''
expect 50-architecture.sh 0 "layers joined by the non-independent delimiter pass"

py_boundary pyname '
contracts = [{name = "fixture.low._boundary_probe -> fixture.absent", type = "layers", layers = ["(fixture.absent)", "fixture.low"]}]' '' ''
expect 50-architecture.sh 1 "a contract named after the probe chain is not a refusal"

py_boundary pyignore "$LAYERS
ignore_imports = [\"fixture.low -> fixture.high\"]" 'import fixture.low' ''
expect 50-architecture.sh 1 "an exempted import is not an enforced boundary"

py_boundary pyescaped "$LAYERS
\"ignore_import\\u0073\" = [\"fixture.low -> fixture.high\"]" 'import fixture.low' ''
expect 50-architecture.sh 1 "an exemption written as an escaped key is still an exemption"


py_boundary pyspace "$LAYERS" 'import fixture.low' ''
add_file pyspace/fixture/relay/crosser.py 'import fixture.high'
expect 50-architecture.sh 1 "a package import-linter cannot analyse is caught"

py_boundary pydeep "$LAYERS" 'import fixture.low' ''
add_file pydeep/fixture/relay/deep/__init__.py 'import fixture.high'
expect 50-architecture.sh 1 "a namespace directory whose python sits below it is caught"

py_boundary pylink "$LAYERS" 'import fixture.low' ''
add_file pylink/outside/deep/__init__.py 'import fixture.high'
mkdir -p "$WORK/pylink/fixture/relay"
ln -s "$WORK/pylink/outside/deep" "$WORK/pylink/fixture/relay/deep"
expect 50-architecture.sh 1 "a module behind a directory symlink is caught"

py_boundary pycache "$LAYERS" 'import fixture.low' ''
add_file pycache/fixture/low/__pycache__/evil.py 'import fixture.high'
expect 50-architecture.sh 1 "a module hidden in __pycache__ is caught"

py_boundary pycancel "$LAYERS" 'import fixture.low' ''
add_file pycancel/fixture/twin/__init__.py ''
ln -s "$WORK/pycancel/fixture/twin" "$WORK/pycancel/fixture/mirror"
add_file pycancel/fixture/hide/crosser.py 'import fixture.high'
expect 50-architecture.sh 1 "a symlinked package does not offset a module nothing analysed"

py_boundary pyunreadable "$LAYERS" 'import fixture.low' ''
add_file pyunreadable/.importlinter '[importlinter]
root_packages =
    fixture

[importlinter:contract:1]
name = Inward
type = layers
layers =
    fixture.high
    fixture.low'
add_file pyunreadable/pyproject.toml "[tool.importlinter]
root_packages = [\"absent\"]$LAYERS"
expect 50-architecture.sh 1 "a helper that cannot run is not a clean tree"

py_boundary elsewhere/pysymroot "$LAYERS" 'import fixture.low' ''
add_file elsewhere/pysymroot/fixture/hide/crosser.py 'import fixture.high'
mkdir -p "$WORK/pysymroot"
ln -s "$WORK/elsewhere/pysymroot/fixture" "$WORK/pysymroot/fixture"
cp "$WORK/elsewhere/pysymroot/pyproject.toml" "$WORK/pysymroot/pyproject.toml"
printf '%s\n' "$WORK/pysymroot/pyproject.toml" >"$WORK/list"
expect 50-architecture.sh 1 "a workspace whose package is a symlink is not skipped"

py_boundary nested/deeper/pyrelative "$LAYERS" 'import fixture.low' ''
realpath --relative-to=. "$WORK/nested/deeper/pyrelative/pyproject.toml" >"$WORK/list"
expect 50-architecture.sh 0 "a workspace named by a relative path is read where it lives"

add_file pyprivate/fixture/__init__.py ''
fixture pyprivate/pyproject.toml '[tool.importlinter]
root_packages = ["fixture"]'
expect 50-architecture.sh 1 "a package with no layers contract is caught"

add_file gows2/.golangci.yml 'linters:
  enable: [govet]'
fixture gows2/go.mod 'module fixture'
expect_silent_about 60-workspaces.sh 'no .golangci config' "a present golangci config is detected"

fixture lint1/package.json '{"name":"fixture","scripts":{"check":"true"}}'
expect 55-lint-config.sh 1 "a workspace without a linter config is caught"

add_file lint2/eslint.config.js 'export default []'
add_file lint2/bad.ts '// explains the obvious
export const a = 1'
printf '%s\n%s\n' "$WORK/lint2/package.json" "$WORK/lint2/bad.ts" >"$WORK/list"
add_file lint2/package.json '{"name":"fixture","scripts":{"check":"true"}}'
expect 10-comments.sh 0 "a linted workspace is no longer scanned by the floor"

printf '%s\n' "$WORK/lint2/bad.ts" >"$WORK/list"
expect 10-comments.sh 1 "the floor still scans a file outside any linted workspace"

add_file bad.sh '# explains the loop
echo hi'
add_file pyproject.toml '[tool.ruff]
line-length = 99'
printf '%s\n%s\n' "$WORK/pyproject.toml" "$WORK/bad.sh" >"$WORK/list"
expect 10-comments.sh 1 "a root workspace does not retire the floor for what its linter cannot parse"

if command -v npm >/dev/null 2>&1; then
  mkdir -p "$WORK/ws2/node_modules"
  fixture ws2/package.json '{"name":"fixture","version":"1.0.0","scripts":{"check":"true"}}'
  expect 60-workspaces.sh 0 "node workspace with a passing check script passes"
else
  echo "npm not installed — skipped the 60-workspaces pass case"
fi

py_boundary pyfilter '
contracts = [{name = "Inward", type = "forbidden", layers = ["fixture.high", "fixture.low"], source_modules = ["fixture.high"], forbidden_modules = ["fixture.absent"]}]' '' ''
if [ -n "$(el_boundary_probes "$WORK/pyfilter/pyproject.toml")" ]; then
  found=1
  echo "el_boundary_probes: derives a probe from a contract that is not a layers contract"
fi

add_file pyreads/fixture/__init__.py ''
add_file pyreads/.importlinter '[importlinter]
IGNORE_IMPORTS =
    fixture.low -> fixture.high'
add_file pyreads/pyproject.toml '[tool.importlinter]
root_packages = ["fixture"]'
if [ -z "$(el_exempted_imports "$WORK/pyreads/pyproject.toml")" ]; then
  found=1
  echo "el_exempted_imports: misses an exemption configparser would lowercase"
fi

[ "$found" -eq 0 ] && exit 0
echo
echo "A gate that stopped firing reports success it cannot back."
exit 1
