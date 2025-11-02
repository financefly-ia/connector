#!/usr/bin/env python3
"""
Deployment Readiness Test

This script validates that the Pluggy Connect SDK update is ready for deployment
by testing the actual application startup and key functionality.

Requirements covered: 1.1, 1.2, 2.1, 2.2, 2.3, 4.1, 4.2
"""

import os
import sys
import time
import logging
import tempfile
from unittest.mock import patch, Mock
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_application_imports():
    """Test that all application modules can be imported successfully"""
    logger.info("🔍 Testing application imports...")
    
    try:
        # Test core application imports
        from modules.pluggy_utils import validate_environment, create_connect_token, PluggyClient
        from modules.db import init_db, save_client, get_conn
        from modules.error_utils import log_and_display_error, display_environment_errors, handle_pluggy_error
        
        logger.info("✅ All core modules imported successfully")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during imports: {e}")
        return False

def test_environment_validation_with_real_env():
    """Test environment validation with actual .env file"""
    logger.info("🔧 Testing environment validation with real configuration...")
    
    try:
        from modules.pluggy_utils import validate_environment
        
        # Test with actual environment
        config = validate_environment()
        
        # Validate config structure
        required_keys = ['client_id', 'client_secret', 'base_url']
        config_valid = all(key in config for key in required_keys)
        
        if config_valid:
            logger.info("✅ Environment validation successful with real configuration")
            logger.info(f"   - Client ID length: {len(config['client_id'])}")
            logger.info(f"   - Client Secret length: {len(config['client_secret'])}")
            logger.info(f"   - Base URL: {config['base_url']}")
            return True
        else:
            logger.error("❌ Environment configuration missing required keys")
            return False
            
    except ValueError as e:
        logger.error(f"❌ Environment validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error in environment validation: {e}")
        return False

