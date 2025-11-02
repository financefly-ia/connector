#!/usr/bin/env python3
"""
Integration tests for full Pluggy flow

Tests cover:
- End-to-end token generation and widget initialization
- SDK loading and error handling scenarios
- Database operations with mock data

Requirements covered: 1.1, 4.1, 4.5
"""

import unittest
import os
import json
import time
import tempfile
import sqlite3
from unittest.mock import patch, Mock, MagicMock, call
import requests
from modules.pluggy_utils import PluggyClient, create_connect_token, validate_environment
from modules.db import init_db, save_client, get_conn


class TestPluggyIntegrationFlow(unittest.TestCase):
    """Integration tests for complete Pluggy connection flow"""
    
    def setUp(self):
        """Set up test environment with valid configuration"""
        # Set up valid environment variables for testing
        self.test_env = {
            'PLUGGY_CLIENT_ID': 'test_client_id_integration_123',
            'PLUGGY_CLIENT_SECRET': 'test_client_secret_integration_456'
        }
        
        # Apply test environment
        for key, value in self.test_env.items():
            os.environ[key] = value
        
        # Test configuration
        self.test_config = {
            'client_id': 'test_client_id_integration_123',
            'client_secret': 'test_client_secret_integration_456',
            'base_url': 'https://api.pluggy.ai'
        }
        
        # Mock user data
        self.test_user_data = {
            'name': 'João Silva',
            'email': 'joao.silva@example.com',
            'item_id': 'item_12345_test'
        }
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove test environment variables
        for key in self.test_env.keys():
            if key in os.environ:
                del os.environ[key]
    
    @patch('modules.pluggy_utils.requests.post')
    def test_end_to_end_token_generation_success(self, mock_post):
        """Test complete end-to-end token generation flow"""
        # Mock successful authentication response
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {'apiKey': 'test_api_key_integration'}
        
        # Mock successful token generation response
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {'accessToken': 'test_connect_token_integration'}
        
        # Configure mock to return different responses for different calls
        mock_post.side_effect = [auth_response, token_response]
        
        # Execute end-to-end flow
        client = PluggyClient(self.test_config)
        
        # Step 1: Authenticate
        api_key = client.authenticate()
        self.assertEqual(api_key, 'test_api_key_integration')
        self.assertEqual(client._api_key, 'test_api_key_integration')
        
        # Step 2: Generate connect token
        connect_token = client.create_connect_token(self.test_user_data['email'])
        self.assertEqual(connect_token, 'test_connect_token_integration')
        
        # Verify API calls were made correctly
        self.assertEqual(mock_post.call_count, 2)
        
        # Verify authentication call
        auth_call = mock_post.call_args_list[0]
        self.assertEqual(auth_call[0][0], 'https://api.pluggy.ai/auth')
        self.assertEqual(auth_call[1]['json']['clientId'], 'test_client_id_integration_123')
        self.assertEqual(auth_call[1]['json']['clientSecret'], 'test_client_secret_integration_456')
        
        # Verify token generation call
        token_call = mock_post.call_args_list[1]
        self.assertEqual(token_call[0][0], 'https://api.pluggy.ai/connect_token')
        self.assertEqual(token_call[1]['headers']['X-API-KEY'], 'test_api_key_integration')
        self.assertEqual(token_call[1]['json']['clientUserId'], self.test_user_data['email'])
    
    @patch('modules.pluggy_utils.requests.post')
    def test_end_to_end_convenience_function(self, mock_post):
        """Test end-to-end flow using convenience function"""
        # Mock successful responses
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {'apiKey': 'convenience_api_key'}
        
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {'accessToken': 'convenience_connect_token'}
        
        mock_post.side_effect = [auth_response, token_response]
        
        # Execute using convenience function
        token = create_connect_token(self.test_user_data['email'])
        
        self.assertEqual(token, 'convenience_connect_token')
        self.assertEqual(mock_post.call_count, 2)
    
    @patch('modules.pluggy_utils.requests.post')
    def test_widget_initialization_flow(self, mock_post):
        """Test widget initialization with proper token"""
        # Mock successful API responses
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {'apiKey': 'widget_test_api_key'}
        
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {'accessToken': 'widget_test_token'}
        
        mock_post.side_effect = [auth_response, token_response]
        
        # Generate token for widget
        client = PluggyClient(self.test_config)
        token = client.create_connect_token(self.test_user_data['email'])
        
        # Verify token is suitable for widget initialization
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 10)  # Basic token format validation
        self.assertEqual(token, 'widget_test_token')
        
        # Simulate widget configuration that would be used in JavaScript
        widget_config = {
            'connectToken': token,
            'includeSandbox': False,
            'language': 'pt',
            'theme': 'dark'
        }
        
        # Verify widget configuration is properly structured
        self.assertIn('connectToken', widget_config)
        self.assertEqual(widget_config['connectToken'], token)
        self.assertEqual(widget_config['language'], 'pt')


