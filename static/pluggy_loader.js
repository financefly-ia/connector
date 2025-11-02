// static/pluggy_loader.js - Enhanced SDK loader with synchronous execution and fallback
(function() {
  // Create status display if not exists
  let statusEl = document.getElementById('pluggy-loader-status');
  if (!statusEl) {
    statusEl = document.createElement('div');
    statusEl.id = 'pluggy-loader-status';
    statusEl.style.cssText = `
      position: fixed; 
      top: 20px; 
      right: 20px; 
      background: #f8f9fa; 
      border: 1px solid #dee2e6; 
      border-radius: 8px; 
      padding: 12px 16px; 
      font-family: system-ui, -apple-system, sans-serif; 
      font-size: 14px; 
      box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
      z-index: 10000;
      max-width: 300px;
    `;
    document.body.appendChild(statusEl);
  }

  function updateStatus(message, type = 'info') {
    const colors = {
      info: { bg: '#d1ecf1', border: '#bee5eb', text: '#0c5460' },
      success: { bg: '#d4edda', border: '#c3e6cb', text: '#155724' },
      error: { bg: '#f8d7da', border: '#f5c6cb', text: '#721c24' },
      warning: { bg: '#fff3cd', border: '#ffeaa7', text: '#856404' }
    };
    
    const color = colors[type] || colors.info;
    statusEl.style.backgroundColor = color.bg;
    statusEl.style.borderColor = color.border;
    statusEl.style.color = color.text;
    statusEl.innerHTML = message;
  }

  let sdkLoadAttempts = 0;
  const maxLoadAttempts = 2; // Allow one retry
  
  function loadSDK() {
    sdkLoadAttempts++;
    
    // Show loading status
    updateStatus(`🔄 Carregando SDK Pluggy... (tentativa ${sdkLoadAttempts}/${maxLoadAttempts})`, 'info');

    // Create and configure script element - NO async/defer for synchronous execution
    const script = document.createElement("script");
    script.src = "https://cdn.pluggy.ai/pluggy-connect/v2.9.2/pluggy-connect.js";
    // Explicitly ensure no async/defer attributes
    script.async = false;
    script.defer = false;
    
    // 10-second timeout for SDK availability
    const sdkTimeout = setTimeout(() => {
      console.log(`SDK timeout after 10 seconds (attempt ${sdkLoadAttempts})`);
      
      if (typeof window.PluggyConnect === 'undefined' && sdkLoadAttempts < maxLoadAttempts) {
        updateStatus('⚠️ SDK não carregou em 10s. Tentando novamente...', 'warning');
        
        // Remove failed script
        if (script.parentNode) {
          script.parentNode.removeChild(script);
        }
        
        // Retry after 1 second
        setTimeout(() => {
          loadSDK();
        }, 1000);
      } else if (typeof window.PluggyConnect === 'undefined') {
        updateStatus('❌ SDK falhou após todas as tentativas. Recarregue a página.', 'error');
        setTimeout(() => statusEl.remove(), 8000);
      }
    }, 10000);

    script.onload = () => {
      console.log(`SDK script loaded successfully (attempt ${sdkLoadAttempts})`);
      updateStatus('✅ SDK script carregado. Verificando execução...', 'success');
      
      // Enhanced SDK readiness validation with more frequent checks
      let sdkReady = false;
      let attempts = 0;
      const maxAttempts = 20; // 10 seconds total (500ms * 20)
      
      const checkSDKReady = () => {
        attempts++;
        
        if (typeof window.PluggyConnect !== 'undefined' && 
            window.PluggyConnect.prototype && 
            typeof window.PluggyConnect.prototype.open === 'function') {
          
          clearTimeout(sdkTimeout);
          sdkReady = true;
          console.log(`SDK ready after ${attempts * 500}ms (load attempt ${sdkLoadAttempts})`);
          updateStatus(`✅ SDK pronto após ${attempts * 500}ms`, 'success');
          window.dispatchEvent(new Event("pluggy_loaded"));
          
          // Hide status after 3 seconds
          setTimeout(() => {
            if (statusEl && statusEl.parentNode) {
              statusEl.style.transition = 'opacity 0.3s ease';
              statusEl.style.opacity = '0';
              setTimeout(() => statusEl.remove(), 300);
            }
          }, 3000);
          
        } else if (attempts < maxAttempts) {
          updateStatus(`🔄 Aguardando execução SDK... (${attempts}/${maxAttempts})`, 'info');
          setTimeout(checkSDKReady, 500);
        } else {
          console.log(`SDK execution check failed after ${maxAttempts} attempts`);
          // Don't clear timeout here - let the 10s timeout handle retry logic
        }
      };
      
      // Start checking SDK readiness immediately
      checkSDKReady();
    };

    script.onerror = (error) => {
      clearTimeout(sdkTimeout);
      console.error(`SDK script loading error (attempt ${sdkLoadAttempts}):`, error);
      
      if (sdkLoadAttempts < maxLoadAttempts) {
        updateStatus('⚠️ Erro ao carregar script. Tentando novamente...', 'warning');
        setTimeout(() => {
          loadSDK();
        }, 1000);
      } else {
        updateStatus('❌ Erro ao carregar SDK após todas as tentativas.', 'error');
        setTimeout(() => statusEl.remove(), 8000);
      }
    };

    // Add script to head for synchronous loading
    document.head.appendChild(script);
  }

  // Start initial SDK load
  loadSDK();
})();