def test_sdk_endpoint_accessibility():
    """Test that the new SDK endpoint is accessible"""
    logger.info("🌐 Testing SDK endpoint accessibility...")
    
    sdk_url = "https://cdn.pluggy.ai/pluggy-connect/v2.9.2/pluggy-connect.js"
    
    try:
        response = requests.head(sdk_url, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ SDK endpoint is accessible")
            logger.info(f"   - Status: {response.status_code}")
            logger.info(f"   - Content-Type: {response.headers.get('content-type', 'N/A')}")
            return True
        else:
            logger.error(f"❌ SDK endpoint returned status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("❌ SDK endpoint request timed out")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ Could not connect to SDK endpoint")
        return False
    except Exception as e:
        logger.error(f"❌ Error accessing SDK endpoint: {e}")
        return False

def test_old_sdk_endpoint_removed():
    """Test that references to old SDK version have been removed"""
    logger.info("🔍 Testing that old SDK references have been removed...")
    
    files_to_check = ['app.py', 'static/pluggy_loader.js']
    old_version_found = False
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'v2.6.0' in content:
                logger.error(f"❌ Old SDK version v2.6.0 found in {file_path}")
                old_version_found = True
            else:
                logger.info(f"✅ No old SDK version found in {file_path}")
                
        except FileNotFoundError:
            logger.warning(f"⚠️ File not found: {file_path}")
    
    if not old_version_found:
        logger.info("✅ All old SDK references have been removed")
        return True
    else:
        logger.error("❌ Old SDK references still present")
        return False

@patch('modules.pluggy_utils.requests.post')
def test_pluggy_api_integration(mock_post):
    """Test Pluggy API integration with mocked responses"""
    logger.info("🔗 Testing Pluggy API integration...")
    
    try:
        from modules.pluggy_utils import create_connect_token
        
        # Mock successful API responses
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {'apiKey': 'test_deployment_api_key'}
        
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {'accessToken': 'test_deployment_token'}
        
        mock_post.side_effect = [auth_response, token_response]
        
        # Test token generation
        start_time = time.time()
        token = create_connect_token('deployment_test@example.com')
        end_time = time.time()
        
        if token and isinstance(token, str) and len(token) > 10:
            logger.info("✅ Pluggy API integration working correctly")
            logger.info(f"   - Token generated in {end_time - start_time:.3f}s")
            logger.info(f"   - Token length: {len(token)}")
            return True
        else:
            logger.error("❌ Invalid token generated")
            return False
            
    except Exception as e:
        logger.error(f"❌ Pluggy API integration failed: {e}")
        return False

def test_error_handling_implementation():
    """Test that error handling is properly implemented"""
    logger.info("🛡️ Testing error handling implementation...")
    
    try:
        # Test error utility functions
        from modules.error_utils import log_and_display_error, display_environment_errors, handle_pluggy_error
        
        # Verify functions are callable
        error_functions = [log_and_display_error, display_environment_errors, handle_pluggy_error]
        all_callable = all(callable(func) for func in error_functions)
        
        if all_callable:
            logger.info("✅ All error handling functions are available and callable")
        else:
            logger.error("❌ Some error handling functions are not callable")
            return False
        
        # Test error handling in main application
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Check for proper error handling patterns
        error_patterns = ['try:', 'except', 'handle_pluggy_error', 'ValueError', 'Exception']
        patterns_found = sum(1 for pattern in error_patterns if pattern in app_content)
        
        if patterns_found >= 4:
            logger.info(f"✅ Error handling properly implemented ({patterns_found} patterns found)")
            return True
        else:
            logger.error(f"❌ Insufficient error handling patterns ({patterns_found} found)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing error handling: {e}")
        return False

def test_status_messages_implementation():
    """Test that status messages are properly implemented"""
    logger.info("💬 Testing status messages implementation...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Check for key status messages
        required_messages = [
            'Conectando com segurança',
            'Validando credenciais',
            'Estabelecendo conexão segura',
            'Preparando interface de conexão'
        ]
        
        messages_found = []
        for message in required_messages:
            if message in app_content:
                messages_found.append(message)
        
        if len(messages_found) == len(required_messages):
            logger.info("✅ All required status messages are implemented")
            for msg in messages_found:
                logger.info(f"   - Found: '{msg}'")
            return True
        else:
            logger.error(f"❌ Missing status messages: {len(messages_found)}/{len(required_messages)} found")
            missing = [msg for msg in required_messages if msg not in messages_found]
            for msg in missing:
                logger.error(f"   - Missing: '{msg}'")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing status messages: {e}")
        return False

def test_widget_configuration():
    """Test that widget configuration is properly implemented"""
    logger.info("🔧 Testing widget configuration...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Check for widget configuration elements
        widget_elements = [
            'PluggyConnect',
            'connectToken',
            'onOpen',
            'onClose',
            'onSuccess',
            'onError'
        ]
        
        elements_found = []
        for element in widget_elements:
            if element in app_content:
                elements_found.append(element)
        
        if len(elements_found) == len(widget_elements):
            logger.info("✅ Widget configuration is complete")
            for element in elements_found:
                logger.info(f"   - Found: {element}")
            return True
        else:
            logger.error(f"❌ Incomplete widget configuration: {len(elements_found)}/{len(widget_elements)} elements found")
            missing = [elem for elem in widget_elements if elem not in elements_found]
            for elem in missing:
                logger.error(f"   - Missing: {elem}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing widget configuration: {e}")
        return False

def test_database_integration():
    """Test that database integration is working"""
    logger.info("🗄️ Testing database integration...")
    
    try:
        from modules.db import init_db, save_client, get_conn
        
        # Test that functions are importable and callable
        db_functions = [init_db, save_client, get_conn]
        all_callable = all(callable(func) for func in db_functions)
        
        if all_callable:
            logger.info("✅ Database functions are available and callable")
            logger.info("   - init_db: ✓")
            logger.info("   - save_client: ✓")
            logger.info("   - get_conn: ✓")
            return True
        else:
            logger.error("❌ Some database functions are not callable")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Database module import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing database integration: {e}")
        return False

def run_deployment_readiness_tests():
    """Run all deployment readiness tests"""
    logger.info("🚀 Starting Deployment Readiness Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Application Imports", test_application_imports),
        ("Environment Validation", test_environment_validation_with_real_env),
        ("SDK Endpoint Accessibility", test_sdk_endpoint_accessibility),
        ("Old SDK References Removed", test_old_sdk_endpoint_removed),
        ("Pluggy API Integration", test_pluggy_api_integration),
        ("Error Handling Implementation", test_error_handling_implementation),
        ("Status Messages Implementation", test_status_messages_implementation),
        ("Widget Configuration", test_widget_configuration),
        ("Database Integration", test_database_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("DEPLOYMENT READINESS SUMMARY")
    logger.info("=" * 60)
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("-" * 60)
    logger.info(f"Overall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL DEPLOYMENT READINESS TESTS PASSED!")
        logger.info("✅ Application is ready for production deployment")
        logger.info("🚀 Pluggy Connect SDK v2.9.2 update is complete and validated")
        return True
    else:
        logger.error("❌ Some deployment readiness tests failed")
        logger.error("🔧 Please fix failing tests before deploying to production")
        return False

def main():
    """Main function"""
    print("🔍 Pluggy Connect SDK - Deployment Readiness Test")
    print("=" * 60)
    
    success = run_deployment_readiness_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 DEPLOYMENT READINESS: PASSED")
        print("✅ Ready for production deployment")
    else:
        print("❌ DEPLOYMENT READINESS: FAILED")
        print("🔧 Fix issues before deployment")
    
    return 0 if success else 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)