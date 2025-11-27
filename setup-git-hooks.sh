#!/bin/bash
# Setup git pre-commit hook to automatically run checks

HOOK_FILE=".git/hooks/pre-commit"

echo "Setting up git pre-commit hook..."

# Create the pre-commit hook
cat > "$HOOK_FILE" << 'EOF'
#!/bin/bash
# Pre-commit hook to run format, lint, and test

echo "🔍 Running pre-commit checks..."
echo "========================================="

# Run format
echo "\n📝 Formatting code with black..."
make format
if [ $? -ne 0 ]; then
    echo "❌ Formatting failed!"
    exit 1
fi

# Run lint with auto-fix
echo "\n🔍 Linting code with ruff..."
make lint-fix
if [ $? -ne 0 ]; then
    echo "❌ Linting failed!"
    exit 1
fi

# Stage any files that were auto-fixed
git add -u

# Run lint check (without fix) to ensure everything passes
echo "\n🔍 Final lint check..."
make lint
if [ $? -ne 0 ]; then
    echo "❌ Linting failed! Please fix the issues above."
    exit 1
fi

# Run tests
echo "\n🧪 Running tests..."
make test
if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Please fix the failing tests."
    exit 1
fi

echo "\n✅ Pre-commit checks passed!"
echo "========================================="
EOF

# Make the hook executable
chmod +x "$HOOK_FILE"

echo "✅ Git pre-commit hook installed successfully!"
echo ""
echo "The hook will automatically run format + lint before each commit."
echo "To skip the hook temporarily, use: git commit --no-verify"
echo ""
echo "To uninstall, run: rm .git/hooks/pre-commit"
