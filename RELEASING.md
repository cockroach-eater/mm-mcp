# Release Process

This document describes how to create a new release of mm-mcp using GitHub flow.

## Prerequisites

- Push access to the repository
- Ability to create tags and releases on GitHub

## Release Steps

### 1. Prepare the Release

Make sure all changes are committed and pushed to `main`:

```bash
git checkout main
git pull origin main
```

### 2. Update Version

Update the version in `pyproject.toml`:

```toml
[project]
version = "0.2.0"  # Update this
```

Update version in `src/mm_mcp/__init__.py`:

```python
__version__ = "0.2.0"
```

Commit the version bump:

```bash
git add pyproject.toml src/mm_mcp/__init__.py
git commit -m "Bump version to 0.2.0"
git push origin main
```

### 3. Create and Push Tag

Create an annotated tag:

```bash
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

### 4. GitHub Actions

The GitHub Actions workflow will automatically:
- Build the package (wheel and source distribution)
- Create a GitHub Release
- Attach the built artifacts to the release
- Generate release notes from commits

### 5. Verify Release

1. Go to https://github.com/cockroach-eater/mm-mcp/releases
2. Check that the release was created
3. Verify that `.whl` and `.tar.gz` files are attached
4. Review the auto-generated release notes

### 6. Test Installation

Test that users can install from the release:

```bash
# From release URL
uvx --from https://github.com/cockroach-eater/mm-mcp/releases/download/v0.2.0/mm_mcp-0.2.0-py3-none-any.whl mm-mcp --help

# From latest release
uvx --from git+https://github.com/cockroach-eater/mm-mcp.git@v0.2.0 mm-mcp --help

# From main branch
uvx --from git+https://github.com/cockroach-eater/mm-mcp.git mm-mcp --help
```

## Hotfix Releases

For urgent fixes:

1. Create a hotfix branch from main:
   ```bash
   git checkout -b hotfix/fix-critical-bug main
   ```

2. Make your fixes and commit

3. Merge back to main via PR

4. Follow the normal release process above

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.2.0): New features, backward compatible
- **PATCH** (0.1.1): Bug fixes, backward compatible

## Troubleshooting

### Build Failed

Check the GitHub Actions logs:
- Go to Actions tab
- Find the failed workflow
- Check the build logs for errors

### Release Not Created

Ensure:
- Tag format is `v*` (e.g., `v0.1.0`)
- GitHub Actions has write permissions
- The workflow file is in `.github/workflows/release.yml`

### Installation Issues

Verify:
- The wheel file is properly attached to the release
- The file name matches the pattern in documentation
- URL is accessible (not a draft release)
