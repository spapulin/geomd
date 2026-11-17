# Contributing

Thanks for your interest in this project! We welcome all contributions and kindly ask that you follow the guidelines below before opening a pull request (PR).

## Before you start

- Open an issue first for new features or non-trivial changes so we can agree on scope (small bug fixes and doc updates are welcome directly as PRs).
- Keep changes focused. A PR should solve one problem.
- Run the test suite locally before submitting.
- Do not include unrelated refactors, formatting churn, or dependency bumps in a bug-fix PR.
- Do not bump the package version in `.toml` files; maintainers handle version updates during releases.

## PR scope

A good PR is:

- **Small**: aim for ≤500 changed lines and ≤10 source files. Larger changes should be split.
- **Thematic**: one logical change per PR (e.g., “fix parser data loss”, “add CLI `check` command”, “update packaging”).
- **Independently reviewable**: each PR should leave tests passing and be understandable on its own.
- **Free of unrelated changes**: do not mix refactoring with behavior changes.

If your work spans multiple concerns, submit **separate PRs by topic**. Stacked PRs are acceptable if later changes depend on earlier ones; keep stacks shallow (≤4–5 PRs).

## Commit hygiene

- Use clear, imperative commit messages (e.g., `fix: preserve inline formatting markers`).
- Group related changes into atomic commits.
- Squash fixup/WIP commits before requesting review.
- Avoid merge commits from `main`; rebase instead (use `git push --force-with-lease` when updating a rebased PR branch).

## AI-assisted contributions

AI tools are welcome as aids, but **a human must take full responsibility** for the submitted code.

- You must be able to explain and defend every change during review.
- Do not submit autonomous bot output without human review and ownership.
- Disclose significant AI assistance in the PR description if it materially shaped the code.

## Security-sensitive changes

Flag any PR that touches:

- CI/CD workflows (`.github/workflows/`, etc.)
- dependencies, lockfiles, install scripts
- authentication, authorization, crypto, secrets
- network calls, file system access, shell execution, deserialization
- parsing or validation of untrusted input

Such PRs may receive a security-review label and take longer to review due to additional scrutiny.

## Review process and labels

We use labels to communicate status:

- `needs-triage` - received, not yet assessed.
- `in-review` - under active review.
- `security-review` - requires security-focused review.
- `needs-changes` - author action required.
- `wontfix` / `invalid` - not accepted.

We aim to acknowledge new PRs within a few days, but review time varies. Acknowledgment is not acceptance.

## Resubmission policy

If a PR is too broad, has a messy history, or mixes unrelated concerns, we may close it and ask for a resubmission. A resubmission should:

- be split into focused, thematic PRs,
- have a clean commit history,
- leave tests passing,
- justify any new dependency or CI change.

PRs that ignore these requirements may be closed without detailed review.

## Attribution

- If you reuse code from another source, preserve its license and attribution.
- If a fix is based on someone else’s report or PR, credit them in the commit message or PR description (e.g., `Reported-by:`, `Based on PR #N by @user`).
- Do not remove existing copyright notices.

## Reporting bugs

Open an issue with:

- a minimal reproduction,
- expected vs. actual behavior,
- version/commit,
- environment details.

## Code of conduct

Be respectful and constructive. Review comments should focus on the code, not the person.