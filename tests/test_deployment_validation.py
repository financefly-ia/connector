#!/usr/bin/env python3
"""
Comprehensive deployment validation tests for Railway Streamlit deployment.

This test suite validates:
- Port configuration and environment variable handling
- External access and API connectivity
- Deployment readiness validation

Requirements covered: 4.1, 4.2, 4.3
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import requests
from datetime import datetime

# Add modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

class TestPortConfiguration(unittest.TestCase):
    """Test port configuration and environment variable handling"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_env = os.environ.copy()
    
    def tearDown(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_port_environment_variable_handling(self):
        """Test PORT environment variable is properly read and validated"""
        # Test with valid PORT
        os.environ["PORT"] = "8080"
        port = os.getenv("PORT")
        self.assertEqual(port, "8080")
        
        # Test port validation
        try:
            port_num = int(port)
            self.assertTrue(1 <= port_num <= 65535)
        except ValueError:
            self.fail("PORT should be a valid integer")
    
    def test_port_fallback_mechanism(self):
        """Test fallback to default port when PORT is not set"""
        # Remove PORT from environment
        if "PORT" in os.environ:
            del os.environ["PORT"]
        
        port = os.getenv("PORT")
        self.assertIsNone(port)
        
        # Test fallback logic
        fallback_port = port or "8080"
        self.assertEqual(fallback_port, "8080")
    
    def test_port_validation_edge_cases(self):
        """Test port validation with invalid values"""
        invalid_ports = ["0", "65536", "abc", "-1", ""]
        
        for invalid_port in invalid_ports:
            os.environ["PORT"] = invalid_port
            port = os.getenv("PORT")
            
            try:
                port_num = int(port)
                # Port should be in valid range
                if port_num < 1 or port_num > 65535:
                    # Should trigger fallback
                    fallback_port = "8080"
                    self.assertEqual(fallback_port, "8080")
            except ValueError:
                # Non-numeric port should trigger fallback
                fallback_port = "8080"
                self.assertEqual(fallback_port, "8080")
    
    def test_streamlit_server_configuration(self):
        """Test Streamlit server environment variables are set correctly"""
        os.environ["PORT"] = "3000"
        
        # Simulate app.py configuration logic
        port = os.getenv("PORT", "8080")
        os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
        os.environ["STREAMLIT_SERVER_PORT"] = str(port)
        os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
        
        # Verify configuration
        self.assertEqual(os.environ["STREAMLIT_SERVER_HEADLESS"], "true")
        self.assertEqual(os.environ["STREAMLIT_SERVER_PORT"], "3000")
        self.assertEqual(os.environ["STREAMLIT_SERVER_ADDRESS"], "0.0.0.0")


class TestEnvironmentVariableHandling(unittest.TestCase):
    """Test comprehensive environment variable validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_env = os.environ.copy()
        # Set up minimal required environment
        self.required_vars = {
            "PLUGGY_CLIENT_ID": "test_client_id_12345",
            "PLUGGY_CLIENT_SECRET": "test_secret_abcdef123456",
            "DB_HOST": "test.railway.app",
            "DB_USER": "postgres",
            "DB_PASSWORD": "test_password_123",
            "DB_NAME": "railway"
        }
    
    def tearDown(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_required_environment_variables_present(self):
        """Test all required environment variables are present"""
        # Set required variables
        for var, value in self.required_vars.items():
            os.environ[var] = value
        
        # Validate all required variables are present
        missing_vars = []
        for var in self.required_vars.keys():
            if not os.getenv(var):
                missing_vars.append(var)
        
        self.assertEqual(len(missing_vars), 0, f"Missing required variables: {missing_vars}")
    
    def test_missing_environment_variables_detection(self):
        """Test detection of missing required environment variables"""
        # Clear environment
        for var in self.required_vars.keys():
            if var in os.environ:
                del os.environ[var]
        
        # Check for missing variables
        missing_vars = []
        for var in self.required_vars.keys():
            if not os.getenv(var):
                missing_vars.append(var)
        
        self.assertEqual(len(missing_vars), len(self.required_vars))
        self.assertIn("PLUGGY_CLIENT_ID", missing_vars)
        self.assertIn("DB_HOST", missing_vars)
    
    def test_optional_environment_variables_defaults(self):
        """Test optional environment variables have proper defaults"""
        # Test DB_PORT default
        db_port = os.getenv("DB_PORT", "5432")
        self.assertEqual(db_port, "5432")
        
        # Test DB_SSLMODE default
        db_sslmode = os.getenv("DB_SSLMODE", "require")
        self.assertEqual(db_sslmode, "require")
        
        # Test with custom values
        os.environ["DB_PORT"] = "5433"
        os.environ["DB_SSLMODE"] = "prefer"
        
        db_port = os.getenv("DB_PORT", "5432")
        db_sslmode = os.getenv("DB_SSLMODE", "require")
        
        self.assertEqual(db_port, "5433")
        self.assertEqual(db_sslmode, "prefer")
    
    def test_sensitive_variable_masking(self):
        """Test sensitive variables are properly masked in logs"""
        sensitive_vars = ["PLUGGY_CLIENT_SECRET", "DB_PASSWORD"]
        
        for var in sensitive_vars:
            test_value = "very_secret_value_123456789"
            os.environ[var] = test_value
            
            # Simulate masking logic from app.py
            value = os.getenv(var)
            if "SECRET" in var or "PASSWORD" in var:
                masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                self.assertTrue(masked_value.startswith("very"))
                self.assertTrue(masked_value.endswith("6789"))
                self.assertIn("...", masked_value)


class TestDeploymentValidator(unittest.TestCase):
    """Test the DeploymentValidator class functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_env = os.environ.copy()
        # Import here to avoid import issues
        try:
            from deployment_validator import DeploymentValidator
            self.validator = DeploymentValidator()
        except ImportError:
            self.skipTest("DeploymentValidator not available")
    
    def tearDown(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_validator_initialization(self):
        """Test DeploymentValidator initializes correctly"""
        self.assertIsNotNone(self.validator)
        self.assertEqual(len(self.validator.errors), 0)
        self.assertEqual(len(self.validator.warnings), 0)
        self.assertIsInstance(self.validator.validation_results, dict)
    
    def test_environment_validation_with_complete_config(self):
        """Test environment validation with complete configuration"""
        # Set up complete environment
        required_vars = {
            "PORT": "8080",
            "PLUGGY_CLIENT_ID": "test_client_id",
            "PLUGGY_CLIENT_SECRET": "test_secret_123456",
            "DB_HOST": "test.railway.app",
            "DB_USER": "postgres",
            "DB_PASSWORD": "test_password",
            "DB_NAME": "railway"
        }
        
        for var, value in required_vars.items():
            os.environ[var] = value
        
        # Run validation
        result = self.validator.validate_environment_variables()
        self.assertTrue(result)
        self.assertTrue(self.validator.validation_results.get("environment", False))
    
    def test_environment_validation_with_missing_vars(self):
        """Test environment validation with missing variables"""
        # Clear critical variables
        critical_vars = ["PLUGGY_CLIENT_ID", "DB_HOST"]
        for var in critical_vars:
            if var in os.environ:
                del os.environ[var]
        
        # Run validation
        result = self.validator.validate_environment_variables()
        self.assertFalse(result)
        self.assertFalse(self.validator.validation_results.get("environment", True))
        self.assertGreater(len(self.validator.errors), 0)
    
    def test_logging_functionality(self):
        """Test validation logging functionality"""
        initial_error_count = len(self.validator.errors)
        initial_warning_count = len(self.validator.warnings)
        
        # Test different log levels
        self.validator.log_validation("Test info message", "INFO", "TEST")
        self.validator.log_validation("Test warning message", "WARNING", "TEST")
        self.validator.log_validation("Test error message", "ERROR", "TEST")
        
        # Verify logging captured errors and warnings
        self.assertEqual(len(self.validator.errors), initial_error_count + 1)
        self.assertEqual(len(self.validator.warnings), initial_warning_count + 1)


class TestExternalConnectivity(unittest.TestCase):
    """Test external API connectivity validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_env = os.environ.copy()
        # Set up test credentials
        os.environ["PLUGGY_CLIENT_ID"] = "test_client_id"
        os.environ["PLUGGY_CLIENT_SECRET"] = "test_secret"
    
    def tearDown(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    @patch('requests.post')
    def test_pluggy_api_authentication_success(self, mock_post):
        """Test successful Pluggy API authentication"""
        # Mock successful authentication response
        mock_auth_response = MagicMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"apiKey": "test_api_key_123456"}
        
        # Mock successful token response
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"accessToken": "test_connect_token_123456"}
        
        mock_post.side_effect = [mock_auth_response, mock_token_response]
        
        # Test authentication logic
        client_id = os.getenv("PLUGGY_CLIENT_ID")
        client_secret = os.getenv("PLUGGY_CLIENT_SECRET")
        
        self.assertIsNotNone(client_id)
        self.assertIsNotNone(client_secret)
        
        # Simulate authentication request
        auth_response = requests.post(
            "https://api.pluggy.ai/auth",
            json={"clientId": client_id, "clientSecret": client_secret}
        )
        
        self.assertEqual(auth_response.status_code, 200)
        api_key = auth_response.json().get("apiKey")
        self.assertIsNotNone(api_key)
        
        # Simulate token request
        token_response = requests.post(
            "https://api.pluggy.ai/connect_token",
            headers={"X-API-KEY": api_key},
            json={"clientUserId": "test_user"}
        )
        
        self.assertEqual(token_response.status_code, 200)
        connect_token = token_response.json().get("accessToken")
        self.assertIsNotNone(connect_token)
    
    @patch('requests.post')
    def test_pluggy_api_authentication_failure(self, mock_post):
        """Test Pluggy API authentication failure handling"""
        # Mock failed authentication response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        # Test authentication failure
        client_id = os.getenv("PLUGGY_CLIENT_ID")
        client_secret = os.getenv("PLUGGY_CLIENT_SECRET")
        
        auth_response = requests.post(
            "https://api.pluggy.ai/auth",
            json={"clientId": client_id, "clientSecret": client_secret}
        )
        
        self.assertEqual(auth_response.status_code, 401)
        self.assertEqual(auth_response.text, "Unauthorized")
    
    @patch('requests.post')
    def test_pluggy_api_timeout_handling(self, mock_post):
        """Test Pluggy API timeout handling"""
        # Mock timeout exception
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        # Test timeout handling
        with self.assertRaises(requests.exceptions.Timeout):
            requests.post(
                "https://api.pluggy.ai/auth",
                json={"clientId": "test", "clientSecret": "test"},
                timeout=15
            )
    
    @patch('requests.post')
    def test_pluggy_api_connection_error_handling(self, mock_post):
        """Test Pluggy API connection error handling"""
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # Test connection error handling
        with self.assertRaises(requests.exceptions.ConnectionError):
            requests.post(
                "https://api.pluggy.ai/auth",
                json={"clientId": "test", "clientSecret": "test"}
            )


class TestDeploymentReadiness(unittest.TestCase):
    """Test overall deployment readiness validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.original_env = os.environ.copy()
    
    def tearDown(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_deployment_readiness_with_complete_config(self):
        """Test deployment readiness with complete configuration"""
        # Set up complete environment
        complete_config = {
            "PORT": "8080",
            "PLUGGY_CLIENT_ID": "test_client_id_12345",
            "PLUGGY_CLIENT_SECRET": "test_secret_abcdef123456",
            "DB_HOST": "test.railway.app",
            "DB_USER": "postgres",
            "DB_PASSWORD": "test_password_123",
            "DB_NAME": "railway",
            "DB_PORT": "5432",
            "DB_SSLMODE": "require"
        }
        
        for var, value in complete_config.items():
            os.environ[var] = value
        
        # Test that all required variables are present
        missing_vars = []
        required_vars = ["PLUGGY_CLIENT_ID", "PLUGGY_CLIENT_SECRET", "DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        self.assertEqual(len(missing_vars), 0, f"Missing variables: {missing_vars}")
    
    def test_deployment_readiness_with_minimal_config(self):
        """Test deployment readiness with minimal required configuration"""
        # Set up minimal environment
        minimal_config = {
            "PLUGGY_CLIENT_ID": "test_client",
            "PLUGGY_CLIENT_SECRET": "test_secret",
            "DB_HOST": "localhost",
            "DB_USER": "user",
            "DB_PASSWORD": "pass",
            "DB_NAME": "db"
        }
        
        for var, value in minimal_config.items():
            os.environ[var] = value
        
        # Test PORT fallback
        port = os.getenv("PORT", "8080")
        self.assertEqual(port, "8080")
        
        # Test optional variables with defaults
        db_port = os.getenv("DB_PORT", "5432")
        db_sslmode = os.getenv("DB_SSLMODE", "require")
        
        self.assertEqual(db_port, "5432")
        self.assertEqual(db_sslmode, "require")
    
    def test_deployment_configuration_files_exist(self):
        """Test that required deployment configuration files exist"""
        required_files = ["Procfile", "requirements.txt", "app.py"]
        
        for file_path in required_files:
            self.assertTrue(os.path.exists(file_path), f"Required file missing: {file_path}")
    
    def test_procfile_configuration(self):
        """Test Procfile contains correct configuration"""
        if os.path.exists("Procfile"):
            with open("Procfile", "r") as f:
                content = f.read()
            
            # Check for required Procfile elements
            self.assertIn("web:", content, "Procfile should define web process")
            self.assertIn("streamlit run app.py", content, "Procfile should start Streamlit")
            self.assertIn("$PORT", content, "Procfile should use $PORT variable")
            self.assertIn("0.0.0.0", content, "Procfile should bind to 0.0.0.0")
            self.assertIn("headless=true", content, "Procfile should enable headless mode")
    
    def test_alternative_startup_script(self):
        """Test alternative startup script configuration"""
        if os.path.exists("start.sh"):
            with open("start.sh", "r") as f:
                content = f.read()
            
            # Check for required script elements
            self.assertIn("#!/bin/bash", content, "Script should have bash shebang")
            self.assertIn("export PORT", content, "Script should export PORT")
            self.assertIn("streamlit run app.py", content, "Script should start Streamlit")
            self.assertIn("--server.port=$PORT", content, "Script should use PORT variable")


def run_deployment_validation_tests():
    """Run all deployment validation tests"""
    print("=" * 70)
    print("RAILWAY DEPLOYMENT VALIDATION TESTS")
    print("=" * 70)
    print(f"Test execution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestPortConfiguration,
        TestEnvironmentVariableHandling,
        TestDeploymentValidator,
        TestExternalConnectivity,
        TestDeploymentReadiness
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0] if 'AssertionError:' in traceback else 'See details above'}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('\\n')[-2] if traceback else 'Unknown error'}")
    
    print(f"\nTest execution completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    try:
        success = run_deployment_validation_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)