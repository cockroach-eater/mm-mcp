#!/bin/bash
set -e

# Release minor version (e.g., 1.1.5 -> 1.2.0)

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

echo "Current version: $CURRENT_VERSION"

# Parse version
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Increment minor, reset patch to 0
NEW_MINOR=$((MINOR + 1))
NEW_VERSION="${MAJOR}.${NEW_MINOR}.0"

echo "New version: $NEW_VERSION"

# Ask for confirmation
read -p "Release v$NEW_VERSION? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted"
    exit 1
fi

# Update version in pyproject.toml
sed -i '' "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Update version in __init__.py
sed -i '' "s/__version__ = \"$CURRENT_VERSION\"/__version__ = \"$NEW_VERSION\"/" src/mm_mcp/__init__.py

# Commit changes
git add pyproject.toml src/mm_mcp/__init__.py
git commit -m "Bump version to $NEW_VERSION"

# Create tag
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION - Minor release"

# Push
git push origin main
git push origin "v$NEW_VERSION"

echo "✅ Released v$NEW_VERSION"
echo "GitHub Actions will build the release at:"
echo "https://github.com/cockroach-eater/mm-mcp/releases/tag/v$NEW_VERSION"
