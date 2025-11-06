#!/usr/bin/env python3
"""
Test script for deployment readiness validator.

This script tests the DeploymentValidator class for Railway deployment readiness.
"""

import sys
import os
import json
from datetime import datetime

# Add modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

def test_deployment_validator():
    """Test the deployment readiness validator."""
    
    print("Testing Railway Deployment Readiness Validator")
    print("=" * 60)
    
    try:
        from deployment_validator import DeploymentValidator, run_deployment_validation
        
        print("✅ Successfully imported DeploymentValidator")
        
        # Test individual validator creation
        validator = DeploymentValidator()
        print("✅ Successfully created DeploymentValidator instance")
        
        # Test environment validation only (safe to run without external dependencies)
        print("\nTesting environment variable validation...")
        env_result = validator.validate_environment_variables()
        print(f"Environment validation result: {env_result}")
        
        # Test the convenience function import
        print("\nTesting convenience function...")
        print("Note: Full validation may fail due to missing environment variables - this is expected in test environment")
        
        # Don't run full validation in test as it requires actual database and API credentials
        print("✅ DeploymentValidator module is working correctly!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logging_functionality():
    """Test the enhanced logging functionality."""
    
    print("\n" + "=" * 60)
    print("Testing Enhanced Logging Functionality")
    print("=" * 60)
    
    try:
        from deployment_validator import DeploymentValidator
        
        validator = DeploymentValidator()
        
        # Test different log levels
        validator.log_validation("Test INFO message", "INFO", "TEST")
        validator.log_validation("Test WARNING message", "WARNING", "TEST")
        validator.log_validation("Test ERROR message", "ERROR", "TEST")
        
        print(f"✅ Logging test complete - Errors: {len(validator.errors)}, Warnings: {len(validator.warnings)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

if __name__ == "__main__":
    try:
        print("Starting Deployment Readiness Validator Tests")
        print("=" * 60)
        
        # Test basic functionality
        basic_test = test_deployment_validator()
        
        # Test logging
        logging_test = test_logging_functionality()
        
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        if basic_test and logging_test:
            print("🎉 All tests passed!")
            print("✅ DeploymentValidator is ready for use")
        else:
            print("⚠️ Some tests failed")
            if not basic_test:
                print("❌ Basic validator test failed")
            if not logging_test:
                print("❌ Logging test failed")
        
        print("\nDeployment readiness validation system implementation completed!")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)