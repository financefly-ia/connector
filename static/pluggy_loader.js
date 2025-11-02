// static/pluggy_loader.js - Enhanced SDK loader with status messaging
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

  // Show loading status
  updateStatus('🔄 Carregando SDK Pluggy...', 'info');

  // Create and configure script element
  const script = document.createElement("script");
  script.src = "https://cdn.pluggy.ai/pluggy-connect/v2.9.2/pluggy-connect.js";
  
  // Enhanced loading with timeout and error handling
  const timeout = setTimeout(() => {
    updateStatus('⚠️ Timeout ao carregar SDK. Verifique sua conexão.', 'warning');
    setTimeout(() => statusEl.remove(), 5000);
  }, 10000);

  script.onload = () => {
    clearTimeout(timeout);
    updateStatus('✅ SDK Pluggy carregado com sucesso!', 'success');
    
    // Enhanced SDK readiness validation
    let sdkReady = false;
    let attempts = 0;
    const maxAttempts = 10; // 5 seconds total (500ms * 10)
    
    const checkSDKReady = () => {
      attempts++;
      
      if (typeof PluggyConnect !== 'undefined' && PluggyConnect.prototype && PluggyConnect.prototype.open) {
        sdkReady = true;
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
        updateStatus(`🔄 Aguardando SDK... (${attempts}/${maxAttempts})`, 'info');
        setTimeout(checkSDKReady, 500);
      } else {
        updateStatus('❌ SDK não ficou disponível. Recarregue a página.', 'error');
        setTimeout(() => statusEl.remove(), 8000);
      }
    };
    
    // Start checking SDK readiness
    setTimeout(checkSDKReady, 100);
  };

  script.onerror = () => {
    clearTimeout(timeout);
    updateStatus('❌ Erro ao carregar SDK. Tente recarregar a página.', 'error');
    setTimeout(() => statusEl.remove(), 8000);
  };

  // Add script to head
  document.head.appendChild(script);
})();