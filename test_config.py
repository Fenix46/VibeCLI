#!/usr/bin/env python3
"""
Test script to verify VibeCLI configuration
"""

def test_config():
    """Test configuration loading"""
    try:
        from config import get_settings
        settings = get_settings()
        
        print("✅ Configuration loaded successfully!")
        print(f"🔧 Model: {settings.gemini_model}")
        print(f"🔧 API Key configured: {'Yes' if settings.gemini_api_key else 'No'}")
        print(f"🔧 Skip patterns: {len(settings.skip_patterns)} patterns")
        print(f"🔧 Cache enabled: {settings.cache_enabled}")
        print(f"🔧 Max file size: {settings.max_file_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure .env file exists")
        print("2. Check SKIP_PATTERNS format (comma-separated, no spaces)")
        print("3. Run: python create_config.py")
        return False

if __name__ == "__main__":
    print("🧪 Testing VibeCLI configuration...")
    success = test_config()
    
    if success:
        print("\n🎉 Configuration test passed!")
    else:
        print("\n❌ Configuration test failed!")
        
    input("\nPress Enter to continue...") 