#!/bin/bash

# Test Installation Script for VibeCli
echo "🧪 VibeCli Installation Test"
echo "============================"

# Test local installation
echo "📦 Testing local build..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful"

# Test binary execution
echo "🔧 Testing binary execution..."
./bin/vibe --version

if [ $? -ne 0 ]; then
    echo "❌ Binary execution failed"
    exit 1
fi

echo "✅ Binary works correctly"

# Test help command
echo "📖 Testing help command..."
./bin/vibe --help

echo ""
echo "🎉 All tests passed! VibeCli is ready for publication."
echo ""
echo "Next steps:"
echo "1. npm login"
echo "2. ./scripts/publish.sh"
echo "3. Test global installation: npm install -g @vibecli/core"
