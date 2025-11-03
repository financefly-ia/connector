// ===========================================================
// Financefly / Pluggy SDK Loader v2.0
// ===========================================================
// Compatível com SDK local (/static/pluggy-connect.js)
// Inclui logs visuais no Streamlit e fallback automático
// ===========================================================

(async function pluggyLoader() {
  const MAX_WAIT = 10000; // 10s para SDK estar pronto
  const MAX_RETRIES = 3;  // tentativas para abrir widget
  const RETRY_INTERVAL = 1500; // ms

  // Elemento de status visual (para logs no front)
  function updateStatus(msg, type = "info") {
    let container = document.getElementById("pluggy-status");
    if (!container) {
      container = document.createElement("div");
      container.id = "pluggy-status";
      container.style.cssText = `
        margin: 10px 0;
        padding: 10px;
        border-radius: 8px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
        background: #1E1E2F;
        color: #fff;
        line-height: 1.6;
      `;
      document.body.prepend(container);
    }

    const colorMap = {
      info: "#2196F3",
      success: "#4CAF50",
      warn: "#FFC107",
      error: "#F44336"
    };
    const iconMap = {
      info: "🔄",
      success: "✅",
      warn: "⚠️",
      error: "❌"
    };

    const line = document.createElement("div");
    line.innerHTML = `<span style="color:${colorMap[type]}">${iconMap[type]}</span> ${msg}`;
    container.appendChild(line);
    console.log(`[PluggyLoader] ${msg}`);
  }

  // Remove instâncias antigas
  if (window.PluggyConnect) {
    updateStatus("Limpando instância antiga do PluggyConnect...", "warn");
    delete window.PluggyConnect;
  }

  // Inicia carregamento
  updateStatus("Carregando SDK Pluggy v2.9.2...", "info");

  // Cria a tag script apontando para o SDK local
  const script = document.createElement("script");
  script.src = "/static/pluggy-connect.js";
  script.type = "text/javascript";
  script.async = true;

  let sdkLoaded = false;
  let widgetReady = false;

  // Timeout se o SDK não carregar
  const timeout = setTimeout(() => {
    if (!sdkLoaded) {
      updateStatus("Erro ao carregar SDK: SDK não ficou disponível após 10 segundos", "error");
    }
  }, MAX_WAIT);

  // Quando o SDK carregar
  script.onload = () => {
    sdkLoaded = true;
    clearTimeout(timeout);
    if (window.PluggyConnect) {
      updateStatus("✅ SDK Pluggy carregado com sucesso!", "success");
      waitForSDKReady();
    } else {
      updateStatus("❌ SDK carregado, mas PluggyConnect não disponível.", "error");
    }
  };

  script.onerror = () => {
    clearTimeout(timeout);
    updateStatus("❌ Falha ao carregar o arquivo pluggy-connect.js", "error");
  };

  document.body.appendChild(script);

  // Aguarda SDK estar pronto
  async function waitForSDKReady() {
    updateStatus("🔍 Verificando disponibilidade do SDK...", "info");

    let attempts = 0;
    while (attempts < 20) {
      if (window.PluggyConnect) {
        updateStatus("✅ SDK pronto para inicialização.", "success");
        initializeWidget();
        return;
      }
      attempts++;
      updateStatus(`🔄 Aguardando SDK... (tentativa ${attempts}/20)`);
      await new Promise(res => setTimeout(res, 500));
    }

    updateStatus("❌ SDK não ficou disponível após múltiplas tentativas.", "error");
  }

  // Inicializa widget Pluggy
  async function initializeWidget() {
    updateStatus("⚙️ Inicializando widget PluggyConnect...", "info");

    const token = window.localStorage.getItem("pluggy_connect_token");
    if (!token) {
      updateStatus("⚠️ Nenhum token encontrado. Gere um novo token antes de continuar.", "warn");
      return;
    }

    let retries = 0;
    while (retries < MAX_RETRIES) {
      try {
        const pluggy = new window.PluggyConnect({
          connectToken: token,
          onOpen: () => updateStatus("🔗 Widget aberto com sucesso!", "success"),
          onClose: () => updateStatus("❎ Widget fechado pelo usuário.", "warn"),
          onError: (error) => updateStatus(`❌ Erro no widget: ${error.message}`, "error"),
          onSuccess: (itemData) => {
            updateStatus("✅ Conexão concluída com sucesso!", "success");
            console.log("Item conectado:", itemData);
          }
        });

        pluggy.open();
        widgetReady = true;
        updateStatus("🎉 Widget inicializado corretamente!", "success");
        return;
      } catch (err) {
        retries++;
        updateStatus(`❌ Erro ao abrir widget (${err.message}) — tentativa ${retries}/${MAX_RETRIES}`, "error");
        await new Promise(res => setTimeout(res, RETRY_INTERVAL));
      }
    }

    if (!widgetReady) {
      updateStatus("❌ Falha ao inicializar o widget após múltiplas tentativas.", "error");
    }
  }
})();