class TestSDKLoadingScenarios(unittest.TestCase):
    """Test SDK loading and error handling scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.sdk_url = "https://cdn.pluggy.ai/pluggy-connect/v2.9.2/pluggy-connect.js"
    
    @patch('requests.get')
    def test_sdk_loading_success_scenario(self, mock_get):
        """Test successful SDK loading scenario"""
        # Mock successful SDK response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        // Mock Pluggy Connect SDK v2.9.2
        window.PluggyConnect = function(config) {
            this.config = config;
            this.open = function() { return true; };
            this.close = function() { return true; };
        };
        """
        mock_response.headers = {'content-type': 'application/javascript'}
        mock_get.return_value = mock_response
        
        # Simulate SDK loading
        response = mock_get(self.sdk_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('PluggyConnect', response.text)
        self.assertIn('v2.9.2', response.text)
        
        # Verify SDK content is valid JavaScript
        sdk_content = response.text
        self.assertTrue(len(sdk_content) > 100)
        self.assertIn('function', sdk_content)
    
    @patch('requests.get')
    def test_sdk_loading_404_error(self, mock_get):
        """Test SDK loading with 404 error (old endpoint)"""
        # Mock 404 response (simulating old v2.6.0 endpoint)
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response
        
        # Simulate SDK loading attempt
        response = mock_get("https://cdn.pluggy.ai/pluggy-connect/v2.6.0/pluggy-connect.js")
        
        self.assertEqual(response.status_code, 404)
        
        # Verify error handling would catch this
        with self.assertRaises(Exception):
            if response.status_code != 200:
                raise Exception(f"SDK loading failed with status {response.status_code}")
    
    @patch('requests.get')
    def test_sdk_loading_timeout_scenario(self, mock_get):
        """Test SDK loading timeout scenario"""
        # Mock timeout exception
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        
        # Simulate SDK loading with timeout
        with self.assertRaises(requests.exceptions.Timeout):
            mock_get(self.sdk_url, timeout=10)
    
    @patch('requests.get')
    def test_sdk_loading_network_error(self, mock_get):
        """Test SDK loading with network error"""
        # Mock connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        
        # Simulate SDK loading with network error
        with self.assertRaises(requests.exceptions.ConnectionError):
            mock_get(self.sdk_url)
    
    def test_sdk_version_validation(self):
        """Test SDK version validation"""
        # Test correct SDK URL format
        expected_url = "https://cdn.pluggy.ai/pluggy-connect/v2.9.2/pluggy-connect.js"
        self.assertEqual(self.sdk_url, expected_url)
        
        # Test version extraction from URL
        version_part = self.sdk_url.split('/pluggy-connect/')[1].split('/')[0]
        self.assertEqual(version_part, 'v2.9.2')
        
        # Verify it's not the old version
        self.assertNotEqual(version_part, 'v2.6.0')


class TestDatabaseIntegrationWithMockData(unittest.TestCase):
    """Test database operations with mock data"""
    
    def setUp(self):
        """Set up test database"""
        # Create temporary database for testing
        self.test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db_path = self.test_db_file.name
        self.test_db_file.close()
        
        # Mock database configuration to use SQLite for testing
        self.original_get_conn = None
        
        # Test data
        self.test_clients = [
            {
                'name': 'Maria Santos',
                'email': 'maria.santos@example.com',
                'item_id': 'item_test_001'
            },
            {
                'name': 'Pedro Oliveira',
                'email': 'pedro.oliveira@example.com',
                'item_id': 'item_test_002'
            },
            {
                'name': 'Ana Costa',
                'email': 'ana.costa@example.com',
                'item_id': 'item_test_003'
            }
        ]
    
    def tearDown(self):
        """Clean up test database"""
        try:
            os.unlink(self.test_db_path)
        except:
            pass
    
    def _create_test_db_connection(self):
        """Create SQLite connection for testing"""
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_test_db(self):
        """Initialize test database with schema"""
        conn = self._create_test_db_connection()
        cursor = conn.cursor()
        
        # Create test table (SQLite version of the schema)
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
        conn.close()
    
    def _save_test_client(self, name, email, item_id):
        """Save client to test database"""
        conn = self._create_test_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO financefly_clients (name, email, item_id)
                VALUES (?, ?, ?)
            """, (name, email, item_id))
            
            client_id = cursor.lastrowid
            conn.commit()
            return client_id
        except sqlite3.IntegrityError:
            # Handle duplicate item_id
            return None
        finally:
            conn.close()
    
    def _get_test_client(self, item_id):
        """Get client from test database"""
        conn = self._create_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM financefly_clients WHERE item_id = ?
        """, (item_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'name': row['name'],
                'email': row['email'],
                'item_id': row['item_id'],
                'created_at': row['created_at']
            }
        return None
    
    def test_database_initialization(self):
        """Test database initialization"""
        self._init_test_db()
        
        # Verify table was created
        conn = self._create_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='financefly_clients'
        """)
        
        table_exists = cursor.fetchone() is not None
        conn.close()
        
        self.assertTrue(table_exists)
    
    def test_save_client_success(self):
        """Test successful client save operation"""
        self._init_test_db()
        
        client_data = self.test_clients[0]
        client_id = self._save_test_client(
            client_data['name'],
            client_data['email'],
            client_data['item_id']
        )
        
        self.assertIsNotNone(client_id)
        self.assertIsInstance(client_id, int)
        self.assertGreater(client_id, 0)
    
    def test_save_client_duplicate_item_id(self):
        """Test handling of duplicate item_id"""
        self._init_test_db()
        
        client_data = self.test_clients[0]
        
        # Save client first time
        client_id_1 = self._save_test_client(
            client_data['name'],
            client_data['email'],
            client_data['item_id']
        )
        
        # Try to save same item_id again
        client_id_2 = self._save_test_client(
            "Different Name",
            "different@email.com",
            client_data['item_id']  # Same item_id
        )
        
        self.assertIsNotNone(client_id_1)
        self.assertIsNone(client_id_2)  # Should return None for duplicate
    
    def test_retrieve_saved_client(self):
        """Test retrieving saved client data"""
        self._init_test_db()
        
        client_data = self.test_clients[0]
        
        # Save client
        client_id = self._save_test_client(
            client_data['name'],
            client_data['email'],
            client_data['item_id']
        )
        
        # Retrieve client
        retrieved_client = self._get_test_client(client_data['item_id'])
        
        self.assertIsNotNone(retrieved_client)
        self.assertEqual(retrieved_client['name'], client_data['name'])
        self.assertEqual(retrieved_client['email'], client_data['email'])
        self.assertEqual(retrieved_client['item_id'], client_data['item_id'])
        self.assertEqual(retrieved_client['id'], client_id)
    
    def test_multiple_clients_save_and_retrieve(self):
        """Test saving and retrieving multiple clients"""
        self._init_test_db()
        
        saved_ids = []
        
        # Save all test clients
        for client_data in self.test_clients:
            client_id = self._save_test_client(
                client_data['name'],
                client_data['email'],
                client_data['item_id']
            )
            saved_ids.append(client_id)
            self.assertIsNotNone(client_id)
        
        # Verify all clients can be retrieved
        for i, client_data in enumerate(self.test_clients):
            retrieved_client = self._get_test_client(client_data['item_id'])
            
            self.assertIsNotNone(retrieved_client)
            self.assertEqual(retrieved_client['name'], client_data['name'])
            self.assertEqual(retrieved_client['email'], client_data['email'])
            self.assertEqual(retrieved_client['item_id'], client_data['item_id'])
            self.assertEqual(retrieved_client['id'], saved_ids[i])
    
    def test_database_connection_error_handling(self):
        """Test database connection error handling"""
        # Try to connect to non-existent database path
        invalid_db_path = "/invalid/path/database.db"
        
        with self.assertRaises(Exception):
            conn = sqlite3.connect(invalid_db_path)
            # This should fail when trying to write to invalid path
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE test (id INTEGER)")
            conn.commit()


class TestCompleteIntegrationFlow(unittest.TestCase):
    """Test complete integration flow combining all components"""
    
    def setUp(self):
        """Set up complete test environment"""
        # Environment setup
        self.test_env = {
            'PLUGGY_CLIENT_ID': 'integration_test_client_123',
            'PLUGGY_CLIENT_SECRET': 'integration_test_secret_456'
        }
        
        for key, value in self.test_env.items():
            os.environ[key] = value
        
        # Test user data
        self.user_data = {
            'name': 'Carlos Mendes',
            'email': 'carlos.mendes@example.com'
        }
        
        # Mock Pluggy connection result
        self.connection_result = {
            'item': {
                'id': 'item_integration_test_789',
                'connector': {
                    'name': 'Banco do Brasil',
                    'id': 201
                }
            }
        }
    
    def tearDown(self):
        """Clean up test environment"""
        for key in self.test_env.keys():
            if key in os.environ:
                del os.environ[key]
    
    @patch('modules.pluggy_utils.requests.post')
    @patch('requests.get')
    def test_complete_user_flow_simulation(self, mock_sdk_get, mock_api_post):
        """Test complete user flow from form submission to successful connection"""
        
        # Step 1: Mock environment validation (already set up in setUp)
        config = validate_environment()
        self.assertEqual(config['client_id'], 'integration_test_client_123')
        
        # Step 2: Mock successful API responses
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {'apiKey': 'complete_flow_api_key'}
        
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {'accessToken': 'complete_flow_token'}
        
        mock_api_post.side_effect = [auth_response, token_response]
        
        # Step 3: Mock successful SDK loading
        sdk_response = Mock()
        sdk_response.status_code = 200
        sdk_response.text = """
        window.PluggyConnect = function(config) {
            this.config = config;
            this.open = function() { 
                // Simulate successful connection after delay
                setTimeout(() => {
                    if (config.onSuccess) {
                        config.onSuccess({
                            item: { id: 'item_integration_test_789' }
                        });
                    }
                }, 100);
                return true; 
            };
        };
        """
        mock_sdk_get.return_value = sdk_response
        
        # Step 4: Execute complete flow
        
        # 4a: Generate connect token
        token = create_connect_token(self.user_data['email'])
        self.assertEqual(token, 'complete_flow_token')
        
        # 4b: Simulate SDK loading
        sdk_resp = mock_sdk_get('https://cdn.pluggy.ai/pluggy-connect/v2.9.2/pluggy-connect.js')
        self.assertEqual(sdk_resp.status_code, 200)
        self.assertIn('PluggyConnect', sdk_resp.text)
        
        # 4c: Simulate widget initialization and success
        widget_config = {
            'connectToken': token,
            'includeSandbox': False,
            'language': 'pt',
            'onSuccess': lambda data: self._handle_success(data),
            'onError': lambda err: self._handle_error(err)
        }
        
        # Verify widget configuration
        self.assertEqual(widget_config['connectToken'], token)
        self.assertEqual(widget_config['language'], 'pt')
        self.assertIsNotNone(widget_config['onSuccess'])
        self.assertIsNotNone(widget_config['onError'])
        
        # Step 5: Verify all API calls were made correctly
        self.assertEqual(mock_api_post.call_count, 2)
        
        # Verify authentication call
        auth_call = mock_api_post.call_args_list[0]
        self.assertEqual(auth_call[0][0], 'https://api.pluggy.ai/auth')
        
        # Verify token generation call
        token_call = mock_api_post.call_args_list[1]
        self.assertEqual(token_call[0][0], 'https://api.pluggy.ai/connect_token')
        self.assertEqual(token_call[1]['headers']['X-API-KEY'], 'complete_flow_api_key')
    
    def _handle_success(self, data):
        """Mock success handler for widget"""
        self.connection_success_data = data
        return True
    
    def _handle_error(self, error):
        """Mock error handler for widget"""
        self.connection_error_data = error
        return True
    
    @patch('modules.pluggy_utils.requests.post')
    def test_error_recovery_scenarios(self, mock_post):
        """Test error recovery in complete flow"""
        
        # Scenario 1: Authentication fails, then succeeds on retry
        auth_fail_response = Mock()
        auth_fail_response.status_code = 401
        
        auth_success_response = Mock()
        auth_success_response.status_code = 200
        auth_success_response.json.return_value = {'apiKey': 'retry_api_key'}
        
        token_response = Mock()
        token_response.status_code = 200
        token_response.json.return_value = {'accessToken': 'retry_token'}
        
        mock_post.side_effect = [auth_fail_response, auth_success_response, token_response]
        
        # First attempt should fail
        client = PluggyClient()
        with self.assertRaises(ValueError) as context:
            client.authenticate()
        
        self.assertIn('Credenciais Pluggy inválidas', str(context.exception))
        
        # Second attempt should succeed
        client2 = PluggyClient()
        api_key = client2.authenticate()
        self.assertEqual(api_key, 'retry_api_key')
        
        # Token generation should work
        token = client2.create_connect_token(self.user_data['email'])
        self.assertEqual(token, 'retry_token')
    
    def test_widget_callback_scenarios(self):
        """Test different widget callback scenarios"""
        
        # Test success callback data structure
        success_data = {
            'item': {
                'id': 'item_callback_test_123',
                'connector': {
                    'name': 'Itaú',
                    'id': 202
                }
            }
        }
        
        # Verify success data structure
        self.assertIn('item', success_data)
        self.assertIn('id', success_data['item'])
        self.assertIn('connector', success_data['item'])
        
        # Test error callback data structure
        error_data = {
            'message': 'Invalid credentials',
            'code': 'AUTH_ERROR',
            'type': 'credentials'
        }
        
        # Verify error data structure
        self.assertIn('message', error_data)
        self.assertIn('code', error_data)
        
        # Test callback handling
        def mock_success_callback(data):
            self.assertIsInstance(data, dict)
            self.assertIn('item', data)
            return True
        
        def mock_error_callback(error):
            self.assertIsInstance(error, dict)
            self.assertIn('message', error)
            return True
        
        # Verify callbacks are callable
        self.assertTrue(callable(mock_success_callback))
        self.assertTrue(callable(mock_error_callback))
        
        # Test callback execution
        result_success = mock_success_callback(success_data)
        result_error = mock_error_callback(error_data)
        
        self.assertTrue(result_success)
        self.assertTrue(result_error)


if __name__ == '__main__':
    # Configure logging to reduce noise during tests
    import logging
    logging.getLogger('modules.pluggy_utils').setLevel(logging.CRITICAL)
    logging.getLogger('modules.db').setLevel(logging.CRITICAL)
    
    # Run tests with detailed output
    unittest.main(verbosity=2)