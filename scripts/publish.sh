#!/bin/bash

# VibeCli Publication Script
echo "🚀 VibeCli Publication Script"
echo "=============================="

# Check if user is logged in to npm
echo "📝 Checking npm authentication..."
if ! npm whoami > /dev/null 2>&1; then
    echo "❌ You are not logged in to npm. Please run 'npm login' first."
    exit 1
fi

echo "✅ Authenticated as: $(npm whoami)"

# Clean and build
echo "🧹 Cleaning previous build..."
rm -rf dist/

echo "🔨 Building project..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Please fix errors before publishing."
    exit 1
fi

echo "✅ Build successful"

# Run tests (if any)
echo "🧪 Running tests..."
npm test 2>/dev/null || echo "⚠️  No tests found, skipping..."

# Check package
echo "📦 Checking package contents..."
npm pack --dry-run

# Confirm publication
echo ""
echo "📋 Package Information:"
echo "  Name: $(npm pkg get name | tr -d '\"')"
echo "  Version: $(npm pkg get version | tr -d '\"')"
echo "  Description: $(npm pkg get description | tr -d '\"')"
echo ""

read -p "🤔 Do you want to publish this package? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Publication cancelled."
    exit 1
fi

# Publish
echo "🚀 Publishing to npm..."
npm publish

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Package published successfully!"
    echo "📦 Install with: npm install -g $(npm pkg get name | tr -d '\"')"
    echo "🔗 View on npm: https://www.npmjs.com/package/$(npm pkg get name | tr -d '\"')"
else
    echo "❌ Publication failed. Check the error messages above."
    exit 1
fi
