# modules/pluggy_utils.py
import os
import requests
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# =========================================================
# ENVIRONMENT VALIDATION
# =========================================================
def validate_environment():
    """
    Validates required environment variables for Pluggy integration.
    Returns configuration dict if valid, otherwise raises ValueError with user-friendly message.
    """
    try:
        logger.info("Starting environment validation")
        load_dotenv()
        
        errors = []
        
        # Check PLUGGY_CLIENT_ID
        client_id = os.getenv("PLUGGY_CLIENT_ID")
        if not client_id:
            errors.append("PLUGGY_CLIENT_ID não está definido")
            logger.error("PLUGGY_CLIENT_ID environment variable is not set")
        elif not client_id.strip():
            errors.append("PLUGGY_CLIENT_ID está vazio")
            logger.error("PLUGGY_CLIENT_ID environment variable is empty")
        elif len(client_id.strip()) < 10:  # Basic format validation
            errors.append("PLUGGY_CLIENT_ID parece inválido (muito curto)")
            logger.error(f"PLUGGY_CLIENT_ID appears invalid (length: {len(client_id.strip())})")
        
        # Check PLUGGY_CLIENT_SECRET
        client_secret = os.getenv("PLUGGY_CLIENT_SECRET")
        if not client_secret:
            errors.append("PLUGGY_CLIENT_SECRET não está definido")
            logger.error("PLUGGY_CLIENT_SECRET environment variable is not set")
        elif not client_secret.strip():
            errors.append("PLUGGY_CLIENT_SECRET está vazio")
            logger.error("PLUGGY_CLIENT_SECRET environment variable is empty")
        elif len(client_secret.strip()) < 10:  # Basic format validation
            errors.append("PLUGGY_CLIENT_SECRET parece inválido (muito curto)")
            logger.error(f"PLUGGY_CLIENT_SECRET appears invalid (length: {len(client_secret.strip())})")
        
        if errors:
            logger.error(f"Environment validation failed with {len(errors)} errors")
            raise ValueError(errors)
        
        logger.info("Environment validation successful")
        return {
            "client_id": client_id.strip(),
            "client_secret": client_secret.strip(),
            "base_url": "https://api.pluggy.ai"
        }
        
    except ValueError:
        # Re-raise ValueError exceptions (these contain validation errors)
        raise
    except Exception as env_error:
        logger.error(f"Unexpected error during environment validation: {env_error}", exc_info=True)
        raise ValueError(["Erro ao validar configuração do ambiente."])

def get_pluggy_config():
    """
    Returns validated Pluggy configuration.
    Convenience wrapper around validate_environment().
    """
    return validate_environment()

