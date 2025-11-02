# app.py
import os
import streamlit as st
import logging
import time
from modules.db import init_db, save_client
from modules.pluggy_utils import validate_environment, create_connect_token
from modules.error_utils import log_and_display_error, display_environment_errors, handle_pluggy_error

# =========================================================
# LOGGING CONFIGURATION
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# =========================================================
# CONFIGURAÇÃO INICIAL
# =========================================================
# Validate environment before proceeding
try:
    pluggy_config = validate_environment()
except ValueError as env_errors:
    if isinstance(env_errors.args[0], list):
        display_environment_errors(env_errors.args[0])
    else:
        st.error("❌ Erro ao validar configuração do ambiente.")
        st.info("💡 Verifique se o arquivo .env está acessível e tente novamente.")
        st.stop()

st.set_page_config(page_title="Financefly Connector", page_icon="🪁", layout="centered")

PLUGGY_CLIENT_ID = pluggy_config["client_id"]
PLUGGY_CLIENT_SECRET = pluggy_config["client_secret"]
PLUGGY_BASE_URL = pluggy_config["base_url"]

# =========================================================
# ESTADO INICIAL DO APP
# =========================================================
if "connect_token" not in st.session_state:
    st.session_state.connect_token = None
if "form_data" not in st.session_state:
    st.session_state.form_data = {"name": "", "email": ""}

# =========================================================
# CONEXÃO COM O BANCO
# =========================================================
try:
    logger.info("Initializing database connection")
    init_db()
    logger.info("Database initialized successfully")
except Exception as db_error:
    logger.error(f"Database initialization failed: {db_error}", exc_info=True)
    st.error("❌ Erro ao conectar com o banco de dados. Tente novamente em alguns minutos.")
    st.info("💡 Se o problema persistir, verifique a configuração do banco de dados.")
    st.stop()

# =========================================================
# INTERFACE STREAMLIT
# =========================================================
st.title("Financefly Connector")
st.caption("Conecte sua conta bancária via Pluggy com segurança.")

params = st.query_params
item_id = params.get("itemId", [None])[0] if isinstance(params.get("itemId"), list) else params.get("itemId")

if item_id:
    name = st.session_state.form_data.get("name")
    email = st.session_state.form_data.get("email")

    if name and email:
        try:
            logger.info(f"Saving client data for item_id: {item_id}, email: {email}")
            save_client(name, email, item_id)
            logger.info(f"Client data saved successfully for item_id: {item_id}")
            st.success(f"✅ Conta conectada com sucesso! ID: {item_id}")
        except Exception as save_error:
            logger.error(f"Database save error for item_id {item_id}: {save_error}", exc_info=True)
            st.error("❌ Erro ao salvar dados da conexão. Tente novamente.")
            st.info("💡 Se o problema persistir, entre em contato com o suporte técnico.")
    else:
        logger.warning(f"Connection received for item_id {item_id} but missing form data")
        st.warning("⚠️ Conexão recebida, mas faltam dados do formulário.")
    st.query_params.clear()
    st.stop()

# =========================================================
# FORMULÁRIO DE CADASTRO
# =========================================================
with st.form("client_form"):
    name = st.text_input("Nome completo", st.session_state.form_data["name"])
    email = st.text_input("E-mail", st.session_state.form_data["email"])
    submit = st.form_submit_button("Conectar conta")

if submit:
    # Validate form inputs
    if not name or not email:
        st.warning("⚠️ Preencha todos os campos para continuar.")
        st.stop()
    
    # Basic email validation
    if "@" not in email or "." not in email:
        st.warning("⚠️ Por favor, insira um e-mail válido.")
        st.stop()
    
    # Store form data in session
    st.session_state.form_data = {"name": name, "email": email}
    logger.info(f"Form submitted for user: {email}")

    # Enhanced status messaging during token generation
    status_container = st.container()
    
    with status_container:
        # Step 1: Validating credentials
        with st.spinner("🔐 Validando credenciais..."):
            st.info("🔄 **Etapa 1/3:** Verificando configuração de segurança")
            time.sleep(0.5)  # Brief pause for user feedback
        
        # Step 2: Connecting securely
        with st.spinner("🔗 Conectando com segurança..."):
            st.info("🔄 **Etapa 2/3:** Estabelecendo conexão segura com Pluggy")
            try:
                logger.info(f"Generating connect token for user: {email}")
                token = create_connect_token(client_user_id=email)
                st.session_state.connect_token = token
                logger.info(f"Connect token generated successfully for user: {email}")
                
            except Exception as token_error:
                handle_pluggy_error(token_error, email)
                st.stop()
        
        # Step 3: Preparing connection interface
        with st.spinner("⚙️ Preparando interface de conexão..."):
            st.info("🔄 **Etapa 3/3:** Carregando componentes de segurança")
            time.sleep(0.3)  # Brief pause for user feedback
        
        # Success message
        st.success("✅ **Conexão preparada com sucesso!** Abrindo interface segura...")
        time.sleep(0.5)  # Brief pause before showing widget

