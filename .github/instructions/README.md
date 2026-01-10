# Path-Specific Copilot Instructions

This directory contains path-specific instructions for GitHub Copilot coding agent, scoped to different parts of the repository.

## Files

### `python.instructions.md`
**Applies to**: `python/**`

Python 3.11+ rewrite instructions. Emphasizes:
- Immutable dataclasses (`frozen=True`)
- Property-based testing with Hypothesis
- Pure functional game logic
- FastAPI patterns
- Type safety

### `legacy.instructions.md`
**Applies to**: `app/**`, `conf/**`, `build.sbt`, `project/**`, `public/**`, `client/**`

Legacy Scala/Play Framework code. Emphasizes:
- **DO NOT MODIFY** unless explicitly instructed
- Read-only reference for understanding original behavior
- All new development happens in Python

## How It Works

GitHub Copilot coding agent reads these files and applies them based on the `applies_to` glob patterns in the YAML frontmatter. When working on files that match a pattern, Copilot will follow those specific instructions in addition to the repository-wide instructions in `.github/copilot-instructions.md`.

## Priority

Instructions are merged with this priority:
1. **Personal** (user-level settings)
2. **Repository** (this repository's `.github/copilot-instructions.md`)
3. **Organization** (organization-level settings)
4. **Path-specific** (files in this directory)

All are combined, but path-specific instructions provide additional context for specific parts of the codebase.

## Best Practices

### DO:
- ✅ Keep instructions focused and actionable
- ✅ Use specific glob patterns in `applies_to`
- ✅ Include concrete code examples
- ✅ Document what NOT to do (anti-patterns)
- ✅ Update instructions as the project evolves

### DON'T:
- ❌ Duplicate information from main `copilot-instructions.md`
- ❌ Create conflicting rules between instruction files
- ❌ Make instructions too verbose (keep them scannable)
- ❌ Include sensitive information or secrets

## Maintenance

When adding new path-specific instructions:

1. Create a new `.instructions.md` file in this directory
2. Add YAML frontmatter with `applies_to` glob patterns
3. Keep instructions concise and specific to that path
4. Update this README with a description of the new file

## References

- [GitHub Copilot Custom Instructions](https://docs.github.com/en/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)
- [Repository Setup Best Practices](https://github.blog/ai-and-ml/github-copilot/onboarding-your-ai-peer-programmer-setting-up-github-copilot-coding-agent-for-success/)
