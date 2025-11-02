# Design Document

## Overview

This design addresses the update of the Pluggy Connect SDK integration from version 2.6.0 to 2.9.2 in a Python + Streamlit application. The current implementation has several issues: outdated SDK endpoint causing 404 errors, poor error handling with exposed tracebacks, and lack of user feedback during connection processes.

The solution involves updating the SDK endpoint, implementing proper environment validation, enhancing error handling, improving user experience with status messages, and optionally refactoring the code into a modular structure.

## Architecture

### Current Architecture
```
app.py (monolithic)
├── Environment loading (.env)
├── Pluggy API integration (inline)
├── Database operations (db.py)
├── Streamlit UI components
└── Inline JavaScript SDK loading
```

### Proposed Architecture
```
app.py (main application)
├── modules/
│   ├── pluggy_utils.py (Pluggy API operations)
│   └── db.py (database operations - existing)
├── static/
│   └── pluggy_loader.js (client-side SDK loading)
└── .env (environment configuration)
```

### Key Design Principles
1. **Separation of Concerns**: Isolate Pluggy-specific logic from main application
2. **Error Resilience**: Graceful handling of API failures and configuration issues
3. **User Experience**: Clear status messages and loading indicators
4. **Maintainability**: Modular code structure for easier updates

## Components and Interfaces

### 1. Environment Validation Module
**Location**: `modules/pluggy_utils.py`

```python
def validate_environment() -> dict:
    """Validates required environment variables and returns configuration"""
    
def get_pluggy_config() -> dict:
    """Returns validated Pluggy configuration"""
```

**Responsibilities**:
- Validate PLUGGY_CLIENT_ID and PLUGGY_CLIENT_SECRET
- Return structured configuration object
- Raise descriptive errors for missing variables

### 2. Pluggy API Client
**Location**: `modules/pluggy_utils.py`

```python
class PluggyClient:
    def __init__(self, config: dict)
    def authenticate(self) -> str
    def create_connect_token(self, client_user_id: str = None) -> str
```

**Responsibilities**:
- Handle Pluggy API authentication
- Generate connect tokens
- Implement retry logic and timeout handling
- Provide clean error messages

### 3. Enhanced JavaScript SDK Loader
**Location**: `static/pluggy_loader.js`

```javascript
class PluggySDKLoader {
    constructor(config)
    async loadSDK()
    initializeWidget(token, callbacks)
    handleError(error)
}
```

**Responsibilities**:
- Load SDK from correct v2.9.2 endpoint
- Provide loading status feedback
- Handle SDK loading failures gracefully
- Initialize Pluggy Connect widget with proper callbacks

### 4. UI Status Manager
**Location**: `app.py` (Streamlit components)

**Responsibilities**:
- Display loading states ("Conectando com segurança...")
- Show success/error messages
- Hide technical details from users
- Manage form state and validation

## Data Models

### Configuration Model
```python
@dataclass
class PluggyConfig:
    client_id: str
    client_secret: str
    base_url: str = "https://api.pluggy.ai"
    sdk_version: str = "v2.9.2"
    sdk_url: str = "https://cdn.pluggy.ai/pluggy-connect/v2.9.2/pluggy-connect.js"
```

### Connection State Model
```python
@dataclass
class ConnectionState:
    token: Optional[str] = None
    status: str = "idle"  # idle, loading, connecting, connected, error
    error_message: Optional[str] = None
    user_data: Optional[dict] = None
```

### Widget Configuration Model
```javascript
const widgetConfig = {
    connectToken: string,
    includeSandbox: boolean,
    language: string,
    theme: string,
    callbacks: {
        onOpen: function,
        onClose: function,
        onSuccess: function,
        onError: function
    }
}
```

## Error Handling

### 1. Environment Configuration Errors
- **Detection**: Startup validation of required environment variables
- **Response**: Display configuration error message, prevent app initialization
- **User Message**: "Configuração incompleta. Verifique as variáveis de ambiente."

### 2. Pluggy API Errors
- **Authentication Failures**: Invalid credentials, network issues
- **Token Generation Failures**: API unavailable, rate limiting
- **Response**: Log detailed error, show user-friendly message
- **User Message**: "Erro ao conectar com o serviço. Tente novamente em alguns minutos."

### 3. SDK Loading Errors
- **Detection**: Failed fetch from CDN, JavaScript errors
- **Response**: Fallback error display, retry option
- **User Message**: "Erro ao carregar componente de conexão. Verifique sua conexão."

### 4. Widget Initialization Errors
- **Detection**: PluggyConnect constructor failures, invalid token
- **Response**: Clear error state, allow retry
- **User Message**: "Erro ao inicializar conexão. Tente gerar um novo token."

### Error Logging Strategy
```python
import logging

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log errors with context
logger.error("Pluggy API error", extra={
    "endpoint": url,
    "status_code": response.status_code,
    "user_id": client_user_id
})
```

## Testing Strategy

### 1. Unit Tests
**Target**: `modules/pluggy_utils.py`
- Environment validation functions
- PluggyClient authentication and token generation
- Error handling scenarios

### 2. Integration Tests
**Target**: Full Pluggy API flow
- End-to-end token generation
- SDK loading and widget initialization
- Database operations with mock data

### 3. UI Tests
**Target**: Streamlit interface
- Form validation and submission
- Status message display
- Error state handling

### 4. Manual Testing Checklist
- [ ] SDK loads from v2.9.2 endpoint without 404 errors
- [ ] Environment validation catches missing variables
- [ ] User sees "Conectando com segurança..." during token generation
- [ ] Pluggy widget opens correctly with valid token
- [ ] Error messages are user-friendly (no tracebacks)
- [ ] Database saves connection data successfully

## Implementation Phases

### Phase 1: Core SDK Update
1. Update SDK endpoint to v2.9.2
2. Fix immediate 404 errors
3. Verify basic widget functionality

### Phase 2: Error Handling Enhancement
1. Implement environment validation
2. Add proper exception handling
3. Replace traceback displays with user-friendly messages

### Phase 3: User Experience Improvements
1. Add loading status messages
2. Implement connection state management
3. Enhance widget callback handling

### Phase 4: Code Organization (Optional)
1. Extract Pluggy utilities to separate module
2. Move JavaScript to static file
3. Implement proper separation of concerns

## Security Considerations

### 1. Environment Variables
- Validate all required variables at startup
- Use secure defaults where appropriate
- Never expose secrets in error messages

### 2. API Token Handling
- Generate tokens with minimal required scope
- Implement token expiration handling
- Clear tokens from session state after use

### 3. Database Security
- Maintain existing SSL connection requirements
- Validate all input data before database operations
- Use parameterized queries (already implemented)

## Performance Considerations

### 1. SDK Loading
- Implement async loading to prevent UI blocking
- Add timeout handling for CDN requests
- Provide fallback for slow connections

### 2. API Calls
- Maintain existing timeout configurations (15s)
- Implement exponential backoff for retries
- Cache authentication tokens when possible

### 3. Database Operations
- Keep existing connection pooling approach
- Maintain ON CONFLICT handling for duplicate items
- Use existing timeout configurations

## Deployment Considerations

### 1. Render Platform Compatibility
- Ensure all changes work with existing Render deployment
- Maintain compatibility with current environment variable setup
- Test SSL/TLS requirements for external API calls

### 2. Rollback Strategy
- Keep backup of current working implementation
- Implement feature flags for gradual rollout
- Maintain backward compatibility during transition

### 3. Monitoring
- Add logging for SDK loading success/failure rates
- Monitor API response times and error rates
- Track widget initialization success rates