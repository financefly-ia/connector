// ===========================================================
// Financefly / Pluggy SDK Loader v2.0.1 (Render Safe)
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
    log("Iniciando carregamento do SDK Pluggy...");

    // Limpa versões anteriores
    if (window.PluggyConnect) {
      log("Instância anterior detectada, limpando...");
      delete window.PluggyConnect;
    }

    // Adiciona script via fetch -> blob (bypass CSP)
    const sdkUrl = "/static/pluggy-connect.js";
    const sdkResponse = await fetch(sdkUrl);
    const sdkCode = await sdkResponse.text();

    const blob = new Blob([sdkCode + "\n//# sourceURL=pluggy-connect.js"], { type: "application/javascript" });
    const sdkScript = document.createElement("script");
    sdkScript.src = URL.createObjectURL(blob);
    document.body.appendChild(sdkScript);

    log("SDK carregado do blob, aguardando PluggyConnect...");

    // Espera até 10s pra garantir inicialização
    let retries = 0;
    const maxRetries = 20;
    while (typeof window.PluggyConnect === "undefined" && retries < maxRetries) {
      retries++;
      log(`Aguardando PluggyConnect... (tentativa ${retries}/${maxRetries})`);
      await new Promise(res => setTimeout(res, 500));
    }

    if (typeof window.PluggyConnect === "undefined") {
      log("❌ PluggyConnect não disponível após 10 segundos.", "error");
      return;
    }

    log("✅ SDK Pluggy disponível! Inicializando widget...", "success");

    // Obtém token do localStorage
    const token = window.localStorage.getItem("pluggy_connect_token");
    if (!token) {
      log("⚠️ Nenhum token encontrado. Gere o token antes de abrir o widget.", "warn");
      return;
    }

    // Inicializa o widget
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

  } catch (err) {
    log(`❌ Erro fatal no carregamento do SDK: ${err.message}`, "error");
  }
})();
