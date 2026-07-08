# Security Policy

## Supported versions

| Version | Supported          |
|---------|--------------------|
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a vulnerability

Please **do not** open public GitHub issues for security vulnerabilities.

Instead, report privately using GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
feature on this repository, or email the maintainer.

Include, where possible:

- A description of the issue and its impact.
- Steps to reproduce or a proof of concept.
- Affected component (Terraform, control-plane service, Helm chart, CI, etc.).
- Any known mitigations.

We aim to acknowledge reports within **3 business days** and to provide a remediation timeline within
**10 business days**.

## Security controls in this repository

- **Secret detection** — Gitleaks runs on every push and pull request.
- **Dependency & filesystem scanning** — Trivy scans the repository and built images.
- **IaC scanning** — Checkov scans Terraform for misconfigurations.
- **Least privilege** — workloads use IRSA; no static cloud credentials are stored in the cluster.
- **Pinned dependencies** — Python requirements and GitHub Actions are version-pinned.

## Disclosure

We follow coordinated disclosure. Once a fix is available and deployed, we will publish a security
advisory crediting the reporter (unless anonymity is requested).
