# Railway Streamlit Deployment Design

## Overview

This design addresses the 502 error issue in the Railway deployment of the Financefly Connector Streamlit application. The core problem is that Railway requires applications to bind to a dynamic port provided via the $PORT environment variable, and the web process must be correctly configured to handle external requests.

The solution involves ensuring proper port configuration, web process setup, and providing fallback mechanisms for robust deployment.

## Architecture

### Deployment Flow
```
Railway Platform → Environment Variables ($PORT) → Procfile → Streamlit App → External Access
```

### Port Configuration Strategy
1. **Primary Method**: Use $PORT environment variable from Railway
2. **Fallback Method**: Default to port 8080 if $PORT is unavailable
3. **Configuration Points**: Both Procfile and app.py should handle port configuration
4. **Binding**: Always bind to 0.0.0.0 for external access

### Process Management
- **Web Process**: Defined in Procfile as the main entry point
- **Alternative Startup**: Bash script option for complex initialization
- **Environment Handling**: Proper export and usage of environment variables

## Components and Interfaces

### 1. Procfile Configuration
**Purpose**: Define the web process for Railway
**Current State**: Already configured correctly
**Validation**: Ensure it uses $PORT variable and correct Streamlit parameters

```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

### 2. Application Startup (app.py)
**Purpose**: Configure Streamlit server settings programmatically
**Current State**: Has environment variable configuration
**Enhancement**: Ensure proper port handling and Railway compatibility

**Key Configuration Points**:
- `STREAMLIT_SERVER_PORT`: Must use $PORT from Railway
- `STREAMLIT_SERVER_ADDRESS`: Must be 0.0.0.0
- `STREAMLIT_SERVER_HEADLESS`: Must be true for server deployment

### 3. Alternative Startup Script (start.sh)
**Purpose**: Provide robust startup mechanism if Procfile approach fails
**Implementation**: Bash script that exports variables and starts Streamlit
**Usage**: Fallback option for complex deployment scenarios

### 4. Runtime Configuration
**Purpose**: Ensure Python version compatibility
**Current State**: python-3.11.9 specified
**Validation**: Confirm Railway supports this version

## Data Models

### Environment Variables
```
Required by Railway:
- PORT: Dynamic port assigned by Railway

Required by Application:
- PLUGGY_CLIENT_ID: Pluggy API authentication
- PLUGGY_CLIENT_SECRET: Pluggy API authentication
- DB_HOST: PostgreSQL connection
- DB_PORT: PostgreSQL connection
- DB_NAME: Database name
- DB_USER: Database user
- DB_PASSWORD: Database password
- DB_SSLMODE: SSL configuration (require)
```

### Configuration Flow
```
Railway Environment → App Environment Variables → Streamlit Server Config → External Access
```

## Error Handling

### 502 Error Resolution
**Root Cause**: Application not binding to Railway's assigned port
**Solution**: Ensure $PORT variable is properly used in both Procfile and app.py

### Port Configuration Issues
**Scenario**: $PORT variable not available or incorrectly used
**Handling**: 
1. Validate $PORT exists and is numeric
2. Fallback to default port 8080
3. Log port configuration for debugging

### Process Startup Failures
**Scenario**: Streamlit fails to start with current configuration
**Handling**:
1. Alternative startup script (start.sh)
2. Enhanced error logging
3. Environment variable validation

### Database Connection Issues
**Scenario**: PostgreSQL connection fails in Railway environment
**Handling**:
1. Validate all DB environment variables
2. Test connection during startup
3. Provide meaningful error messages

## Testing Strategy

### Deployment Validation
1. **Port Binding Test**: Verify application binds to $PORT
2. **External Access Test**: Confirm public URL returns 200 status
3. **Pluggy Integration Test**: Validate API connectivity works
4. **Database Connection Test**: Ensure PostgreSQL operations function

### Log Verification
1. **Startup Logs**: Look for "You can now view your Streamlit app in your browser"
2. **Port Logs**: Confirm correct port number in Network URL
3. **Error Logs**: Check for any configuration or startup errors

### Fallback Testing
1. **Alternative Startup**: Test start.sh script functionality
2. **Environment Handling**: Validate variable export and usage
3. **Static File Serving**: Ensure /static directory is accessible if needed

## Implementation Approach

### Phase 1: Validate Current Configuration
- Review existing Procfile and app.py settings
- Identify specific Railway compatibility issues
- Test current deployment logs for error patterns

### Phase 2: Fix Port Configuration
- Ensure proper $PORT variable usage
- Update app.py environment variable handling if needed
- Validate Streamlit server parameter configuration

### Phase 3: Create Fallback Mechanism
- Implement start.sh script as alternative startup method
- Update Procfile to use bash script if needed
- Add environment variable validation and logging

### Phase 4: Validate and Test
- Deploy with updated configuration
- Test external access via Railway URL
- Verify Pluggy widget functionality
- Confirm database operations work correctly

## Railway-Specific Considerations

### Port Requirements
- Railway assigns dynamic ports via $PORT environment variable
- Applications must bind to 0.0.0.0, not localhost
- Port must be used exactly as provided by Railway

### Process Configuration
- Web process must be defined in Procfile
- Process must start within Railway's timeout limits
- Application must respond to health checks

### Static File Serving
- Streamlit handles static files automatically
- /static directory should be accessible
- No additional web server configuration needed for Streamlit

### Environment Variables
- All variables are injected by Railway at runtime
- No need for .env file in production
- Variables should be validated during startup