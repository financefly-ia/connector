#!/usr/bin/env python3
"""
Unit tests for modules/pluggy_utils.py

Tests cover:
- Environment validation functions
- PluggyClient authentication and token generation methods  
- Error handling scenarios and edge cases

Requirements covered: 3.1, 3.4, 4.1
"""

import unittest
import os
import json
from unittest.mock import patch, Mock, MagicMock
import requests
from modules.pluggy_utils import (
    validate_environment, 
    get_pluggy_config, 
    PluggyClient, 
    create_connect_token
)


class TestEnvironmentValidation(unittest.TestCase):
    """Test environment validation functions"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear environment variables before each test
        for var in ['PLUGGY_CLIENT_ID', 'PLUGGY_CLIENT_SECRET']:
            if var in os.environ:
                del os.environ[var]
    
    def tearDown(self):
        """Clean up after each test"""
        # Clear environment variables after each test
        for var in ['PLUGGY_CLIENT_ID', 'PLUGGY_CLIENT_SECRET']:
            if var in os.environ:
                del os.environ[var]
    
    @patch('modules.pluggy_utils.load_dotenv')
    def test_validate_environment_success(self, mock_load_dotenv):
        """Test successful environment validation"""
        # Set valid environment variables
        os.environ['PLUGGY_CLIENT_ID'] = 'valid_client_id_123'
        os.environ['PLUGGY_CLIENT_SECRET'] = 'valid_client_secret_456'
        
        config = validate_environment()
        
        self.assertIsInstance(config, dict)
        self.assertEqual(config['client_id'], 'valid_client_id_123')
        self.assertEqual(config['client_secret'], 'valid_client_secret_456')
        self.assertEqual(config['base_url'], 'https://api.pluggy.ai')
        mock_load_dotenv.assert_called_once()
    
    @patch('modules.pluggy_utils.load_dotenv')
    def test_validate_environment_missing_client_id(self, mock_load_dotenv):
        """Test validation failure when PLUGGY_CLIENT_ID is missing"""
        os.environ['PLUGGY_CLIENT_SECRET'] = 'valid_client_secret_456'
        
        with self.assertRaises(ValueError) as context:
            validate_environment()
        
        errors = context.exception.args[0]
        self.assertIsInstance(errors, list)
        self.assertIn('PLUGGY_CLIENT_ID não está definido', errors)
    
    @patch('modules.pluggy_utils.load_dotenv')
    def test_validate_environment_missing_client_secret(self, mock_load_dotenv):
        """Test validation failure when PLUGGY_CLIENT_SECRET is missing"""
        os.environ['PLUGGY_CLIENT_ID'] = 'valid_client_id_123'
        
        with self.assertRaises(ValueError) as context:
            validate_environment()
        
        errors = context.exception.args[0]
        self.assertIsInstance(errors, list)
        self.assertIn('PLUGGY_CLIENT_SECRET não está definido', errors)
    
    @patch('modules.pluggy_utils.load_dotenv')
    def test_validate_environment_empty_values(self, mock_load_dotenv):
        """Test validation failure when environment variables are empty"""
        os.environ['PLUGGY_CLIENT_ID'] = '   '  # Empty/whitespace
        os.environ['PLUGGY_CLIENT_SECRET'] = ''  # Empty
        
        with self.assertRaises(ValueError) as context:
            validate_environment()
        
        errors = context.exception.args[0]
        self.assertIsInstance(errors, list)
        self.assertIn('PLUGGY_CLIENT_ID está vazio', errors)
        # Empty string is caught by "not client_secret" check first
        self.assertIn('PLUGGY_CLIENT_SECRET não está definido', errors)
    
    @patch('modules.pluggy_utils.load_dotenv')
    def test_validate_environment_whitespace_values(self, mock_load_dotenv):
        """Test validation failure when environment variables are whitespace-only"""
        os.environ['PLUGGY_CLIENT_ID'] = '   '  # Whitespace only
        os.environ['PLUGGY_CLIENT_SECRET'] = '  \t  '  # Whitespace and tabs
        
        with self.assertRaises(ValueError) as context:
            validate_environment()
        
        errors = context.exception.args[0]
        self.assertIsInstance(errors, list)
        self.assertIn('PLUGGY_CLIENT_ID está vazio', errors)
        self.assertIn('PLUGGY_CLIENT_SECRET está vazio', errors)
    
    @patch('modules.pluggy_utils.load_dotenv')
    def test_validate_environment_short_values(self, mock_load_dotenv):
        """Test validation failure when environment variables are too short"""
        os.environ['PLUGGY_CLIENT_ID'] = 'short'  # Less than 10 chars
        os.environ['PLUGGY_CLIENT_SECRET'] = 'tiny'  # Less than 10 chars
        
        with self.assertRaises(ValueError) as context:
            validate_environment()
        
        errors = context.exception.args[0]
        self.assertIsInstance(errors, list)
        self.assertIn('PLUGGY_CLIENT_ID parece inválido (muito curto)', errors)
        self.assertIn('PLUGGY_CLIENT_SECRET parece inválido (muito curto)', errors)
    
    @patch('modules.pluggy_utils.load_dotenv')
    def test_validate_environment_multiple_errors(self, mock_load_dotenv):
        """Test validation with multiple errors"""
        # Don't set any environment variables
        
        with self.assertRaises(ValueError) as context:
            validate_environment()
        
        errors = context.exception.args[0]
        self.assertIsInstance(errors, list)
        self.assertEqual(len(errors), 2)  # Both client_id and client_secret missing
    
    @patch('modules.pluggy_utils.load_dotenv')
    @patch('modules.pluggy_utils.os.getenv')
    def test_validate_environment_unexpected_error(self, mock_getenv, mock_load_dotenv):
        """Test handling of unexpected errors during validation"""
        mock_getenv.side_effect = Exception("Unexpected error")
        
        with self.assertRaises(ValueError) as context:
            validate_environment()
        
        errors = context.exception.args[0]
        self.assertIsInstance(errors, list)
        self.assertIn('Erro ao validar configuração do ambiente.', errors)
    
    def test_get_pluggy_config(self):
        """Test get_pluggy_config convenience function"""
        with patch('modules.pluggy_utils.validate_environment') as mock_validate:
            expected_config = {
                'client_id': 'test_id',
                'client_secret': 'test_secret',
                'base_url': 'https://api.pluggy.ai'
            }
            mock_validate.return_value = expected_config
            
            config = get_pluggy_config()
            
            self.assertEqual(config, expected_config)
            mock_validate.assert_called_once()


class TestPluggyClient(unittest.TestCase):
    """Test PluggyClient class"""
    
    def setUp(self):
        """Set up test client"""
        self.test_config = {
            'client_id': 'test_client_id_123',
            'client_secret': 'test_client_secret_456',
            'base_url': 'https://api.pluggy.ai'
        }
        self.client = PluggyClient(self.test_config)
    
    def test_client_initialization_with_config(self):
        """Test PluggyClient initialization with provided config"""
        self.assertEqual(self.client.client_id, 'test_client_id_123')
        self.assertEqual(self.client.client_secret, 'test_client_secret_456')
        self.assertEqual(self.client.base_url, 'https://api.pluggy.ai')
        self.assertIsNone(self.client._api_key)
    
    @patch('modules.pluggy_utils.validate_environment')
    def test_client_initialization_without_config(self, mock_validate):
        """Test PluggyClient initialization without config (auto-validation)"""
        mock_validate.return_value = self.test_config
        
        client = PluggyClient()
        
        self.assertEqual(client.client_id, 'test_client_id_123')
        mock_validate.assert_called_once()
    
    @patch('modules.pluggy_utils.requests.post')
    def test_authenticate_success(self, mock_post):
        """Test successful authentication"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'apiKey': 'test_api_key_789'}
        mock_post.return_value = mock_response
        
        api_key = self.client.authenticate()
        
        self.assertEqual(api_key, 'test_api_key_789')
        self.assertEqual(self.client._api_key, 'test_api_key_789')
        
        # Verify request was made correctly
        mock_post.assert_called_once_with(
            'https://api.pluggy.ai/auth',
            headers={'accept': 'application/json', 'content-type': 'application/json'},
            json={'clientId': 'test_client_id_123', 'clientSecret': 'test_client_secret_456'},
            timeout=15
        )
    
    @patch('modules.pluggy_utils.requests.post')
    def test_authenticate_invalid_credentials(self, mock_post):
        """Test authentication with invalid credentials (401)"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            self.client.authenticate()
        
        self.assertIn('Credenciais Pluggy inválidas', str(context.exception))
    
    @patch('modules.pluggy_utils.requests.post')
    def test_authenticate_forbidden(self, mock_post):
        """Test authentication with forbidden access (403)"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            self.client.authenticate()
        
        self.assertIn('Acesso negado pelo serviço Pluggy', str(context.exception))
    
    @patch('modules.pluggy_utils.requests.post')
    def test_authenticate_rate_limit(self, mock_post):
        """Test authentication with rate limit (429)"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            self.client.authenticate()
        
        self.assertIn('Muitas tentativas de conexão', str(context.exception))
    
    @patch('modules.pluggy_utils.requests.post')
    def test_authenticate_server_error(self, mock_post):
        """Test authentication with server error (500+)"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            self.client.authenticate()
        
        self.assertIn('Serviço Pluggy temporariamente indisponível', str(context.exception))
    
    @patch('modules.pluggy_utils.requests.post')
    def test_authenticate_invalid_json_response(self, mock_post):
        """Test authentication with invalid JSON response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            self.client.authenticate()
        
        self.assertIn('Resposta inválida do serviço Pluggy', str(context.exception))
    
    @patch('modules.pluggy_utils.requests.post')
    def test_authenticate_missing_api_key(self, mock_post):
        """Test authentication with missing API key in response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # No apiKey field
        mock_post.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            self.client.authenticate()
        
        self.assertIn('API key não recebida', str(context.exception))
    
    @patch('modules.pluggy_utils.requests.post')
    def test_authenticate_timeout_error(self, mock_post):
        """Test authentication with timeout error"""
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        with self.assertRaises(ValueError) as context:
            self.client.authenticate()
        
        self.assertIn('Timeout ao conectar com o serviço Pluggy', str(context.exception))
    
    @patch('modules.pluggy_utils.requests.post')
    def test_authenticate_connection_error(self, mock_post):
        """Test authentication with connection error"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with self.assertRaises(ValueError) as context:
            self.client.authenticate()
        
        self.assertIn('Erro de conexão com o serviço Pluggy', str(context.exception))
    
    @patch('modules.pluggy_utils.requests.post')
    def test_create_connect_token_success(self, mock_post):
        """Test successful connect token creation"""
        # Set up authenticated client
        self.client._api_key = 'test_api_key_789'
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'accessToken': 'test_access_token_abc'}
        mock_post.return_value = mock_response
        
        token = self.client.create_connect_token('test_user@example.com')
        
        self.assertEqual(token, 'test_access_token_abc')
        
        # Verify request was made correctly
        mock_post.assert_called_once_with(
            'https://api.pluggy.ai/connect_token',
            headers={
                'accept': 'application/json',
                'content-type': 'application/json',
                'X-API-KEY': 'test_api_key_789'
            },
            json={'clientUserId': 'test_user@example.com'},
            timeout=15
        )
    
    @patch('modules.pluggy_utils.requests.post')
    def test_create_connect_token_without_user_id(self, mock_post):
        """Test connect token creation without user ID"""
        # Set up authenticated client
        self.client._api_key = 'test_api_key_789'
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'accessToken': 'test_access_token_abc'}
        mock_post.return_value = mock_response
        
        token = self.client.create_connect_token()
        
        self.assertEqual(token, 'test_access_token_abc')
        
        # Verify request was made with empty payload
        mock_post.assert_called_once_with(
            'https://api.pluggy.ai/connect_token',
            headers={
                'accept': 'application/json',
                'content-type': 'application/json',
                'X-API-KEY': 'test_api_key_789'
            },
            json={},
            timeout=15
        )
    
    @patch.object(PluggyClient, 'authenticate')
    @patch('modules.pluggy_utils.requests.post')
    def test_create_connect_token_auto_authenticate(self, mock_post, mock_authenticate):
        """Test connect token creation with automatic authentication"""
        # Client has no API key initially
        self.client._api_key = None
        mock_authenticate.return_value = 'auto_generated_key'
        
        # Mock successful token response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'accessToken': 'test_access_token_abc'}
        mock_post.return_value = mock_response
        
        token = self.client.create_connect_token('test_user@example.com')
        
        self.assertEqual(token, 'test_access_token_abc')
        mock_authenticate.assert_called_once()
    
    @patch('modules.pluggy_utils.requests.post')
    def test_create_connect_token_unauthorized(self, mock_post):
        """Test connect token creation with unauthorized error (401)"""
        self.client._api_key = 'invalid_api_key'
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            self.client.create_connect_token()
        
        self.assertIn('Erro de autorização ao gerar token', str(context.exception))
    
    @patch('modules.pluggy_utils.requests.post')
    def test_create_connect_token_bad_request(self, mock_post):
        """Test connect token creation with bad request (400)"""
        self.client._api_key = 'test_api_key_789'
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'Invalid request data'
        mock_post.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            self.client.create_connect_token()
        
        self.assertIn('Dados inválidos para geração do token', str(context.exception))
    
    @patch('modules.pluggy_utils.requests.post')
    def test_create_connect_token_missing_access_token(self, mock_post):
        """Test connect token creation with missing access token in response"""
        self.client._api_key = 'test_api_key_789'
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # No accessToken field
        mock_post.return_value = mock_response
        
        with self.assertRaises(ValueError) as context:
            self.client.create_connect_token()
        
        self.assertIn('token não recebido', str(context.exception))


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""
    
    @patch.object(PluggyClient, 'create_connect_token')
    @patch.object(PluggyClient, '__init__')
    def test_create_connect_token_function(self, mock_init, mock_create_token):
        """Test create_connect_token convenience function"""
        # Mock PluggyClient initialization
        mock_init.return_value = None
        mock_create_token.return_value = 'test_token_xyz'
        
        token = create_connect_token('test_user@example.com')
        
        self.assertEqual(token, 'test_token_xyz')
        mock_init.assert_called_once_with()
        mock_create_token.assert_called_once_with('test_user@example.com')


class TestErrorHandlingEdgeCases(unittest.TestCase):
    """Test error handling edge cases"""
    
    def setUp(self):
        """Set up test client"""
        self.test_config = {
            'client_id': 'test_client_id_123',
            'client_secret': 'test_client_secret_456',
            'base_url': 'https://api.pluggy.ai'
        }
        self.client = PluggyClient(self.test_config)
    
    @patch('modules.pluggy_utils.requests.post')
    def test_authenticate_unexpected_exception(self, mock_post):
        """Test authentication with unexpected exception"""
        mock_post.side_effect = Exception("Unexpected error")
        
        with self.assertRaises(ValueError) as context:
            self.client.authenticate()
        
        self.assertIn('Erro interno ao autenticar com Pluggy', str(context.exception))
    
    @patch('modules.pluggy_utils.requests.post')
    def test_create_connect_token_unexpected_exception(self, mock_post):
        """Test connect token creation with unexpected exception"""
        self.client._api_key = 'test_api_key_789'
        mock_post.side_effect = Exception("Unexpected error")
        
        with self.assertRaises(ValueError) as context:
            self.client.create_connect_token()
        
        self.assertIn('Erro interno ao gerar token de conexão', str(context.exception))
    
    @patch('modules.pluggy_utils.requests.post')
    def test_authenticate_http_error(self, mock_post):
        """Test authentication with HTTP error"""
        mock_post.side_effect = requests.exceptions.HTTPError("HTTP error")
        
        with self.assertRaises(ValueError) as context:
            self.client.authenticate()
        
        self.assertIn('Erro HTTP ao comunicar com o serviço Pluggy', str(context.exception))
    
    @patch('modules.pluggy_utils.requests.post')
    def test_create_connect_token_request_exception(self, mock_post):
        """Test connect token creation with general request exception"""
        self.client._api_key = 'test_api_key_789'
        mock_post.side_effect = requests.exceptions.RequestException("Request error")
        
        with self.assertRaises(ValueError) as context:
            self.client.create_connect_token()
        
        self.assertIn('Erro ao comunicar com o serviço Pluggy', str(context.exception))


if __name__ == '__main__':
    # Configure logging to reduce noise during tests
    import logging
    logging.getLogger('modules.pluggy_utils').setLevel(logging.CRITICAL)
    
    # Run tests
    unittest.main(verbosity=2)