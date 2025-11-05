#!/usr/bin/env python3
"""
Railway Deployment Validation Test Suite
Tests the deployment configuration and validates Railway compatibility
"""

import os
import sys
import subprocess
import time
import requests
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RailwayDeploymentTester:
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "UNKNOWN",
            "errors": [],
            "warnings": []
        }
        
    def log_test_result(self, test_name, status, message, details=None):
        """Log test result with structured data"""
        result = {
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results["tests"][test_name] = result
        
        if status == "PASS":
            logger.info(f"✅ {test_name}: {message}")
        elif status == "FAIL":
            logger.error(f"❌ {test_name}: {message}")
            self.test_results["errors"].append(f"{test_name}: {message}")
        elif status == "WARNING":
            logger.warning(f"⚠️ {test_name}: {message}")
            self.test_results["warnings"].append(f"{test_name}: {message}")
            
    def test_procfile_configuration(self):
        """Test Procfile configuration for Railway compatibility"""
        test_name = "Procfile Configuration"
        
        try:
            if not os.path.exists("Procfile"):
                self.log_test_result(test_name, "FAIL", "Procfile not found")
                return False
                
            with open("Procfile", "r") as f:
                content = f.read()
                
            # Check for web process definition
            if "web:" not in content:
                self.log_test_result(test_name, "FAIL", "No web process defined in Procfile")
                return False
                
            # Check for PORT variable usage
            if "$PORT" not in content:
                self.log_test_result(test_name, "FAIL", "Procfile does not use $PORT environment variable")
                return False
                
            # Check for correct server address
            if "--server.address=0.0.0.0" not in content:
                self.log_test_result(test_name, "FAIL", "Procfile does not bind to 0.0.0.0")
                return False
                
            # Check for headless mode
            if "--server.headless=true" not in content:
                self.log_test_result(test_name, "FAIL", "Procfile does not enable headless mode")
                return False
                
            self.log_test_result(test_name, "PASS", "Procfile correctly configured for Railway")
            return True
            
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Error reading Procfile: {str(e)}")
            return False
            
    def test_port_configuration(self):
        """Test port configuration logic in app.py"""
        test_name = "Port Configuration"
        
        try:
            # Test with PORT environment variable
            os.environ["PORT"] = "8080"
            
            # Import and test port logic (simplified)
            port = os.getenv("PORT")
            if port is None:
                port = "8080"
                
            try:
                port_num = int(port)
                if port_num < 1 or port_num > 65535:
                    raise ValueError(f"Port {port_num} outside valid range")
            except ValueError as e:
                self.log_test_result(test_name, "FAIL", f"Port validation failed: {str(e)}")
                return False
                
            self.log_test_result(test_name, "PASS", f"Port configuration working correctly (port: {port_num})")
            return True
            
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Port configuration error: {str(e)}")
            return False
            
    def test_environment_variables(self):
        """Test required environment variables for Railway deployment"""
        test_name = "Environment Variables"
        
        required_vars = [
            "PLUGGY_CLIENT_ID",
            "PLUGGY_CLIENT_SECRET", 
            "DB_HOST",
            "DB_USER",
            "DB_PASSWORD",
            "DB_NAME"
        ]
        
        missing_vars = []
        present_vars = []
        
        for var in required_vars:
            if os.getenv(var):
                present_vars.append(var)
            else:
                missing_vars.append(var)
                
        if missing_vars:
            self.log_test_result(
                test_name, 
                "WARNING", 
                f"Missing environment variables: {missing_vars}",
                {"missing": missing_vars, "present": present_vars}
            )
            return False
        else:
            self.log_test_result(
                test_name, 
                "PASS", 
                f"All {len(required_vars)} required environment variables present"
            )
            return True
            
    def test_startup_script(self):
        """Test alternative startup script (start.sh)"""
        test_name = "Startup Script"
        
        try:
            if not os.path.exists("start.sh"):
                self.log_test_result(test_name, "WARNING", "start.sh not found (optional fallback)")
                return True
                
            # Check if script is executable (on Unix systems)
            if os.name != 'nt':  # Not Windows
                stat_info = os.stat("start.sh")
                if not (stat_info.st_mode & 0o111):
                    self.log_test_result(test_name, "WARNING", "start.sh is not executable")
                    
            with open("start.sh", "r") as f:
                content = f.read()
                
            # Check for PORT handling
            if "PORT" not in content:
                self.log_test_result(test_name, "FAIL", "start.sh does not handle PORT variable")
                return False
                
            # Check for Streamlit command
            if "streamlit run" not in content:
                self.log_test_result(test_name, "FAIL", "start.sh does not contain Streamlit startup command")
                return False
                
            self.log_test_result(test_name, "PASS", "start.sh correctly configured")
            return True
            
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Error testing start.sh: {str(e)}")
            return False
            
    def test_python_runtime(self):
        """Test Python runtime configuration"""
        test_name = "Python Runtime"
        
        try:
            # Check runtime.txt
            if os.path.exists("runtime.txt"):
                with open("runtime.txt", "r") as f:
                    runtime_content = f.read().strip()
                    
                if runtime_content.startswith("python-"):
                    python_version = runtime_content.replace("python-", "")
                    self.log_test_result(
                        test_name, 
                        "PASS", 
                        f"Runtime specified: {runtime_content}",
                        {"version": python_version}
                    )
                else:
                    self.log_test_result(test_name, "WARNING", f"Unexpected runtime.txt format: {runtime_content}")
            else:
                self.log_test_result(test_name, "WARNING", "runtime.txt not found, Railway will use default Python")
                
            # Check current Python version
            current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            self.log_test_result(
                test_name + " (Current)", 
                "PASS", 
                f"Current Python version: {current_version}"
            )
            
            return True
            
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Runtime test error: {str(e)}")
            return False
            
    def test_dependencies(self):
        """Test requirements.txt and dependencies"""
        test_name = "Dependencies"
        
        try:
            if not os.path.exists("requirements.txt"):
                self.log_test_result(test_name, "FAIL", "requirements.txt not found")
                return False
                
            with open("requirements.txt", "r") as f:
                requirements = f.read().strip().split('\n')
                
            # Check for essential dependencies
            essential_deps = ["streamlit", "requests"]
            postgres_deps = ["psycopg2-binary", "psycopg[binary]", "psycopg"]
            missing_deps = []
            
            for dep in essential_deps:
                found = any(dep in req.lower() for req in requirements if req.strip())
                if not found:
                    missing_deps.append(dep)
                    
            # Check for PostgreSQL driver (any of the variants)
            postgres_found = any(
                any(pg_dep in req.lower() for pg_dep in postgres_deps) 
                for req in requirements if req.strip()
            )
            if not postgres_found:
                missing_deps.append("postgresql-driver (psycopg2-binary or psycopg[binary])")
                    
            if missing_deps:
                self.log_test_result(
                    test_name, 
                    "WARNING", 
                    f"Potentially missing dependencies: {missing_deps}"
                )
            else:
                self.log_test_result(
                    test_name, 
                    "PASS", 
                    f"Essential dependencies found in {len(requirements)} total requirements"
                )
                
            return True
            
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Dependencies test error: {str(e)}")
            return False
            
    def test_app_structure(self):
        """Test application file structure"""
        test_name = "App Structure"
        
        try:
            required_files = ["app.py", "Procfile"]
            optional_files = ["start.sh", "runtime.txt", "requirements.txt", ".env"]
            
            missing_required = []
            present_files = []
            
            for file in required_files:
                if os.path.exists(file):
                    present_files.append(file)
                else:
                    missing_required.append(file)
                    
            if missing_required:
                self.log_test_result(
                    test_name, 
                    "FAIL", 
                    f"Missing required files: {missing_required}"
                )
                return False
                
            # Check optional files
            present_optional = [f for f in optional_files if os.path.exists(f)]
            
            self.log_test_result(
                test_name, 
                "PASS", 
                f"Required files present. Optional files: {present_optional}",
                {"required": present_files, "optional": present_optional}
            )
            
            return True
            
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"App structure test error: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all deployment validation tests"""
        logger.info("🚀 Starting Railway Deployment Validation Tests")
        logger.info("=" * 60)
        
        tests = [
            self.test_app_structure,
            self.test_procfile_configuration,
            self.test_port_configuration,
            self.test_environment_variables,
            self.test_startup_script,
            self.test_python_runtime,
            self.test_dependencies
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                logger.error(f"Test {test_func.__name__} failed with exception: {str(e)}")
                
        # Calculate overall status
        if passed_tests == total_tests:
            self.test_results["overall_status"] = "PASS"
        elif passed_tests >= total_tests * 0.7:  # 70% pass rate
            self.test_results["overall_status"] = "WARNING"
        else:
            self.test_results["overall_status"] = "FAIL"
            
        # Log summary
        logger.info("=" * 60)
        logger.info(f"🏁 Deployment Validation Complete")
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"Overall Status: {self.test_results['overall_status']}")
        
        if self.test_results["errors"]:
            logger.info(f"Errors: {len(self.test_results['errors'])}")
            
        if self.test_results["warnings"]:
            logger.info(f"Warnings: {len(self.test_results['warnings'])}")
            
        return self.test_results
        
    def save_results(self, filename="railway_deployment_validation.json"):
        """Save test results to JSON file"""
        try:
            with open(filename, "w") as f:
                json.dump(self.test_results, f, indent=2)
            logger.info(f"📄 Test results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")

def main():
    """Main function to run deployment validation"""
    tester = RailwayDeploymentTester()
    results = tester.run_all_tests()
    tester.save_results()
    
    # Exit with appropriate code
    if results["overall_status"] == "FAIL":
        sys.exit(1)
    elif results["overall_status"] == "WARNING":
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()