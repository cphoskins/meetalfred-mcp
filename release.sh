#!/usr/bin/env bash
# release.sh — update version in all three files atomically
# Usage: ./release.sh 0.2.0

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 0.2.0"
    exit 1
fi

NEW_VERSION="$1"

echo "Updating version to ${NEW_VERSION} ..."

# 1. pyproject.toml
sed -i "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" pyproject.toml

# 2. __init__.py
sed -i "s/^__version__ = \".*\"/__version__ = \"${NEW_VERSION}\"/" meetalfred_mcp/__init__.py

# 3. server.json (both occurrences)
sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"${NEW_VERSION}\"/g" server.json

echo "Done. Updated to ${NEW_VERSION} in:"
echo "  - pyproject.toml"
echo "  - meetalfred_mcp/__init__.py"
echo "  - server.json"
echo ""
echo "Next steps:"
echo "  git add -A && git commit -m 'Release v${NEW_VERSION}'"
echo "  git tag v${NEW_VERSION}"
echo "  git push origin main --tags"
