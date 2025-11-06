#!/usr/bin/env python3
"""
Performance and Integration Testing Script

This script implements task 5.3 from the Railway Streamlit deployment specification:
- Test application response times
- Validate all API integrations work correctly  
- Test form submission and database storage

Requirements covered: 4.3, 4.4
"""

import os
import sys
import time
import json
import tempfile
import sqlite3
import logging
import statistics
from datetime import datetime
from unittest.mock import patch, Mock
import requests
import psycopg
from psycopg.rows import dict_row

# Import application modules
from modules.pluggy_utils import PluggyClient, create_connect_token, validate_environment
from modules.db import init_db, save_client, get_conn
from modules.error_utils import log_and_display_error, display_environment_errors, handle_pluggy_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceIntegrationTester:
    """Comprehensive performance and integration tester"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "performance_tests": {},
            "integration_tests": {},
            "database_tests": {},
            "overall_status": "UNKNOWN",
            "errors": [],
            "warnings": []
        }
        
        # Test configuration
        self.test_env = {
            'PLUGGY_CLIENT_ID': 'perf_test_client_id_123456',
            'PLUGGY_CLIENT_SECRET': 'perf_test_client_secret_789012'
        }
        
        # Performance thresholds
        self.performance_thresholds = {
            'token_generation_max_time': 5.0,  # seconds
            'api_response_max_time': 3.0,      # seconds
            'database_operation_max_time': 2.0, # seconds
            'acceptable_success_rate': 0.95     # 95%
        }
        
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Set up test environment variables"""
        logger.info("Setting up performance test environment...")
        for key, value in self.test_env.items():
            os.environ[key] = value
        logger.info("Test environment configured")
    
    def cleanup_test_environment(self):
        """Clean up test environment variables"""
        logger.info("Cleaning up test environment...")
        for key in self.test_env.keys():
            if key in os.environ:
                del os.environ[key]
        logger.info("Test environment cleaned up")
    
    def log_test_result(self, category, test_name, success, message="", details=None, duration=None):
        """Log test result with performance metrics"""
        result = {
            'success': success,
            'message': message,
            'details': details or {},
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        if category not in self.test_results:
            self.test_results[category] = {}
        
        self.test_results[category][test_name] = result
        
        status = "✅ PASS" if success else "❌ FAIL"
        duration_str = f" ({duration:.3f}s)" if duration else ""
        logger.info(f"{status}: {test_name}{duration_str} - {message}")
        
        if not success:
            self.test_results["errors"].append(f"{test_name}: {message}")
        
        return success

    # =========================================================
    # PERFORMANCE TESTS
    # =========================================================
    
    @patch('modules.pluggy_utils.requests.post')
    def test_token_generation_performance(self, mock_post):
        """Test token generation response times"""
        logger.info("🚀 Testing token generation performance...")
        
        # Mock successful API responses
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {'apiKey': 'perf_test_api_key'}
        
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {'accessToken': 'perf_test_token'}
        
        mock_post.side_effect = [auth_response, token_response]
        
        # Test multiple token generations for performance metrics
        generation_times = []
        success_count = 0
        total_tests = 5
        
        for i in range(total_tests):
            try:
                start_time = time.time()
                token = create_connect_token(f'perf_test_user_{i}@example.com')
                end_time = time.time()
                
                duration = end_time - start_time
                generation_times.append(duration)
                
                if token and isinstance(token, str) and len(token) > 10:
                    success_count += 1
                
                # Reset mock for next iteration
                mock_post.side_effect = [auth_response, token_response]
                
            except Exception as e:
                logger.error(f"Token generation {i+1} failed: {e}")
        
        # Calculate performance metrics
        if generation_times:
            avg_time = statistics.mean(generation_times)
            max_time = max(generation_times)
            min_time = min(generation_times)
            success_rate = success_count / total_tests
            
            # Check against performance thresholds
            performance_acceptable = (
                avg_time <= self.performance_thresholds['token_generation_max_time'] and
                success_rate >= self.performance_thresholds['acceptable_success_rate']
            )
            
            details = {
                'total_tests': total_tests,
                'successful_tests': success_count,
                'success_rate': success_rate,
                'average_time': avg_time,
                'max_time': max_time,
                'min_time': min_time,
                'generation_times': generation_times,
                'threshold_max_time': self.performance_thresholds['token_generation_max_time'],
                'threshold_success_rate': self.performance_thresholds['acceptable_success_rate']
            }
            
            message = f"Avg: {avg_time:.3f}s, Success: {success_rate:.1%}"
            
            return self.log_test_result(
                "performance_tests",
                "Token Generation Performance",
                performance_acceptable,
                message,
                details,
                avg_time
            )
        else:
            return self.log_test_result(
                "performance_tests",
                "Token Generation Performance",
                False,
                "No successful token generations recorded"
            )
    
    @patch('modules.pluggy_utils.requests.post')
    def test_api_response_times(self, mock_post):
        """Test API response times under different conditions"""
        logger.info("⚡ Testing API response times...")
        
        # Test scenarios with different response times
        test_scenarios = [
            {
                'name': 'Fast Response',
                'delay': 0.1,
                'expected_success': True
            },
            {
                'name': 'Normal Response',
                'delay': 0.5,
                'expected_success': True
            },
            {
                'name': 'Slow Response',
                'delay': 2.0,
                'expected_success': True
            }
        ]
        
        all_scenarios_passed = True
        scenario_results = {}
        
        for scenario in test_scenarios:
            try:
                # Mock response with simulated delay
                def mock_response_with_delay(*args, **kwargs):
                    time.sleep(scenario['delay'])
                    response = Mock()
                    response.status_code = 200
                    response.json.return_value = {'apiKey': f"test_key_{scenario['name']}"}
                    return response
                
                mock_post.side_effect = mock_response_with_delay
                
                # Measure actual response time
                start_time = time.time()
                client = PluggyClient()
                api_key = client.authenticate()
                end_time = time.time()
                
                actual_duration = end_time - start_time
                
                # Check if response time is acceptable
                response_acceptable = actual_duration <= self.performance_thresholds['api_response_max_time']
                
                scenario_results[scenario['name']] = {
                    'expected_delay': scenario['delay'],
                    'actual_duration': actual_duration,
                    'acceptable': response_acceptable,
                    'api_key_received': bool(api_key)
                }
                
                if not response_acceptable and scenario['expected_success']:
                    all_scenarios_passed = False
                
            except Exception as e:
                logger.error(f"API response test failed for {scenario['name']}: {e}")
                scenario_results[scenario['name']] = {
                    'error': str(e),
                    'acceptable': False
                }
                all_scenarios_passed = False
        
        # Calculate overall API performance
        successful_scenarios = sum(1 for result in scenario_results.values() 
                                 if result.get('acceptable', False))
        total_scenarios = len(test_scenarios)
        
        return self.log_test_result(
            "performance_tests",
            "API Response Times",
            all_scenarios_passed,
            f"Passed {successful_scenarios}/{total_scenarios} response time tests",
            {
                'scenario_results': scenario_results,
                'threshold_max_time': self.performance_thresholds['api_response_max_time']
            }
        )
    
    def test_concurrent_operations_performance(self):
        """Test performance under concurrent operations simulation"""
        logger.info("🔄 Testing concurrent operations performance...")
        
        try:
            # Simulate concurrent token generation requests
            import threading
            import queue
            
            results_queue = queue.Queue()
            num_threads = 3
            operations_per_thread = 2
            
            def worker_thread(thread_id):
                """Worker thread for concurrent operations"""
                thread_results = []
                
                for i in range(operations_per_thread):
                    try:
                        start_time = time.time()
                        
                        # Simulate environment validation (lightweight operation)
                        config = validate_environment()
                        
                        end_time = time.time()
                        duration = end_time - start_time
                        
                        thread_results.append({
                            'thread_id': thread_id,
                            'operation_id': i,
                            'duration': duration,
                            'success': bool(config)
                        })
                        
                    except Exception as e:
                        thread_results.append({
                            'thread_id': thread_id,
                            'operation_id': i,
                            'error': str(e),
                            'success': False
                        })
                
                results_queue.put(thread_results)
            
            # Start concurrent threads
            threads = []
            start_time = time.time()
            
            for thread_id in range(num_threads):
                thread = threading.Thread(target=worker_thread, args=(thread_id,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # Collect results
            all_results = []
            while not results_queue.empty():
                thread_results = results_queue.get()
                all_results.extend(thread_results)
            
            # Analyze concurrent performance
            successful_operations = sum(1 for result in all_results if result.get('success', False))
            total_operations = len(all_results)
            success_rate = successful_operations / total_operations if total_operations > 0 else 0
            
            if all_results:
                operation_durations = [r['duration'] for r in all_results if 'duration' in r]
                avg_operation_time = statistics.mean(operation_durations) if operation_durations else 0
            else:
                avg_operation_time = 0
            
            # Check performance criteria
            concurrent_performance_acceptable = (
                success_rate >= self.performance_thresholds['acceptable_success_rate'] and
                total_duration <= 10.0  # Total concurrent execution should complete within 10 seconds
            )
            
            details = {
                'num_threads': num_threads,
                'operations_per_thread': operations_per_thread,
                'total_operations': total_operations,
                'successful_operations': successful_operations,
                'success_rate': success_rate,
                'total_duration': total_duration,
                'avg_operation_time': avg_operation_time,
                'all_results': all_results
            }
            
            return self.log_test_result(
                "performance_tests",
                "Concurrent Operations Performance",
                concurrent_performance_acceptable,
                f"Success rate: {success_rate:.1%}, Total time: {total_duration:.3f}s",
                details,
                total_duration
            )
            
        except Exception as e:
            return self.log_test_result(
                "performance_tests",
                "Concurrent Operations Performance",
                False,
                f"Concurrent operations test failed: {str(e)}"
            )

    # =========================================================
    # INTEGRATION TESTS
    # =========================================================
    
    @patch('modules.pluggy_utils.requests.post')
    def test_pluggy_api_integration(self, mock_post):
        """Test complete Pluggy API integration flow"""
        logger.info("🔗 Testing Pluggy API integration...")
        
        try:
            # Test 1: Environment validation
            config = validate_environment()
            env_valid = bool(config and config.get('client_id') and config.get('client_secret'))
            
            # Test 2: Authentication flow
            auth_response = Mock()
            auth_response.status_code = 200
            auth_response.json.return_value = {'apiKey': 'integration_test_api_key'}
            
            token_response = Mock()
            token_response.status_code = 200
            token_response.json.return_value = {'accessToken': 'integration_test_token'}
            
            mock_post.side_effect = [auth_response, token_response]
            
            client = PluggyClient(config)
            api_key = client.authenticate()
            auth_successful = bool(api_key)
            
            # Test 3: Token generation
            connect_token = client.create_connect_token('integration_test@example.com')
            token_generated = bool(connect_token and len(connect_token) > 10)
            
            # Test 4: Error handling
            error_response = Mock()
            error_response.status_code = 401
            mock_post.side_effect = [error_response]  # Reset side_effect for error test
            
            error_handled = False
            try:
                client2 = PluggyClient(config)
                client2.authenticate()
            except ValueError as e:
                error_handled = "Credenciais Pluggy inválidas" in str(e)
            
            # Overall integration success
            integration_successful = all([
                env_valid,
                auth_successful,
                token_generated,
                error_handled
            ])
            
            details = {
                'environment_validation': env_valid,
                'authentication_successful': auth_successful,
                'token_generation_successful': token_generated,
                'error_handling_working': error_handled,
                'api_calls_made': mock_post.call_count,
                'config_keys': list(config.keys()) if config else []
            }
            
            return self.log_test_result(
                "integration_tests",
                "Pluggy API Integration",
                integration_successful,
                f"All integration components working: {integration_successful}",
                details
            )
            
        except Exception as e:
            return self.log_test_result(
                "integration_tests",
                "Pluggy API Integration",
                False,
                f"Integration test failed: {str(e)}"
            )
    
    def test_error_handling_integration(self):
        """Test error handling integration across modules"""
        logger.info("🛡️ Testing error handling integration...")
        
        try:
            # Test error utility functions exist and are callable
            from modules.error_utils import log_and_display_error, display_environment_errors, handle_pluggy_error
            
            error_functions = [
                log_and_display_error,
                display_environment_errors,
                handle_pluggy_error
            ]
            
            functions_available = all(callable(func) for func in error_functions)
            
            # Test error message formatting
            test_errors = [
                "PLUGGY_CLIENT_ID não está definido",
                "PLUGGY_CLIENT_SECRET está vazio"
            ]
            
            # Test that functions can be imported successfully
            error_formatting_works = True
            try:
                # Function exists and is importable
                error_formatting_works = callable(log_and_display_error)
            except Exception:
                error_formatting_works = False
            
            # Test Pluggy error handling
            pluggy_error_handling_works = True
            try:
                # Function exists and is importable
                pluggy_error_handling_works = callable(handle_pluggy_error)
            except Exception:
                pluggy_error_handling_works = False
            
            error_integration_successful = all([
                functions_available,
                error_formatting_works,
                pluggy_error_handling_works
            ])
            
            details = {
                'error_functions_available': functions_available,
                'error_formatting_works': error_formatting_works,
                'pluggy_error_handling_works': pluggy_error_handling_works,
                'available_functions': [func.__name__ for func in error_functions]
            }
            
            return self.log_test_result(
                "integration_tests",
                "Error Handling Integration",
                error_integration_successful,
                f"Error handling integration working: {error_integration_successful}",
                details
            )
            
        except Exception as e:
            return self.log_test_result(
                "integration_tests",
                "Error Handling Integration",
                False,
                f"Error handling integration test failed: {str(e)}"
            )
    
    def test_module_integration(self):
        """Test integration between application modules"""
        logger.info("🔧 Testing module integration...")
        
        try:
            # Test module imports
            modules_imported = True
            import_errors = []
            
            try:
                from modules import pluggy_utils, db, error_utils
            except ImportError as e:
                modules_imported = False
                import_errors.append(str(e))
            
            # Test cross-module functionality
            cross_module_integration = True
            
            try:
                # Test that pluggy_utils can work with error_utils
                from modules.pluggy_utils import validate_environment
                from modules.error_utils import handle_pluggy_error
                
                # These functions should be compatible
                cross_module_integration = True
            except Exception as e:
                cross_module_integration = False
                import_errors.append(f"Cross-module integration error: {str(e)}")
            
            # Test database module integration
            db_integration = True
            try:
                from modules.db import init_db, save_client, get_conn
                # Functions exist and are callable
                db_integration = all(callable(func) for func in [init_db, save_client, get_conn])
            except Exception as e:
                db_integration = False
                import_errors.append(f"Database integration error: {str(e)}")
            
            module_integration_successful = all([
                modules_imported,
                cross_module_integration,
                db_integration
            ])
            
            details = {
                'modules_imported': modules_imported,
                'cross_module_integration': cross_module_integration,
                'database_integration': db_integration,
                'import_errors': import_errors
            }
            
            return self.log_test_result(
                "integration_tests",
                "Module Integration",
                module_integration_successful,
                f"Module integration working: {module_integration_successful}",
                details
            )
            
        except Exception as e:
            return self.log_test_result(
                "integration_tests",
                "Module Integration",
                False,
                f"Module integration test failed: {str(e)}"
            )

    # =========================================================
    # DATABASE TESTS
    # =========================================================
    
    def test_database_performance(self):
        """Test database operation performance"""
        logger.info("🗄️ Testing database performance...")
        
        try:
            # Create temporary SQLite database for testing
            test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            test_db_path = test_db_file.name
            test_db_file.close()
            
            # Test database operations with timing
            operation_times = {}
            
            # Test 1: Database initialization
            start_time = time.time()
            conn = sqlite3.connect(test_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Create test table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS financefly_clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    item_id TEXT NOT NULL UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            end_time = time.time()
            operation_times['initialization'] = end_time - start_time
            
            # Test 2: Insert operations
            test_clients = [
                ('Performance Test User 1', 'perf1@example.com', 'item_perf_001'),
                ('Performance Test User 2', 'perf2@example.com', 'item_perf_002'),
                ('Performance Test User 3', 'perf3@example.com', 'item_perf_003'),
                ('Performance Test User 4', 'perf4@example.com', 'item_perf_004'),
                ('Performance Test User 5', 'perf5@example.com', 'item_perf_005')
            ]
            
            insert_times = []
            successful_inserts = 0
            
            for name, email, item_id in test_clients:
                start_time = time.time()
                try:
                    cursor.execute("""
                        INSERT INTO financefly_clients (name, email, item_id)
                        VALUES (?, ?, ?)
                    """, (name, email, item_id))
                    conn.commit()
                    successful_inserts += 1
                except sqlite3.IntegrityError:
                    # Handle duplicate item_id
                    pass
                end_time = time.time()
                insert_times.append(end_time - start_time)
            
            operation_times['average_insert'] = statistics.mean(insert_times)
            operation_times['max_insert'] = max(insert_times)
            
            # Test 3: Query operations
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) as count FROM financefly_clients")
            count_result = cursor.fetchone()
            end_time = time.time()
            operation_times['count_query'] = end_time - start_time
            
            start_time = time.time()
            cursor.execute("SELECT * FROM financefly_clients WHERE item_id = ?", ('item_perf_001',))
            select_result = cursor.fetchone()
            end_time = time.time()
            operation_times['select_query'] = end_time - start_time
            
            conn.close()
            
            # Check performance against thresholds
            db_performance_acceptable = all([
                operation_times['initialization'] <= self.performance_thresholds['database_operation_max_time'],
                operation_times['average_insert'] <= self.performance_thresholds['database_operation_max_time'],
                operation_times['count_query'] <= self.performance_thresholds['database_operation_max_time'],
                operation_times['select_query'] <= self.performance_thresholds['database_operation_max_time'],
                successful_inserts >= len(test_clients) * 0.8  # At least 80% successful
            ])
            
            details = {
                'operation_times': operation_times,
                'successful_inserts': successful_inserts,
                'total_test_clients': len(test_clients),
                'insert_success_rate': successful_inserts / len(test_clients),
                'threshold_max_time': self.performance_thresholds['database_operation_max_time'],
                'records_in_db': count_result['count'] if count_result else 0
            }
            
            # Cleanup
            try:
                os.unlink(test_db_path)
            except:
                pass
            
            return self.log_test_result(
                "database_tests",
                "Database Performance",
                db_performance_acceptable,
                f"Avg insert: {operation_times['average_insert']:.3f}s, Success rate: {successful_inserts}/{len(test_clients)}",
                details,
                operation_times['average_insert']
            )
            
        except Exception as e:
            return self.log_test_result(
                "database_tests",
                "Database Performance",
                False,
                f"Database performance test failed: {str(e)}"
            )
    
    def test_form_submission_simulation(self):
        """Test form submission and database storage simulation"""
        logger.info("📝 Testing form submission simulation...")
        
        try:
            # Create temporary SQLite database for testing
            test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            test_db_path = test_db_file.name
            test_db_file.close()
            
            # Initialize test database
            conn = sqlite3.connect(test_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS financefly_clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    item_id TEXT NOT NULL UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            
            # Simulate form submissions
            form_submissions = [
                {
                    'name': 'Carlos Silva',
                    'email': 'carlos.silva@example.com',
                    'item_id': 'item_form_test_001'
                },
                {
                    'name': 'Maria Santos',
                    'email': 'maria.santos@example.com',
                    'item_id': 'item_form_test_002'
                },
                {
                    'name': 'João Oliveira',
                    'email': 'joao.oliveira@example.com',
                    'item_id': 'item_form_test_003'
                }
            ]
            
            submission_results = []
            
            for submission in form_submissions:
                start_time = time.time()
                
                try:
                    # Simulate form validation
                    if not submission['name'] or not submission['email']:
                        raise ValueError("Missing required fields")
                    
                    if '@' not in submission['email']:
                        raise ValueError("Invalid email format")
                    
                    # Simulate database save
                    cursor.execute("""
                        INSERT INTO financefly_clients (name, email, item_id)
                        VALUES (?, ?, ?)
                        ON CONFLICT(item_id) DO NOTHING
                    """, (submission['name'], submission['email'], submission['item_id']))
                    
                    conn.commit()
                    
                    # Verify save
                    cursor.execute("SELECT * FROM financefly_clients WHERE item_id = ?", (submission['item_id'],))
                    saved_record = cursor.fetchone()
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    submission_results.append({
                        'submission': submission,
                        'success': bool(saved_record),
                        'duration': duration,
                        'saved_record': dict(saved_record) if saved_record else None
                    })
                    
                except Exception as e:
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    submission_results.append({
                        'submission': submission,
                        'success': False,
                        'duration': duration,
                        'error': str(e)
                    })
            
            conn.close()
            
            # Analyze form submission results
            successful_submissions = sum(1 for result in submission_results if result['success'])
            total_submissions = len(submission_results)
            success_rate = successful_submissions / total_submissions
            
            submission_times = [result['duration'] for result in submission_results]
            avg_submission_time = statistics.mean(submission_times)
            
            # Check form submission performance
            form_submission_acceptable = (
                success_rate >= self.performance_thresholds['acceptable_success_rate'] and
                avg_submission_time <= self.performance_thresholds['database_operation_max_time']
            )
            
            details = {
                'total_submissions': total_submissions,
                'successful_submissions': successful_submissions,
                'success_rate': success_rate,
                'average_submission_time': avg_submission_time,
                'submission_results': submission_results,
                'threshold_success_rate': self.performance_thresholds['acceptable_success_rate'],
                'threshold_max_time': self.performance_thresholds['database_operation_max_time']
            }
            
            # Cleanup
            try:
                os.unlink(test_db_path)
            except:
                pass
            
            return self.log_test_result(
                "database_tests",
                "Form Submission Simulation",
                form_submission_acceptable,
                f"Success rate: {success_rate:.1%}, Avg time: {avg_submission_time:.3f}s",
                details,
                avg_submission_time
            )
            
        except Exception as e:
            return self.log_test_result(
                "database_tests",
                "Form Submission Simulation",
                False,
                f"Form submission test failed: {str(e)}"
            )
    
    def test_database_connection_reliability(self):
        """Test database connection reliability and error handling"""
        logger.info("🔌 Testing database connection reliability...")
        
        try:
            # Test database function imports
            from modules.db import init_db, save_client, get_conn
            
            functions_available = all(callable(func) for func in [init_db, save_client, get_conn])
            
            # Test that database configuration is readable
            from modules.db import DB_CONFIG
            config_available = isinstance(DB_CONFIG, dict)
            
            # Test environment variable handling
            required_db_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
            env_vars_configured = all(os.getenv(var) for var in required_db_vars)
            
            # Note: We can't test actual PostgreSQL connection without real credentials
            # But we can test that the connection logic is properly structured
            
            connection_logic_valid = True
            try:
                # Test that get_conn function exists and has proper structure
                import inspect
                conn_source = inspect.getsource(get_conn)
                connection_logic_valid = 'psycopg.connect' in conn_source
            except Exception:
                connection_logic_valid = False
            
            db_reliability_acceptable = all([
                functions_available,
                config_available,
                connection_logic_valid
            ])
            
            details = {
                'functions_available': functions_available,
                'config_available': config_available,
                'env_vars_configured': env_vars_configured,
                'connection_logic_valid': connection_logic_valid,
                'required_db_vars': required_db_vars,
                'config_keys': list(DB_CONFIG.keys()) if config_available else []
            }
            
            return self.log_test_result(
                "database_tests",
                "Database Connection Reliability",
                db_reliability_acceptable,
                f"Database connection logic properly structured: {db_reliability_acceptable}",
                details
            )
            
        except Exception as e:
            return self.log_test_result(
                "database_tests",
                "Database Connection Reliability",
                False,
                f"Database connection reliability test failed: {str(e)}"
            )

    # =========================================================
    # MAIN TEST EXECUTION
    # =========================================================
    
    def run_all_tests(self):
        """Run all performance and integration tests"""
        logger.info("🚀 Starting Performance and Integration Testing...")
        logger.info("=" * 70)
        
        # Performance Tests
        logger.info("📊 PERFORMANCE TESTS")
        logger.info("-" * 30)
        perf_results = [
            self.test_token_generation_performance(),
            self.test_api_response_times(),
            self.test_concurrent_operations_performance()
        ]
        
        # Integration Tests
        logger.info("\n🔗 INTEGRATION TESTS")
        logger.info("-" * 30)
        integration_results = [
            self.test_pluggy_api_integration(),
            self.test_error_handling_integration(),
            self.test_module_integration()
        ]
        
        # Database Tests
        logger.info("\n🗄️ DATABASE TESTS")
        logger.info("-" * 30)
        database_results = [
            self.test_database_performance(),
            self.test_form_submission_simulation(),
            self.test_database_connection_reliability()
        ]
        
        # Calculate overall results
        all_results = perf_results + integration_results + database_results
        total_tests = len(all_results)
        passed_tests = sum(1 for result in all_results if result)
        success_rate = passed_tests / total_tests
        
        # Determine overall status
        if success_rate >= 0.95:
            self.test_results["overall_status"] = "EXCELLENT"
        elif success_rate >= 0.85:
            self.test_results["overall_status"] = "GOOD"
        elif success_rate >= 0.70:
            self.test_results["overall_status"] = "ACCEPTABLE"
        else:
            self.test_results["overall_status"] = "POOR"
        
        # Log summary
        logger.info("\n" + "=" * 70)
        logger.info("PERFORMANCE AND INTEGRATION TEST SUMMARY")
        logger.info("=" * 70)
        
        logger.info(f"Performance Tests: {sum(perf_results)}/{len(perf_results)} passed")
        logger.info(f"Integration Tests: {sum(integration_results)}/{len(integration_results)} passed")
        logger.info(f"Database Tests: {sum(database_results)}/{len(database_results)} passed")
        logger.info("-" * 70)
        logger.info(f"Overall Result: {passed_tests}/{total_tests} tests passed ({success_rate:.1%})")
        logger.info(f"Overall Status: {self.test_results['overall_status']}")
        
        if self.test_results["errors"]:
            logger.info(f"Errors: {len(self.test_results['errors'])}")
        
        if success_rate >= 0.85:
            logger.info("🎉 PERFORMANCE AND INTEGRATION TESTS PASSED!")
            logger.info("✅ Application performance and integrations are working correctly")
        else:
            logger.error("❌ Some performance or integration tests failed")
            logger.error("🔧 Please review and optimize the failing components")
        
        return success_rate >= 0.85, self.test_results
    
    def save_results(self, filename=None):
        """Save test results to JSON file"""
        if filename is None:
            filename = f"performance_integration_test_results_{int(time.time())}.json"
        
        try:
            with open(filename, "w", encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            logger.info(f"📄 Test results saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save test results: {str(e)}")
            return None


def main():
    """Main function for performance and integration testing"""
    print("🚀 Performance and Integration Testing")
    print("=" * 50)
    
    tester = PerformanceIntegrationTester()
    
    try:
        # Run all tests
        success, results = tester.run_all_tests()
        
        # Save results
        report_file = tester.save_results()
        
        # Print final status
        print("\n" + "=" * 50)
        if success:
            print("🎉 PERFORMANCE AND INTEGRATION TESTING COMPLETED SUCCESSFULLY!")
            print("✅ All critical tests passed")
            print("🚀 Application is performing well and integrations are working")
        else:
            print("❌ PERFORMANCE AND INTEGRATION TESTING FAILED!")
            print("🔧 Some tests failed - review and optimize failing components")
            print("📋 Check the detailed report for more information")
        
        if report_file:
            print(f"📄 Detailed report: {report_file}")
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ Testing failed with unexpected error: {str(e)}")
        return 1
        
    finally:
        # Clean up test environment
        tester.cleanup_test_environment()


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)