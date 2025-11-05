# deployment_validator.py
import os
import requests
import psycopg
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DeploymentValidator:
    """Validates deployment readiness for Railway Streamlit application"""
    
    def __init__(self):
        self.validation_results = {}
        self.errors = []
        self.warnings = []
        
    def log_validation(self, message: str, level: str = "INFO", component: str = "VALIDATOR"):
        """Enhanced logging for validation steps"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"[{component} {level}] {timestamp}"
        print(f"{prefix} {message}")
        
        if level == "ERROR":
            logger.error(f"{component}: {message}")
            self.errors.append(f"{component}: {message}")
        elif level == "WARNING":
            logger.warning(f"{component}: {message}")
            self.warnings.append(f"{component}: {message}")
        else:
            logger.info(f"{component}: {message}")
    
    def validate_environment_variables(self) -> bool:
        """Validate all required environment variables are present and valid"""
        self.log_validation("=== ENVIRONMENT VARIABLES VALIDATION ===", component="ENV")
        
        required_vars = {
            "PORT": "Railway dynamic port assignment",
            "PLUGGY_CLIENT_ID": "Pluggy API authentication client ID",
            "PLUGGY_CLIENT_SECRET": "Pluggy API authentication secret",
            "DB_HOST": "PostgreSQL database host",
            "DB_USER": "PostgreSQL database user", 
            "DB_PASSWORD": "PostgreSQL database password",
            "DB_NAME": "PostgreSQL database name"
        }
        
        optional_vars = {
            "DB_PORT": ("PostgreSQL database port", "5432"),
            "DB_SSLMODE": ("PostgreSQL SSL mode", "require")
        }
        
        all_valid = True
        
        # Check required variables
        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value:
                self.log_validation(f"❌ MISSING: {var} - {description}", "ERROR", "ENV")
                all_valid = False
            else:
                # Mask sensitive values
                if any(sensitive in var.upper() for sensitive in ["SECRET", "PASSWORD", "KEY"]):
                    masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                    self.log_validation(f"✅ PRESENT: {var} - {description} (masked: {masked})", component="ENV")
                else:
                    self.log_validation(f"✅ PRESENT: {var} - {description} (value: {value})", component="ENV")
        
        # Check optional variables with defaults
        for var, (description, default) in optional_vars.items():
            value = os.getenv(var, default)
            status = "configured" if os.getenv(var) else "default"
            self.log_validation(f"📋 OPTIONAL: {var} - {description} (value: {value}, {status})", component="ENV")
        
        # Validate PORT specifically for Railway
        port = os.getenv("PORT")
        if port:
            try:
                port_num = int(port)
                if 1 <= port_num <= 65535:
                    self.log_validation(f"✅ PORT validation successful: {port_num}", component="ENV")
                else:
                    self.log_validation(f"❌ PORT out of range: {port_num} (must be 1-65535)", "ERROR", "ENV")
                    all_valid = False
            except ValueError:
                self.log_validation(f"❌ PORT not numeric: {port}", "ERROR", "ENV")
                all_valid = False
        else:
            self.log_validation("⚠️ PORT not set - using fallback (OK for local development)", "WARNING", "ENV")
        
        self.validation_results["environment"] = all_valid
        return all_valid
    
    def validate_database_connectivity(self) -> bool:
        """Test PostgreSQL database connection and basic operations"""
        self.log_validation("=== DATABASE CONNECTIVITY VALIDATION ===", component="DB")
        
        try:
            from modules.db import DB_CONFIG, get_conn
            
            # Log connection parameters (without sensitive data)
            self.log_validation(f"Testing connection to: {DB_CONFIG.get('host')}:{DB_CONFIG.get('port', '5432')}", component="DB")
            self.log_validation(f"Database: {DB_CONFIG.get('dbname')}", component="DB")
            self.log_validation(f"User: {DB_CONFIG.get('user')}", component="DB")
            self.log_validation(f"SSL Mode: {DB_CONFIG.get('sslmode', 'require')}", component="DB")
            
            # Test basic connection
            self.log_validation("Testing database connection...", component="DB")
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Test connection with version query
                    cur.execute("SELECT version();")
                    version = cur.fetchone()[0]
                    self.log_validation(f"✅ Connection successful - PostgreSQL: {version[:50]}...", component="DB")
                    
                    # Test schema access
                    cur.execute("SELECT current_database(), current_user;")
                    db_info = cur.fetchone()
                    self.log_validation(f"✅ Connected to database: {db_info[0]} as user: {db_info[1]}", component="DB")
                    
                    # Test table existence and access
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'financefly_clients'
                        );
                    """)
                    table_exists = cur.fetchone()[0]
                    
                    if table_exists:
                        cur.execute("SELECT COUNT(*) FROM financefly_clients;")
                        count = cur.fetchone()[0]
                        self.log_validation(f"✅ Table 'financefly_clients' exists with {count} records", component="DB")
                    else:
                        self.log_validation("⚠️ Table 'financefly_clients' does not exist yet (will be created)", "WARNING", "DB")
                    
                    # Test write permissions
                    cur.execute("SELECT has_table_privilege(current_user, 'financefly_clients', 'INSERT');")
                    can_insert = cur.fetchone()[0] if table_exists else True
                    if can_insert:
                        self.log_validation("✅ Database write permissions confirmed", component="DB")
                    else:
                        self.log_validation("❌ No INSERT permission on financefly_clients table", "ERROR", "DB")
                        self.validation_results["database"] = False
                        return False
            
            self.validation_results["database"] = True
            return True
            
        except psycopg.OperationalError as e:
            error_msg = str(e).lower()
            if "could not connect" in error_msg:
                self.log_validation(f"❌ Cannot reach database server: {e}", "ERROR", "DB")
                self.log_validation("Check DB_HOST and DB_PORT configuration", "ERROR", "DB")
            elif "authentication failed" in error_msg:
                self.log_validation(f"❌ Database authentication failed: {e}", "ERROR", "DB")
                self.log_validation("Check DB_USER and DB_PASSWORD configuration", "ERROR", "DB")
            elif "database" in error_msg and "does not exist" in error_msg:
                self.log_validation(f"❌ Database does not exist: {e}", "ERROR", "DB")
                self.log_validation("Check DB_NAME configuration", "ERROR", "DB")
            else:
                self.log_validation(f"❌ Database connection error: {e}", "ERROR", "DB")
            
            self.validation_results["database"] = False
            return False
            
        except Exception as e:
            self.log_validation(f"❌ Unexpected database error: {e}", "ERROR", "DB")
            self.validation_results["database"] = False
            return False
    
    def validate_pluggy_api_connectivity(self) -> bool:
        """Test Pluggy API connectivity and authentication"""
        self.log_validation("=== PLUGGY API CONNECTIVITY VALIDATION ===", component="PLUGGY")
        
        client_id = os.getenv("PLUGGY_CLIENT_ID")
        client_secret = os.getenv("PLUGGY_CLIENT_SECRET")
        base_url = "https://api.pluggy.ai"
        
        if not client_id or not client_secret:
            self.log_validation("❌ Pluggy API credentials not configured", "ERROR", "PLUGGY")
            self.validation_results["pluggy_api"] = False
            return False
        
        try:
            self.log_validation(f"Testing Pluggy API connectivity to: {base_url}", component="PLUGGY")
            self.log_validation(f"Using Client ID: {client_id[:8]}...{client_id[-4:]}", component="PLUGGY")
            
            # Test authentication endpoint
            auth_payload = {
                "clientId": client_id,
                "clientSecret": client_secret
            }
            
            self.log_validation("Attempting Pluggy API authentication...", component="PLUGGY")
            auth_response = requests.post(
                f"{base_url}/auth",
                headers={
                    "accept": "application/json",
                    "content-type": "application/json"
                },
                json=auth_payload,
                timeout=15
            )
            
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                api_key = auth_data.get("apiKey")
                
                if api_key:
                    self.log_validation("✅ Pluggy API authentication successful", component="PLUGGY")
                    self.log_validation(f"API Key received: {api_key[:8]}...{api_key[-4:]}", component="PLUGGY")
                    
                    # Test connect_token endpoint
                    self.log_validation("Testing connect_token generation...", component="PLUGGY")
                    token_response = requests.post(
                        f"{base_url}/connect_token",
                        headers={
                            "accept": "application/json",
                            "content-type": "application/json",
                            "X-API-KEY": api_key
                        },
                        json={"clientUserId": "validation_test"},
                        timeout=15
                    )
                    
                    if token_response.status_code == 200:
                        token_data = token_response.json()
                        connect_token = token_data.get("accessToken")
                        if connect_token:
                            self.log_validation("✅ Connect token generation successful", component="PLUGGY")
                            self.log_validation(f"Connect token: {connect_token[:8]}...{connect_token[-4:]}", component="PLUGGY")
                        else:
                            self.log_validation("❌ Connect token not received in response", "ERROR", "PLUGGY")
                            self.validation_results["pluggy_api"] = False
                            return False
                    else:
                        self.log_validation(f"❌ Connect token request failed: {token_response.status_code}", "ERROR", "PLUGGY")
                        self.log_validation(f"Response: {token_response.text}", "ERROR", "PLUGGY")
                        self.validation_results["pluggy_api"] = False
                        return False
                else:
                    self.log_validation("❌ API key not received in authentication response", "ERROR", "PLUGGY")
                    self.validation_results["pluggy_api"] = False
                    return False
            else:
                self.log_validation(f"❌ Pluggy API authentication failed: {auth_response.status_code}", "ERROR", "PLUGGY")
                self.log_validation(f"Response: {auth_response.text}", "ERROR", "PLUGGY")
                self.validation_results["pluggy_api"] = False
                return False
            
            self.validation_results["pluggy_api"] = True
            return True
            
        except requests.exceptions.Timeout:
            self.log_validation("❌ Pluggy API request timeout", "ERROR", "PLUGGY")
            self.validation_results["pluggy_api"] = False
            return False
        except requests.exceptions.ConnectionError:
            self.log_validation("❌ Cannot connect to Pluggy API", "ERROR", "PLUGGY")
            self.validation_results["pluggy_api"] = False
            return False
        except Exception as e:
            self.log_validation(f"❌ Unexpected Pluggy API error: {e}", "ERROR", "PLUGGY")
            self.validation_results["pluggy_api"] = False
            return False
    
    def run_full_validation(self) -> Dict[str, bool]:
        """Run complete deployment readiness validation"""
        self.log_validation("🚀 STARTING DEPLOYMENT READINESS VALIDATION", component="MAIN")
        self.log_validation("=" * 60, component="MAIN")
        
        start_time = datetime.now()
        
        # Run all validation checks
        env_valid = self.validate_environment_variables()
        db_valid = self.validate_database_connectivity()
        api_valid = self.validate_pluggy_api_connectivity()
        
        # Calculate overall status
        all_valid = env_valid and db_valid and api_valid
        
        # Generate summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.log_validation("=" * 60, component="MAIN")
        self.log_validation("🏁 DEPLOYMENT VALIDATION SUMMARY", component="MAIN")
        self.log_validation(f"Validation Duration: {duration:.2f} seconds", component="MAIN")
        self.log_validation("", component="MAIN")
        
        # Component status
        components = [
            ("Environment Variables", env_valid),
            ("Database Connectivity", db_valid),
            ("Pluggy API Connectivity", api_valid)
        ]
        
        for component, status in components:
            status_icon = "✅" if status else "❌"
            self.log_validation(f"{status_icon} {component}: {'PASS' if status else 'FAIL'}", component="MAIN")
        
        self.log_validation("", component="MAIN")
        
        # Overall status
        if all_valid:
            self.log_validation("🎉 DEPLOYMENT READINESS: VALIDATED", component="MAIN")
            self.log_validation("Application is ready for Railway deployment", component="MAIN")
        else:
            self.log_validation("⚠️ DEPLOYMENT READINESS: FAILED", "ERROR", "MAIN")
            self.log_validation(f"Found {len(self.errors)} errors and {len(self.warnings)} warnings", "ERROR", "MAIN")
            
            if self.errors:
                self.log_validation("Critical errors that must be fixed:", "ERROR", "MAIN")
                for error in self.errors:
                    self.log_validation(f"  • {error}", "ERROR", "MAIN")
        
        self.validation_results["overall"] = all_valid
        self.validation_results["duration"] = duration
        self.validation_results["errors"] = self.errors
        self.validation_results["warnings"] = self.warnings
        
        return self.validation_results

def run_deployment_validation() -> Dict[str, bool]:
    """Convenience function to run deployment validation"""
    validator = DeploymentValidator()
    return validator.run_full_validation()