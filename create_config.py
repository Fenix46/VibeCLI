#!/usr/bin/env python3
"""
Utility script to create default VibeCLI configuration
"""

from config.settings import create_default_config_file

if __name__ == "__main__":
    create_default_config_file()
    print("\n🎉 Configuration setup completed!")
    print("💡 You can now customize .env file with your settings")
    print("🔑 Don't forget to set your GEMINI_API_KEY!") 