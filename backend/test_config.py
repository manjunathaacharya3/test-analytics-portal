#!/usr/bin/env python3
"""Test script to verify CORS_ORIGINS parsing."""

import os
import sys

# Add app directory to path
sys.path.insert(0, '/app')

# Set test environment variable
os.environ['CORS_ORIGINS'] = 'http://localhost:3000,http://frontend:3000'

try:
    from app.core.config import settings
    
    print("✅ Config loaded successfully!")
    print(f"\nCORS_ORIGINS type: {type(settings.CORS_ORIGINS)}")
    print(f"CORS_ORIGINS value: {settings.CORS_ORIGINS}")
    
    # Verify it's a list
    assert isinstance(settings.CORS_ORIGINS, list), "CORS_ORIGINS should be a list"
    assert len(settings.CORS_ORIGINS) == 2, "Should have 2 origins"
    assert 'http://localhost:3000' in settings.CORS_ORIGINS, "Should contain localhost:3000"
    assert 'http://frontend:3000' in settings.CORS_ORIGINS, "Should contain frontend:3000"
    
    print("\n✅ All assertions passed!")
    print("\n🎉 CORS_ORIGINS is correctly parsed as a list!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
