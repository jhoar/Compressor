<!-- Copilot instructions for Compressor repository -->

# Copilot instructions — Compressor

If files referenced below are missing, stop and ask the maintainer where the
source or manifests live (other branch, submodule, or external repo).

Summary (what to know immediately)
- This repo currently contains small tooling to create .cbz archives: `make-cbz.ps1`
  and `make_cbz.py` at the repository root. Both scripts target "leaf"
  directories (directories that contain files but no descendant directories with
  files) and produce a `.cbz` per leaf.
- Default behavior: when no explicit output directory is provided, each
  archive is written into the parent directory of the leaf folder.
- Both scripts support a dry-run mode and verbose output:
  - PowerShell: `.	ools
un` style — use `-DryRun` and `-Verbose`.
  - Python: `--dry-run` and `--verbose`.

What to do first (must-do checklist)
1. List the repository root to locate code and scripts. Prefer local inspection
   over assumptions. If the repo is empty, ask where sources live.
2. Run the Python dry-run to preview leaf directories and destinations:
   `python .\make_cbz.py -r . --dry-run --verbose`
3. When creating archives use a temporary branch and include a short PR note
   explaining verification steps (commands run, files produced).

Project conventions and gotchas
- Archives are named after the leaf directory (e.g., `chapter1.cbz`). If
  multiple leaves share the same name the scripts append `_1`, `_2`, ... in
  the destination folder.
- Hidden files (names starting with `.`) are ignored by default.
- The PowerShell script uses `Compress-Archive` and targets PowerShell 5.1
  compatibility; the Python script is cross-platform (Python 3.6+).

Developer workflows
- To preview actions (safe):
  - PowerShell: `.	ools\make-cbz.ps1 -RootPath . -DryRun -Verbose`
  - Python: `python .\make_cbz.py -r . --dry-run --verbose`
- To create archives and write them next to source folders (default):
  - PowerShell: `.	ools\make-cbz.ps1 -RootPath .`
  - Python: `python .\make_cbz.py -r .`
- To write all archives into a single folder use the output option:
  - PowerShell: `-OutputDir .\archives`
  - Python: `-o .\archives`

When to ask the maintainer
- Repo lacks source files or build manifests.
- You require secrets, private feeds, or infra to run tests.

Safety notes
- Never embed or expose credentials. If a task requires secrets, ask for
  ephemeral test credentials or instructions for a local mock.
- Use dry-run and verbose modes before any destructive changes.

If this file is out of date, tell me where source code or build manifests
actually live and I will update these instructions.
<!--
  Purpose: Guidance for AI coding agents working on this repository.
  Note: This repo currently contains no discoverable source files or READMEs
  (search returned no matches). The instructions below therefore focus on
  how to quickly discover project structure, build/test workflows, and
  safe next-steps to make productive changes.
-->

# Copilot instructions for Compressor

Keep this short and actionable. If you (the AI) cannot find the files or
evidence referenced below, stop and ask the human maintainer for the next
location of the source (branch, submodule, or private package feed).

## Quick facts (repo state)
- At time of creation this repository root contains no README or AGENT files
  and a glob search returned no conventional project manifests. Start by
  verifying where the project's source actually lives (other branch/submodule
  or external repo).

## First actions (must do)
1. List the repository root and `src/`, `cmd/`, `pkg/` (or equivalent) to find
   code. If empty, check branches and submodules and ask the maintainer.
2. Search for common build manifests: `package.json`, `pyproject.toml`,
   `go.mod`, `Cargo.toml`, `Makefile`, `Dockerfile`. Use those files to infer
   language and build commands.
3. If you create or modify files, keep changes minimal and explain why in the
   commit message. Prefer a single behavior-preserving change per PR.

## How to discover architecture and workflows
- Follow top-down: prefer high-level manifests (README, Makefile, package files)
  then open `src/` and key entrypoints (e.g., `main.go`, `src/index.js`,
  `cmd/` binaries). In the absence of manifests, look for tests (`tests/`,
  `*_test.go`, `test_*.py`) to observe runtime wiring and important behaviors.
- Note boundaries: services, CLIs, libraries. If you find a `cmd/` folder,
  treat each subfolder as an independent executable and inspect its imports.

## Project-specific conventions (discoverable patterns)
- If present, prefer the repository's Makefile or `scripts/` tasks to run
  builds and tests — they express project-specific flags and environment.
- Keep file and module names aligned with existing conventions (no new top-level
  folders unless requested). If you add a new toolchain (e.g., add a
  `package.json`), document commands in a new `README.md` at the repo root.

## Debugging and test workflows
- If you find a language manifest, run the conventional commands:
  - Node: `npm test` / `npm run build`
  - Python: `python -m pytest` or `tox` if present
  - Go: `go test ./...` and `go build ./...`
  - Rust: `cargo test`
  Run these only after confirming the manifest and dependencies exist.

## Integration points & dependencies
- Look for environment/config files (`.env`, `config/`, `docker-compose.yml`)
  for integrations (databases, queues). If these are missing, ask for a
  description or test doubles to avoid touching production services.

## Examples / useful checks (what to run and why)
- "Is this a Node project?" — check for `package.json` at repo root.
- "Is there a CLI?" — look for `cmd/` or files named `main.go` / `__main__.py`.
- "Where are tests?" — search for `test` glob and inspect the test runner.

## Safety and PR guidance
- Do not guess runtime secrets or credentials. If a change requires secrets,
  ask the maintainer for ephemeral test credentials or a reproducible local
  dev setup.
- For any generated code or large scaffolding, create a tiny runnable example
  (one-file) and a short `README.md` showing how to run it locally.

## When to ask the maintainer
- Repo is empty or missing manifests.
- You need access to private package feeds, environment variables, or infra
  setup to run tests.
- Ambiguous architecture decisions (monorepo vs multiple repos).

## Final note
If you implement changes, include a short verification step in the PR body
that tells a human reviewer how you validated the change (commands run and
expected results). If you'd like, paste a draft PR description and I will
help refine it.
