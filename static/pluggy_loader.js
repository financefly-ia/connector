// ===========================================================
// Financefly / Pluggy SDK Loader (Render + CDN Safe)
// ===========================================================

(async function loadPluggySDK() {
  const log = (msg, type = "info") => {
    const colors = {
      info: "color:#2196F3",
      success: "color:#4CAF50",
      warn: "color:#FF9800",
      error: "color:#F44336"
    };
    console.log(`%c[PluggyLoader] ${msg}`, colors[type] || colors.info);
  };

  try {
    log("Iniciando carregamento do SDK Pluggy (via CDN latest)...");

    // Remove versões antigas
    if (window.PluggyConnect) {
      log("Removendo instância anterior...");
      delete window.PluggyConnect;
    }

    // Cria o elemento script com a versão mais recente
    const sdkScript = document.createElement("script");
    sdkScript.src = "https://cdn.pluggy.ai/pluggy-connect/latest/pluggy-connect.js";
    sdkScript.async = true;

    sdkScript.onload = async () => {
      log("✅ SDK Pluggy carregado com sucesso!", "success");

      // Espera até 10s pra garantir que o objeto esteja pronto
      let retries = 0;
      const maxRetries = 20;
      while (typeof window.PluggyConnect === "undefined" && retries < maxRetries) {
        retries++;
        log(`Aguardando PluggyConnect... (tentativa ${retries}/${maxRetries})`);
        await new Promise(res => setTimeout(res, 500));
      }

      if (typeof window.PluggyConnect === "undefined") {
        log("❌ SDK não ficou disponível após 10 segundos.", "error");
        return;
      }

      log("✅ SDK disponível! Inicializando widget...", "success");

      const token = window.localStorage.getItem("pluggy_connect_token");
      if (!token) {
        log("⚠️ Nenhum token encontrado. Gere o token antes de abrir o widget.", "warn");
        return;
      }

      const pluggy = new window.PluggyConnect({
        connectToken: token,
        onOpen: () => log("🔗 Widget aberto com sucesso!", "success"),
        onClose: () => log("❎ Widget fechado."),
        onError: (err) => log(`❌ Erro no widget: ${err.message}`, "error"),
        onSuccess: (data) => {
          log("✅ Conexão concluída com sucesso!", "success");
          console.log("Item conectado:", data);
        }
      });

      pluggy.open();
    };

    sdkScript.onerror = () => {
      log("❌ Falha ao carregar o SDK da Pluggy (erro de rede ou CSP).", "error");
    };

    document.head.appendChild(sdkScript);

  } catch (err) {
    log(`❌ Erro fatal no carregamento do SDK: ${err.message}`, "error");
  }
})();
