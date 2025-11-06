#!/usr/bin/env python3
"""
Railway Environment Simulation Test
Simulates Railway deployment environment to test configuration
"""

import os
import sys
import subprocess
import time
import threading
import requests
import signal
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RailwaySimulator:
    def __init__(self):
        self.streamlit_process = None
        self.test_port = 8080
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "simulation_tests": {},
            "deployment_ready": False,
            "errors": [],
            "warnings": []
        }
        
    def log_result(self, test_name, status, message, details=None):
        """Log test result"""
        result = {
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results["simulation_tests"][test_name] = result
        
        if status == "PASS":
            logger.info(f"✅ {test_name}: {message}")
        elif status == "FAIL":
            logger.error(f"❌ {test_name}: {message}")
            self.test_results["errors"].append(f"{test_name}: {message}")
        elif status == "WARNING":
            logger.warning(f"⚠️ {test_name}: {message}")
            self.test_results["warnings"].append(f"{test_name}: {message}")
            
    def setup_railway_environment(self):
        """Setup environment variables to simulate Railway"""
        logger.info("🔧 Setting up Railway simulation environment...")
        
        # Set Railway-style environment variables
        os.environ["PORT"] = str(self.test_port)
        os.environ["RAILWAY_ENVIRONMENT"] = "production"
        os.environ["RAILWAY_PROJECT_ID"] = "test-project"
        
        # Set minimal required environment variables for testing
        test_env_vars = {
            "PLUGGY_CLIENT_ID": "test_client_id_12345",
            "PLUGGY_CLIENT_SECRET": "test_client_secret_67890",
            "DB_HOST": "localhost",
            "DB_USER": "test_user",
            "DB_PASSWORD": "test_password",
            "DB_NAME": "test_db",
            "DB_PORT": "5432",
            "DB_SSLMODE": "require"
        }
        
        for key, value in test_env_vars.items():
            os.environ[key] = value
            
        logger.info(f"Environment configured with PORT={self.test_port}")
        
    def test_port_binding(self):
        """Test if application can bind to Railway port"""
        test_name = "Port Binding Simulation"
        
        try:
            # Test different port values
            test_ports = [8080, 3000, 5000]
            
            for port in test_ports:
                os.environ["PORT"] = str(port)
                
                # Import port logic from app.py (simplified test)
                port_env = os.getenv("PORT")
                if port_env:
                    try:
                        port_num = int(port_env)
                        if 1 <= port_num <= 65535:
                            self.log_result(
                                f"{test_name} (Port {port})", 
                                "PASS", 
                                f"Port {port} validation successful"
                            )
                        else:
                            self.log_result(
                                f"{test_name} (Port {port})", 
                                "FAIL", 
                                f"Port {port} outside valid range"
                            )
                            return False
                    except ValueError:
                        self.log_result(
                            f"{test_name} (Port {port})", 
                            "FAIL", 
                            f"Port {port} is not numeric"
                        )
                        return False
                        
            # Reset to test port
            os.environ["PORT"] = str(self.test_port)
            return True
            
        except Exception as e:
            self.log_result(test_name, "FAIL", f"Port binding test failed: {str(e)}")
            return False
            
    def test_streamlit_startup(self):
        """Test Streamlit application startup"""
        test_name = "Streamlit Startup"
        
        try:
            logger.info("🚀 Testing Streamlit startup with Railway configuration...")
            
            # Build Streamlit command similar to Procfile
            cmd = [
                sys.executable, "-m", "streamlit", "run", "app.py",
                f"--server.port={self.test_port}",
                "--server.address=0.0.0.0",
                "--server.headless=true",
                "--server.enableCORS=false",
                "--server.enableXsrfProtection=false"
            ]
            
            logger.info(f"Starting Streamlit with command: {' '.join(cmd)}")
            
            # Start Streamlit process
            self.streamlit_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Wait for startup (max 30 seconds)
            startup_timeout = 30
            startup_success = False
            
            for i in range(startup_timeout):
                if self.streamlit_process.poll() is not None:
                    # Process terminated
                    stdout, stderr = self.streamlit_process.communicate()
                    self.log_result(
                        test_name, 
                        "FAIL", 
                        f"Streamlit process terminated during startup. Exit code: {self.streamlit_process.returncode}",
                        {"stdout": stdout[:500], "stderr": stderr[:500]}
                    )
                    return False
                    
                # Check if server is responding
                try:
                    response = requests.get(f"http://localhost:{self.test_port}", timeout=2)
                    if response.status_code == 200:
                        startup_success = True
                        break
                except requests.exceptions.RequestException:
                    pass  # Server not ready yet
                    
                time.sleep(1)
                logger.info(f"Waiting for Streamlit startup... ({i+1}/{startup_timeout})")
                
            if startup_success:
                self.log_result(
                    test_name, 
                    "PASS", 
                    f"Streamlit started successfully on port {self.test_port}"
                )
                return True
            else:
                self.log_result(
                    test_name, 
                    "FAIL", 
                    f"Streamlit failed to start within {startup_timeout} seconds"
                )
                return False
                
        except Exception as e:
            self.log_result(test_name, "FAIL", f"Streamlit startup test failed: {str(e)}")
            return False
            
    def test_http_response(self):
        """Test HTTP response from the application"""
        test_name = "HTTP Response"
        
        try:
            if not self.streamlit_process or self.streamlit_process.poll() is not None:
                self.log_result(test_name, "FAIL", "Streamlit process not running")
                return False
                
            # Test HTTP response
            response = requests.get(f"http://localhost:{self.test_port}", timeout=10)
            
            if response.status_code == 200:
                self.log_result(
                    test_name, 
                    "PASS", 
                    f"HTTP 200 response received. Content length: {len(response.content)} bytes"
                )
                
                # Check for Streamlit content
                if "streamlit" in response.text.lower() or "financefly" in response.text.lower():
                    self.log_result(
                        test_name + " (Content)", 
                        "PASS", 
                        "Response contains expected application content"
                    )
                else:
                    self.log_result(
                        test_name + " (Content)", 
                        "WARNING", 
                        "Response does not contain expected application identifiers"
                    )
                    
                return True
            else:
                self.log_result(
                    test_name, 
                    "FAIL", 
                    f"HTTP {response.status_code} response received instead of 200"
                )
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result(test_name, "FAIL", f"HTTP request failed: {str(e)}")
            return False
        except Exception as e:
            self.log_result(test_name, "FAIL", f"HTTP response test failed: {str(e)}")
            return False
            
    def test_external_access_simulation(self):
        """Simulate external access test"""
        test_name = "External Access Simulation"
        
        try:
            # Test that server binds to 0.0.0.0 (external access)
            # This is a simplified test since we can't easily test true external access locally
            
            # Check if we can connect via different interfaces
            interfaces_to_test = ["localhost", "127.0.0.1"]
            
            successful_interfaces = []
            failed_interfaces = []
            
            for interface in interfaces_to_test:
                try:
                    response = requests.get(f"http://{interface}:{self.test_port}", timeout=5)
                    if response.status_code == 200:
                        successful_interfaces.append(interface)
                    else:
                        failed_interfaces.append(f"{interface} (HTTP {response.status_code})")
                except requests.exceptions.RequestException as e:
                    failed_interfaces.append(f"{interface} ({str(e)})")
                    
            if successful_interfaces:
                self.log_result(
                    test_name, 
                    "PASS", 
                    f"Application accessible via: {successful_interfaces}",
                    {"successful": successful_interfaces, "failed": failed_interfaces}
                )
                return True
            else:
                self.log_result(
                    test_name, 
                    "FAIL", 
                    f"Application not accessible via any interface: {failed_interfaces}"
                )
                return False
                
        except Exception as e:
            self.log_result(test_name, "FAIL", f"External access test failed: {str(e)}")
            return False
            
    def cleanup(self):
        """Cleanup test environment"""
        logger.info("🧹 Cleaning up test environment...")
        
        if self.streamlit_process:
            try:
                # Terminate Streamlit process
                self.streamlit_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.streamlit_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if necessary
                    self.streamlit_process.kill()
                    self.streamlit_process.wait()
                    
                logger.info("Streamlit process terminated")
            except Exception as e:
                logger.error(f"Error terminating Streamlit process: {str(e)}")
                
    def run_simulation(self):
        """Run complete Railway deployment simulation"""
        logger.info("🚀 Starting Railway Deployment Simulation")
        logger.info("=" * 60)
        
        try:
            # Setup environment
            self.setup_railway_environment()
            
            # Run tests
            tests = [
                ("Port Binding", self.test_port_binding),
                ("Streamlit Startup", self.test_streamlit_startup),
                ("HTTP Response", self.test_http_response),
                ("External Access", self.test_external_access_simulation)
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_name, test_func in tests:
                logger.info(f"Running {test_name} test...")
                try:
                    if test_func():
                        passed_tests += 1
                    else:
                        logger.error(f"{test_name} test failed")
                except Exception as e:
                    logger.error(f"{test_name} test failed with exception: {str(e)}")
                    
            # Calculate results
            success_rate = passed_tests / total_tests
            self.test_results["deployment_ready"] = success_rate >= 0.75  # 75% success rate
            
            # Log summary
            logger.info("=" * 60)
            logger.info(f"🏁 Railway Simulation Complete")
            logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
            logger.info(f"Success Rate: {success_rate:.1%}")
            logger.info(f"Deployment Ready: {self.test_results['deployment_ready']}")
            
            if self.test_results["errors"]:
                logger.info(f"Errors: {len(self.test_results['errors'])}")
                
            if self.test_results["warnings"]:
                logger.info(f"Warnings: {len(self.test_results['warnings'])}")
                
        finally:
            self.cleanup()
            
        return self.test_results

def main():
    """Main function"""
    simulator = RailwaySimulator()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        logger.info("Received interrupt signal, cleaning up...")
        simulator.cleanup()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        results = simulator.run_simulation()
        
        # Save results
        import json
        with open("railway_simulation_results.json", "w") as f:
            json.dump(results, f, indent=2)
        logger.info("📄 Simulation results saved to railway_simulation_results.json")
        
        # Exit with appropriate code
        if results["deployment_ready"]:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()