# =========================================================
# PLUGGY CONNECT WIDGET
# =========================================================
if st.session_state.connect_token:
    logger.info("Displaying Pluggy Connect widget")
    
    # Enhanced status display with progress indicators
    st.markdown("### 🔐 Conexão Segura Pluggy")
    st.info("🚀 **Iniciando processo de conexão bancária segura...**")

    html = f"""
    <div id="pluggy-status" style="margin:12px 0; font-family: ui-sans-serif, system-ui; padding: 15px; background: linear-gradient(135deg, #f0f2f6 0%, #e8f4f8 100%); border-radius: 8px; border-left: 4px solid #28a745;">
      <div style="color: #28a745; font-weight: 600; font-size: 1.1em; margin-bottom: 8px;">
        ✅ Token de conexão gerado com sucesso
      </div>
      <div style="font-size: 0.85em; color: #6c757d; margin-bottom: 12px;">
        Token: <code style="background: #fff; padding: 2px 6px; border-radius: 3px;">{st.session_state.connect_token[:8]}...</code>
      </div>
      <div id="progress-bar" style="background: #e9ecef; height: 6px; border-radius: 3px; overflow: hidden; margin-bottom: 8px;">
        <div id="progress-fill" style="background: linear-gradient(90deg, #28a745, #20c997); height: 100%; width: 0%; transition: width 0.3s ease;"></div>
      </div>
      <div id="current-step" style="font-size: 0.9em; color: #495057; font-weight: 500;">
        🔄 Preparando conexão...
      </div>
    </div>

    <script>
      (async function() {{
        const statusEl = document.getElementById('pluggy-status');
        const progressFill = document.getElementById('progress-fill');
        const currentStep = document.getElementById('current-step');
        let currentProgress = 0;
        
        // Initialize global widget state tracking
        window.pluggyWidgetState = 'initializing';
        window.pluggyConnectionData = null;
        window.pluggyErrorData = null;
        window.pluggyConnectInstance = null;
        
        function updateProgress(percent, stepText) {{
          currentProgress = Math.max(currentProgress, percent);
          progressFill.style.width = currentProgress + '%';
          currentStep.innerHTML = stepText;
        }}
        
        function log(msg, type = 'info', showInStep = false) {{
          const p = document.createElement('div');
          p.style.marginTop = '8px';
          p.style.padding = '8px 12px';
          p.style.borderRadius = '5px';
          p.style.fontSize = '0.9em';
          p.style.fontWeight = '500';
          
          if (type === 'error') {{
            p.style.backgroundColor = '#f8d7da';
            p.style.color = '#721c24';
            p.style.border = '1px solid #f5c6cb';
            p.innerHTML = '❌ ' + msg;
            if (showInStep) updateProgress(currentProgress, '❌ ' + msg);
          }} else if (type === 'success') {{
            p.style.backgroundColor = '#d4edda';
            p.style.color = '#155724';
            p.style.border = '1px solid #c3e6cb';
            p.innerHTML = '✅ ' + msg;
            if (showInStep) updateProgress(currentProgress, '✅ ' + msg);
          }} else if (type === 'warning') {{
            p.style.backgroundColor = '#fff3cd';
            p.style.color = '#856404';
            p.style.border = '1px solid #ffeaa7';
            p.innerHTML = '⚠️ ' + msg;
            if (showInStep) updateProgress(currentProgress, '⚠️ ' + msg);
          }} else {{
            p.style.backgroundColor = '#d1ecf1';
            p.style.color = '#0c5460';
            p.style.border = '1px solid #bee5eb';
            p.innerHTML = '🔄 ' + msg;
            if (showInStep) updateProgress(currentProgress, '🔄 ' + msg);
          }}
          
          statusEl.appendChild(p);
        }}

        // Step 1: Initialize SDK loading
        updateProgress(10, "🔄 Iniciando carregamento do SDK...");
        await new Promise(resolve => setTimeout(resolve, 300));

        // Step 2: Load SDK
        updateProgress(25, "📦 Baixando componentes de segurança...");
        log("Carregando SDK Pluggy v2.9.2...", "info", true);

        // Enhanced SDK loading with better error handling and progress feedback
        try {{
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
          
          updateProgress(40, "🌐 Conectando com servidor Pluggy...");
          
          const sdkResp = await fetch("https://cdn.pluggy.ai/pluggy-connect/v2.9.2/pluggy-connect.js", {{
            signal: controller.signal,
            cache: 'default'
          }});
          
          clearTimeout(timeoutId);
          
          if (!sdkResp.ok) {{
            throw new Error(`Falha ao carregar SDK (HTTP ${{sdkResp.status}})`);
          }}
          
          updateProgress(60, "📥 Processando componentes...");
          const sdkText = await sdkResp.text();
          
          if (!sdkText || sdkText.length < 100) {{
            throw new Error("SDK carregado está vazio ou corrompido");
          }}
          
          updateProgress(75, "⚙️ Instalando componentes...");
          const scriptEl = document.createElement("script");
          scriptEl.textContent = sdkText;
          document.body.appendChild(scriptEl);
          
          log("SDK Pluggy carregado com sucesso!", "success");
          updateProgress(85, "✅ SDK carregado com sucesso!");
          
          // Wait a bit for SDK to initialize
          await new Promise(resolve => setTimeout(resolve, 800));
          
        }} catch (e) {{
          if (e.name === 'AbortError') {{
            log("Timeout ao carregar SDK. Verifique sua conexão.", "error", true);
          }} else {{
            log("Erro ao carregar SDK: " + e.message, "error", true);
          }}
          log("Tente recarregar a página ou verifique sua conexão com a internet.", "warning");
          return;
        }}

        // Step 3: Initialize widget
        updateProgress(90, "🔧 Inicializando widget de conexão...");
        
        // Enhanced widget initialization with better error handling
        try {{
          if (typeof PluggyConnect === 'undefined') {{
            throw new Error("SDK Pluggy não foi carregado corretamente");
          }}
          
          log("Configurando widget de conexão...", "info", true);
          
          // Enhanced widget configuration with better state management
          const widgetConfig = {{
            connectToken: "{st.session_state.connect_token}",
            includeSandbox: false,
            language: "pt",
            theme: "dark",
            
            // Enhanced callback handling with proper state management
            onOpen: () => {{
              updateProgress(100, "🎉 Widget aberto - Conecte sua conta!");
              log("Widget Pluggy aberto com sucesso! Você pode agora conectar sua conta bancária.", "success");
              
              // Store widget state
              window.pluggyWidgetState = 'opened';
              
              // Add modal overlay styling to ensure proper display
              const modalOverlay = document.querySelector('.pluggy-modal-overlay');
              if (modalOverlay) {{
                modalOverlay.style.zIndex = '999999';
                modalOverlay.style.position = 'fixed';
                modalOverlay.style.top = '0';
                modalOverlay.style.left = '0';
                modalOverlay.style.width = '100%';
                modalOverlay.style.height = '100%';
                modalOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
              }}
            }},
            
            onClose: () => {{
              updateProgress(95, "👋 Widget fechado pelo usuário");
              log("Widget Pluggy fechado. Você pode tentar novamente quando quiser.", "info");
              
              // Update widget state
              window.pluggyWidgetState = 'closed';
              
              // Clean up any modal styling
              const modalOverlay = document.querySelector('.pluggy-modal-overlay');
              if (modalOverlay) {{
                modalOverlay.remove();
              }}
            }},
            
            onSuccess: (data) => {{
              updateProgress(100, "🎉 Conexão realizada com sucesso!");
              log("🎉 Parabéns! Sua conta foi conectada com sucesso!", "success");
              
              // Update widget state
              window.pluggyWidgetState = 'success';
              
              // Enhanced success handling with data validation
              if (data && data.item && data.item.id) {{
                log(`✅ Processando dados da conexão... (ID: ${{data.item.id}})`, "success");
                log("🔄 Redirecionando para finalizar o processo...", "info");
                
                // Store connection data for potential use
                window.pluggyConnectionData = {{
                  itemId: data.item.id,
                  timestamp: new Date().toISOString(),
                  status: 'connected'
                }};
                
                // The redirect will be handled automatically by Pluggy
                // but we can add additional logging or state management here
                console.log("Connection successful:", data);
              }} else {{
                log("⚠️ Conexão realizada, mas dados incompletos recebidos.", "warning");
                console.warn("Success callback received incomplete data:", data);
              }}
            }},
            
            onError: (err) => {{
              console.error("Pluggy Connect Error:", err);
              updateProgress(currentProgress, "❌ Erro na conexão");
              
              // Update widget state
              window.pluggyWidgetState = 'error';
              
              // Enhanced error handling with categorization
              let errorMessage = "Erro desconhecido na conexão. Tente novamente.";
              let errorType = "unknown";
              
              if (err && err.message) {{
                errorMessage = err.message;
                
                // Categorize common errors for better user guidance
                if (err.message.includes('credentials') || err.message.includes('login')) {{
                  errorType = "credentials";
                  errorMessage = "Credenciais inválidas. Verifique seu usuário e senha.";
                }} else if (err.message.includes('timeout') || err.message.includes('network')) {{
                  errorType = "network";
                  errorMessage = "Problema de conexão. Verifique sua internet e tente novamente.";
                }} else if (err.message.includes('bank') || err.message.includes('institution')) {{
                  errorType = "bank";
                  errorMessage = "Problema com o banco selecionado. Tente outro banco ou aguarde alguns minutos.";
                }}
              }}
              
              log("Erro na conexão: " + errorMessage, "error");
              
              // Provide specific guidance based on error type
              switch(errorType) {{
                case "credentials":
                  log("💡 Dica: Certifique-se de usar as mesmas credenciais do seu internet banking.", "warning");
                  break;
                case "network":
                  log("💡 Dica: Verifique sua conexão com a internet e tente novamente.", "warning");
                  break;
                case "bank":
                  log("💡 Dica: Alguns bancos podem estar temporariamente indisponíveis.", "warning");
                  break;
                default:
                  log("💡 Dica: Tente recarregar a página ou entre em contato com o suporte.", "warning");
              }}
              
              // Store error data for debugging
              window.pluggyErrorData = {{
                error: err,
                timestamp: new Date().toISOString(),
                errorType: errorType
              }};
            }}
          }};
          
          // Initialize the widget
          const connect = new PluggyConnect(widgetConfig);
          
          // Store widget instance for potential future use
          window.pluggyConnectInstance = connect;
          
          updateProgress(95, "🚀 Abrindo interface de conexão...");
          log("Abrindo interface segura de conexão bancária...", "info", true);
          
          // Enhanced widget opening with validation
          try {{
            // Ensure widget is properly initialized before opening
            if (typeof connect.open !== 'function') {{
              throw new Error("Widget não foi inicializado corretamente");
            }}
            
            // Set initial state
            window.pluggyWidgetState = 'initializing';
            
            // Small delay before opening to ensure everything is ready
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Open the widget
            connect.open();
            
            log("✅ Interface de conexão iniciada com sucesso!", "success");
            
          }} catch (openError) {{
            console.error("Error opening widget:", openError);
            log("Erro ao abrir interface: " + (openError?.message || "Erro desconhecido"), "error");
            log("Tente recarregar a página. Se o problema persistir, entre em contato com o suporte.", "warning");
            window.pluggyWidgetState = 'error';
          }}
          
        }} catch (e) {{
          console.error("Widget initialization error:", e);
          updateProgress(currentProgress, "❌ Erro ao inicializar");
          log("Erro ao inicializar widget: " + (e?.message || "Erro desconhecido"), "error", true);
          log("Tente recarregar a página. Se o problema persistir, entre em contato com o suporte.", "warning");
          window.pluggyWidgetState = 'error';
        }}
        
        // Add periodic state monitoring for debugging
        const stateMonitor = setInterval(() => {{
          if (window.pluggyWidgetState && window.pluggyWidgetState !== 'initializing') {{
            console.log("Pluggy Widget State:", window.pluggyWidgetState);
            
            // Clear monitor after widget is opened or encounters error
            if (['opened', 'success', 'error', 'closed'].includes(window.pluggyWidgetState)) {{
              clearInterval(stateMonitor);
            }}
          }}
        }}, 2000);
      }})();
    </script>
    """
    st.components.v1.html(html, height=700, scrolling=False)
    
    # Additional user guidance
    st.markdown("---")
    st.markdown("### 📋 Próximos passos:")
    st.markdown("""
    1. **Selecione seu banco** na lista que aparecerá
    2. **Insira suas credenciais** de acesso ao internet banking
    3. **Autorize a conexão** seguindo as instruções na tela
    4. **Aguarde a confirmação** de que a conta foi conectada com sucesso
    """)
    
    st.info("🔒 **Segurança:** Suas credenciais são processadas diretamente pelo Pluggy usando criptografia de ponta. Não armazenamos suas senhas bancárias.")
    
    # Help section
    with st.expander("❓ Precisa de ajuda?"):
        st.markdown("""
        **Problemas comuns e soluções:**
        
        - **Widget não abre:** Verifique se você tem JavaScript habilitado no navegador
        - **Erro de conexão:** Certifique-se de que suas credenciais bancárias estão corretas
        - **Banco não encontrado:** Verifique se seu banco é suportado pelo Pluggy
        - **Timeout:** Tente recarregar a página se a conexão demorar muito
        
        **Ainda com problemas?** Entre em contato com nosso suporte técnico.
        """)