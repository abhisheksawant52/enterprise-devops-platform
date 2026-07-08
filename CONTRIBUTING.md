# Contributing

Thanks for taking the time to contribute to the Enterprise DevOps Platform.

## Ground rules

- Every change goes through a pull request; direct pushes to `main` are disabled.
- All required status checks (lint, type-check, tests, security scans) must pass.
- Keep changes scoped and internally consistent — a change to a port/name/image must be reflected across
  Terraform, Helm, Kustomize, and the service.

## Development environment

```bash
make install          # create .venv and install runtime + dev dependencies
make lint             # ruff + black --check
make typecheck        # mypy
make test             # pytest with coverage
make fmt              # auto-format with black + ruff --fix
make tf-fmt           # terraform fmt -recursive
```

Install the git hooks so the same checks run locally before you push:

```bash
pip install pre-commit
pre-commit install
```

## Commit style

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(control-plane): add deployment rollback endpoint
fix(terraform): pin eks node group ami type
docs(runbooks): add incident response runbook
```

## Branching and releases

- Branch from `main` using `feat/…`, `fix/…`, `docs/…`, or `chore/…`.
- Merges to `main` are squashed.
- Releases are cut by pushing a `v*` tag; the release workflow builds and pushes the image and packages
  the Helm chart.

## Terraform changes

- Run `terraform fmt` and `terraform validate` before opening a PR.
- Never commit `*.tfstate`, `.terraform/`, or real `*.tfvars` containing account-specific values.
- New resources must be scanned cleanly by Checkov or carry a justified, inline suppression.

## Reviewing

At least one approval from a [CODEOWNERS](CODEOWNERS) reviewer is required. Reviewers check for
correctness, security, and consistency across the stack.
