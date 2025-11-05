#!/usr/bin/env python3
"""
External Access and Functionality Validation
Tests the deployed Railway application for external access and functionality
"""

import requests
import time
import json
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExternalAccessValidator:
    def __init__(self, base_url="https://connector-finacefly.up.railway.app"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "tests": {},
            "overall_status": "UNKNOWN",
            "errors": [],
            "warnings": [],
            "functionality_score": 0
        }
        
        # Configure session headers
        self.session.headers.update({
            'User-Agent': 'Railway-Deployment-Validator/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
    def log_result(self, test_name, status, message, details=None):
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
            self.test_results["functionality_score"] += 1
        elif status == "FAIL":
            logger.error(f"❌ {test_name}: {message}")
            self.test_results["errors"].append(f"{test_name}: {message}")
        elif status == "WARNING":
            logger.warning(f"⚠️ {test_name}: {message}")
            self.test_results["warnings"].append(f"{test_name}: {message}")
            
    def test_basic_connectivity(self):
        """Test basic HTTP connectivity to the Railway URL"""
        test_name = "Basic Connectivity"
        
        try:
            logger.info(f"Testing connectivity to {self.base_url}...")
            
            response = self.session.get(self.base_url, timeout=30)
            
            # Log response details
            details = {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "content_length": len(response.content),
                "headers": dict(response.headers)
            }
            
            if response.status_code == 200:
                self.log_result(
                    test_name, 
                    "PASS", 
                    f"Successfully connected. Response time: {details['response_time']:.2f}s",
                    details
                )
                return True
            elif response.status_code == 502:
                self.log_result(
                    test_name, 
                    "FAIL", 
                    "502 Bad Gateway - Application not responding correctly",
                    details
                )
                return False
            elif response.status_code == 503:
                self.log_result(
                    test_name, 
                    "FAIL", 
                    "503 Service Unavailable - Application may be starting up",
                    details
                )
                return False
            else:
                self.log_result(
                    test_name, 
                    "FAIL", 
                    f"Unexpected HTTP status: {response.status_code}",
                    details
                )
                return False
                
        except requests.exceptions.Timeout:
            self.log_result(test_name, "FAIL", "Connection timeout after 30 seconds")
            return False
        except requests.exceptions.ConnectionError as e:
            self.log_result(test_name, "FAIL", f"Connection error: {str(e)}")
            return False
        except Exception as e:
            self.log_result(test_name, "FAIL", f"Connectivity test failed: {str(e)}")
            return False
            
    def test_streamlit_interface(self):
        """Test if Streamlit interface loads correctly"""
        test_name = "Streamlit Interface"
        
        try:
            response = self.session.get(self.base_url, timeout=30)
            
            if response.status_code != 200:
                self.log_result(test_name, "FAIL", f"Cannot test interface - HTTP {response.status_code}")
                return False
                
            content = response.text.lower()
            
            # Check for Streamlit indicators
            streamlit_indicators = [
                "streamlit",
                "st-emotion-cache",
                "data-testid",
                "streamlit-container"
            ]
            
            found_indicators = [indicator for indicator in streamlit_indicators if indicator in content]
            
            if found_indicators:
                self.log_result(
                    test_name, 
                    "PASS", 
                    f"Streamlit interface detected. Indicators: {found_indicators}",
                    {"indicators_found": found_indicators, "content_length": len(content)}
                )
                return True
            else:
                # Check for application-specific content
                app_indicators = ["financefly", "pluggy", "connector"]
                found_app_indicators = [indicator for indicator in app_indicators if indicator in content]
                
                if found_app_indicators:
                    self.log_result(
                        test_name, 
                        "WARNING", 
                        f"Application content found but Streamlit indicators missing: {found_app_indicators}"
                    )
                    return True
                else:
                    self.log_result(
                        test_name, 
                        "FAIL", 
                        "No Streamlit or application indicators found in response"
                    )
                    return False
                    
        except Exception as e:
            self.log_result(test_name, "FAIL", f"Interface test failed: {str(e)}")
            return False
            
    def test_application_content(self):
        """Test for specific application content"""
        test_name = "Application Content"
        
        try:
            response = self.session.get(self.base_url, timeout=30)
            
            if response.status_code != 200:
                self.log_result(test_name, "FAIL", f"Cannot test content - HTTP {response.status_code}")
                return False
                
            content = response.text.lower()
            
            # Check for expected application elements
            expected_elements = {
                "title": ["financefly connector", "financefly", "connector"],
                "form_elements": ["nome", "email", "e-mail", "input", "form"],
                "pluggy_integration": ["pluggy", "connect", "conta bancária", "conectar"],
                "interface_elements": ["button", "submit", "conectar conta"]
            }
            
            found_elements = {}
            total_categories = len(expected_elements)
            found_categories = 0
            
            for category, keywords in expected_elements.items():
                found_keywords = [keyword for keyword in keywords if keyword in content]
                if found_keywords:
                    found_elements[category] = found_keywords
                    found_categories += 1
                    
            if found_categories >= total_categories * 0.75:  # 75% of categories found
                self.log_result(
                    test_name, 
                    "PASS", 
                    f"Application content validated. Found {found_categories}/{total_categories} content categories",
                    {"found_elements": found_elements}
                )
                return True
            elif found_categories > 0:
                self.log_result(
                    test_name, 
                    "WARNING", 
                    f"Partial application content found. {found_categories}/{total_categories} categories",
                    {"found_elements": found_elements}
                )
                return True
            else:
                self.log_result(
                    test_name, 
                    "FAIL", 
                    "No expected application content found"
                )
                return False
                
        except Exception as e:
            self.log_result(test_name, "FAIL", f"Content test failed: {str(e)}")
            return False
            
    def test_static_resources(self):
        """Test static resource loading"""
        test_name = "Static Resources"
        
        try:
            # Test common static resource paths
            static_paths = [
                "/static/pluggy_connect.js",
                "/static/pluggy_loader.js"
            ]
            
            accessible_resources = []
            failed_resources = []
            
            for path in static_paths:
                try:
                    url = urljoin(self.base_url, path)
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        accessible_resources.append(path)
                    else:
                        failed_resources.append(f"{path} (HTTP {response.status_code})")
                        
                except Exception as e:
                    failed_resources.append(f"{path} ({str(e)})")
                    
            if accessible_resources:
                self.log_result(
                    test_name, 
                    "PASS", 
                    f"Static resources accessible: {accessible_resources}",
                    {"accessible": accessible_resources, "failed": failed_resources}
                )
                return True
            elif not static_paths:
                self.log_result(test_name, "PASS", "No static resources to test")
                return True
            else:
                self.log_result(
                    test_name, 
                    "WARNING", 
                    f"Static resources not accessible: {failed_resources}"
                )
                return False
                
        except Exception as e:
            self.log_result(test_name, "FAIL", f"Static resources test failed: {str(e)}")
            return False
            
    def test_response_performance(self):
        """Test response performance and reliability"""
        test_name = "Response Performance"
        
        try:
            # Test multiple requests to check consistency
            response_times = []
            status_codes = []
            
            for i in range(3):
                try:
                    start_time = time.time()
                    response = self.session.get(self.base_url, timeout=30)
                    end_time = time.time()
                    
                    response_time = end_time - start_time
                    response_times.append(response_time)
                    status_codes.append(response.status_code)
                    
                    time.sleep(1)  # Brief pause between requests
                    
                except Exception as e:
                    logger.warning(f"Performance test request {i+1} failed: {str(e)}")
                    
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                consistent_status = len(set(status_codes)) == 1
                
                details = {
                    "average_response_time": avg_response_time,
                    "max_response_time": max_response_time,
                    "response_times": response_times,
                    "status_codes": status_codes,
                    "consistent_status": consistent_status
                }
                
                if avg_response_time < 10.0 and consistent_status and all(code == 200 for code in status_codes):
                    self.log_result(
                        test_name, 
                        "PASS", 
                        f"Good performance. Avg: {avg_response_time:.2f}s, Max: {max_response_time:.2f}s",
                        details
                    )
                    return True
                elif consistent_status and all(code == 200 for code in status_codes):
                    self.log_result(
                        test_name, 
                        "WARNING", 
                        f"Slow performance. Avg: {avg_response_time:.2f}s, Max: {max_response_time:.2f}s",
                        details
                    )
                    return True
                else:
                    self.log_result(
                        test_name, 
                        "FAIL", 
                        f"Inconsistent responses or errors. Status codes: {status_codes}",
                        details
                    )
                    return False
            else:
                self.log_result(test_name, "FAIL", "No successful requests for performance testing")
                return False
                
        except Exception as e:
            self.log_result(test_name, "FAIL", f"Performance test failed: {str(e)}")
            return False
            
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        test_name = "Error Handling"
        
        try:
            # Test invalid paths
            invalid_paths = ["/nonexistent", "/invalid-page", "/test-404"]
            
            error_responses = []
            
            for path in invalid_paths:
                try:
                    url = urljoin(self.base_url, path)
                    response = self.session.get(url, timeout=10)
                    error_responses.append({
                        "path": path,
                        "status_code": response.status_code,
                        "handled": response.status_code in [404, 200]  # Streamlit might redirect to main page
                    })
                except Exception as e:
                    error_responses.append({
                        "path": path,
                        "error": str(e),
                        "handled": False
                    })
                    
            handled_errors = [resp for resp in error_responses if resp.get("handled", False)]
            
            if len(handled_errors) >= len(error_responses) * 0.5:  # At least 50% handled properly
                self.log_result(
                    test_name, 
                    "PASS", 
                    f"Error handling working. {len(handled_errors)}/{len(error_responses)} errors handled",
                    {"error_responses": error_responses}
                )
                return True
            else:
                self.log_result(
                    test_name, 
                    "WARNING", 
                    f"Limited error handling. {len(handled_errors)}/{len(error_responses)} errors handled",
                    {"error_responses": error_responses}
                )
                return False
                
        except Exception as e:
            self.log_result(test_name, "FAIL", f"Error handling test failed: {str(e)}")
            return False
            
    def run_validation(self):
        """Run complete external access validation"""
        logger.info("🌐 Starting External Access and Functionality Validation")
        logger.info(f"Target URL: {self.base_url}")
        logger.info("=" * 70)
        
        # Define test suite
        tests = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("Streamlit Interface", self.test_streamlit_interface),
            ("Application Content", self.test_application_content),
            ("Static Resources", self.test_static_resources),
            ("Response Performance", self.test_response_performance),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        # Run tests
        for test_name, test_func in tests:
            logger.info(f"Running {test_name} test...")
            try:
                if test_func():
                    passed_tests += 1
                else:
                    logger.error(f"{test_name} test failed")
            except Exception as e:
                logger.error(f"{test_name} test failed with exception: {str(e)}")
                
        # Calculate overall status
        success_rate = passed_tests / total_tests
        
        if success_rate >= 0.9:
            self.test_results["overall_status"] = "EXCELLENT"
        elif success_rate >= 0.75:
            self.test_results["overall_status"] = "GOOD"
        elif success_rate >= 0.5:
            self.test_results["overall_status"] = "ACCEPTABLE"
        else:
            self.test_results["overall_status"] = "POOR"
            
        # Log summary
        logger.info("=" * 70)
        logger.info(f"🏁 External Access Validation Complete")
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"Success Rate: {success_rate:.1%}")
        logger.info(f"Overall Status: {self.test_results['overall_status']}")
        logger.info(f"Functionality Score: {self.test_results['functionality_score']}")
        
        if self.test_results["errors"]:
            logger.info(f"Errors: {len(self.test_results['errors'])}")
            
        if self.test_results["warnings"]:
            logger.info(f"Warnings: {len(self.test_results['warnings'])}")
            
        return self.test_results
        
    def save_results(self, filename="external_access_validation.json"):
        """Save validation results to JSON file"""
        try:
            with open(filename, "w") as f:
                json.dump(self.test_results, f, indent=2)
            logger.info(f"📄 Validation results saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")

def main():
    """Main function"""
    # Allow custom URL via command line argument
    base_url = "https://connector-finacefly.up.railway.app"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        
    validator = ExternalAccessValidator(base_url)
    
    try:
        results = validator.run_validation()
        validator.save_results()
        
        # Exit with appropriate code based on results
        if results["overall_status"] in ["EXCELLENT", "GOOD"]:
            sys.exit(0)
        elif results["overall_status"] == "ACCEPTABLE":
            sys.exit(1)
        else:
            sys.exit(2)
            
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()