# =========================================================
# PLUGGY API CLIENT
# =========================================================
class PluggyClient:
    """
    Client for interacting with Pluggy API.
    Handles authentication and connect token generation.
    """
    
    def __init__(self, config=None):
        """
        Initialize PluggyClient with configuration.
        
        Args:
            config (dict, optional): Configuration dict with client_id, client_secret, base_url
                                   If None, will validate environment automatically
        """
        if config is None:
            config = validate_environment()
        
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.base_url = config["base_url"]
        self._api_key = None
    
    def authenticate(self):
        """
        Authenticates with Pluggy API and returns API key.
        
        Returns:
            str: API key for subsequent requests
            
        Raises:
            ValueError: User-friendly error messages for various failure scenarios
        """
        try:
            logger.info("Starting Pluggy API authentication")
            
            auth_url = f"{self.base_url}/auth"
            auth_payload = {
                "clientId": self.client_id, 
                "clientSecret": self.client_secret
            }
            
            logger.debug(f"Authenticating with Pluggy API at {auth_url}")
            auth_resp = requests.post(
                auth_url,
                headers={"accept": "application/json", "content-type": "application/json"},
                json=auth_payload,
                timeout=15
            )

            # Handle authentication errors with specific logging
            if auth_resp.status_code == 401:
                logger.error("Pluggy authentication failed: Invalid credentials")
                raise ValueError("Credenciais Pluggy inválidas. Verifique a configuração.")
            elif auth_resp.status_code == 403:
                logger.error("Pluggy authentication failed: Access forbidden")
                raise ValueError("Acesso negado pelo serviço Pluggy. Verifique suas permissões.")
            elif auth_resp.status_code == 429:
                logger.error("Pluggy authentication failed: Rate limit exceeded")
                raise ValueError("Muitas tentativas de conexão. Aguarde alguns minutos e tente novamente.")
            elif auth_resp.status_code >= 500:
                logger.error(f"Pluggy server error during auth: {auth_resp.status_code}")
                raise ValueError("Serviço Pluggy temporariamente indisponível. Tente novamente em alguns minutos.")
            elif auth_resp.status_code != 200:
                logger.error(f"Pluggy authentication failed with status {auth_resp.status_code}: {auth_resp.text}")
                raise ValueError(f"Erro de autenticação Pluggy (código {auth_resp.status_code})")

            # Parse authentication response
            try:
                auth_data = auth_resp.json()
                api_key = auth_data.get("apiKey")
            except ValueError as json_error:
                logger.error(f"Invalid JSON response from Pluggy auth: {json_error}")
                raise ValueError("Resposta inválida do serviço Pluggy. Tente novamente.")
            
            if not api_key:
                logger.error("No API key received from Pluggy authentication")
                raise ValueError("Falha na autenticação: API key não recebida")

            logger.info("Pluggy authentication successful")
            self._api_key = api_key
            return api_key
        
        except requests.exceptions.Timeout as timeout_error:
            logger.error(f"Timeout error in authenticate: {timeout_error}")
            raise ValueError("Timeout ao conectar com o serviço Pluggy. Verifique sua conexão e tente novamente.")
        
        except requests.exceptions.ConnectionError as conn_error:
            logger.error(f"Connection error in authenticate: {conn_error}")
            raise ValueError("Erro de conexão com o serviço Pluggy. Verifique sua internet e tente novamente.")
        
        except requests.exceptions.HTTPError as http_error:
            logger.error(f"HTTP error in authenticate: {http_error}")
            raise ValueError("Erro HTTP ao comunicar com o serviço Pluggy. Tente novamente em alguns minutos.")
        
        except requests.exceptions.RequestException as req_error:
            logger.error(f"Request error in authenticate: {req_error}")
            raise ValueError("Erro ao comunicar com o serviço Pluggy. Tente novamente em alguns minutos.")
        
        except ValueError:
            # Re-raise ValueError exceptions (these are user-friendly messages)
            raise
        
        except Exception as unexpected_error:
            # Log the actual error for debugging but show user-friendly message
            logger.error(f"Unexpected error in authenticate: {unexpected_error}", exc_info=True)
            raise ValueError("Erro interno ao autenticar com Pluggy. Tente novamente ou contate o suporte.")
    
    def create_connect_token(self, client_user_id=None):
        """
        Creates a Pluggy Connect token for user authentication.
        
        Args:
            client_user_id (str, optional): User identifier for the token
            
        Returns:
            str: Access token for Pluggy Connect widget
            
        Raises:
            ValueError: User-friendly error messages for various failure scenarios
        """
        try:
            logger.info(f"Starting token generation for user: {client_user_id or 'anonymous'}")
            
            # Ensure we have an API key
            if not self._api_key:
                self.authenticate()
            
            # Generate connect token
            token_url = f"{self.base_url}/connect_token"
            token_headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "X-API-KEY": self._api_key
            }
            token_payload = {"clientUserId": client_user_id} if client_user_id else {}

            logger.debug(f"Generating connect token at {token_url}")
            token_resp = requests.post(
                token_url, 
                headers=token_headers, 
                json=token_payload, 
                timeout=15
            )

            # Handle token generation errors with specific logging
            if token_resp.status_code == 401:
                logger.error("Connect token generation failed: Invalid API key")
                raise ValueError("Erro de autorização ao gerar token. Tente novamente.")
            elif token_resp.status_code == 400:
                logger.error(f"Connect token generation failed: Bad request - {token_resp.text}")
                raise ValueError("Dados inválidos para geração do token. Verifique as informações.")
            elif token_resp.status_code == 429:
                logger.error("Connect token generation failed: Rate limit exceeded")
                raise ValueError("Muitas tentativas de geração de token. Aguarde alguns minutos.")
            elif token_resp.status_code >= 500:
                logger.error(f"Pluggy server error during token generation: {token_resp.status_code}")
                raise ValueError("Serviço Pluggy temporariamente indisponível. Tente novamente em alguns minutos.")
            elif token_resp.status_code != 200:
                logger.error(f"Connect token generation failed with status {token_resp.status_code}: {token_resp.text}")
                raise ValueError(f"Erro ao gerar token de conexão (código {token_resp.status_code})")

            # Parse token response
            try:
                token_data = token_resp.json()
                access_token = token_data.get("accessToken")
            except ValueError as json_error:
                logger.error(f"Invalid JSON response from connect token endpoint: {json_error}")
                raise ValueError("Resposta inválida do serviço Pluggy. Tente novamente.")
            
            if not access_token:
                logger.error("No access token received from Pluggy")
                raise ValueError("Falha na geração do token: token não recebido")

            logger.info(f"Connect token generated successfully for user: {client_user_id or 'anonymous'}")
            return access_token
        
        except requests.exceptions.Timeout as timeout_error:
            logger.error(f"Timeout error in create_connect_token: {timeout_error}")
            raise ValueError("Timeout ao conectar com o serviço Pluggy. Verifique sua conexão e tente novamente.")
        
        except requests.exceptions.ConnectionError as conn_error:
            logger.error(f"Connection error in create_connect_token: {conn_error}")
            raise ValueError("Erro de conexão com o serviço Pluggy. Verifique sua internet e tente novamente.")
        
        except requests.exceptions.HTTPError as http_error:
            logger.error(f"HTTP error in create_connect_token: {http_error}")
            raise ValueError("Erro HTTP ao comunicar com o serviço Pluggy. Tente novamente em alguns minutos.")
        
        except requests.exceptions.RequestException as req_error:
            logger.error(f"Request error in create_connect_token: {req_error}")
            raise ValueError("Erro ao comunicar com o serviço Pluggy. Tente novamente em alguns minutos.")
        
        except ValueError:
            # Re-raise ValueError exceptions (these are user-friendly messages)
            raise
        
        except Exception as unexpected_error:
            # Log the actual error for debugging but show user-friendly message
            logger.error(f"Unexpected error in create_connect_token: {unexpected_error}", exc_info=True)
            raise ValueError("Erro interno ao gerar token de conexão. Tente novamente ou contate o suporte.")

# =========================================================
# CONVENIENCE FUNCTIONS
# =========================================================
def create_connect_token(client_user_id=None):
    """
    Convenience function to create a connect token.
    Creates a PluggyClient instance and generates a token.
    
    Args:
        client_user_id (str, optional): User identifier for the token
        
    Returns:
        str: Access token for Pluggy Connect widget
        
    Raises:
        ValueError: User-friendly error messages for various failure scenarios
    """
    client = PluggyClient()
    return client.create_connect_token(client_user_id)