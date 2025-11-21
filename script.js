'use strict';

(function () {
  const pluggyConfig = Object.freeze({
    clientId: 'cd43d65a-0e1d-4f1a-87f3-1d1c20081450',
    clientSecret: 'efe33d13-e9ba-4104-82b7-f55832a3f660',
    baseUrl: 'https://api.pluggy.ai'
  });

  const refs = {
    form: document.getElementById('connect-form'),
    name: document.getElementById('full-name'),
    email: document.getElementById('user-email'),
    button: document.getElementById('connect-btn'),
    statusChip: document.getElementById('status-chip'),
    itemId: document.getElementById('item-id'),
    itemUpdated: document.getElementById('item-updated'),
    logToggle: document.getElementById('log-toggle'),
    logContainer: document.getElementById('log-container'),
    logStream: document.getElementById('log-stream')
  };

  const uiState = {
    logsVisible: false,
    logCount: 0,
    connectToken: null,
    pluggyInstance: null,
    pluggyReadyPromise: null
  };

  const LOG_LIMIT = 80;

  function setStatus(label, state) {
    refs.statusChip.textContent = label;
    refs.statusChip.dataset.state = state;
  }

  function setLoading(isLoading) {
    refs.button.disabled = isLoading;
    refs.button.textContent = isLoading
      ? 'Gerando token e abrindo widget...'
      : 'Iniciar conexão financeira';
  }

  function formatTime(date) {
    return date.toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  function pushLog(message, level = 'info') {
    uiState.logCount += 1;
    if (refs.logStream.children.length >= LOG_LIMIT) {
      refs.logStream.removeChild(refs.logStream.firstElementChild);
    }

    const entry = document.createElement('li');
    entry.className = `log-entry ${level}`;
    const time = document.createElement('time');
    const now = new Date();
    time.dateTime = now.toISOString();
    time.textContent = formatTime(now);
    const text = document.createElement('span');
    text.textContent = message;
    entry.appendChild(text);
    entry.appendChild(time);
    refs.logStream.appendChild(entry);
    refs.logStream.scrollTop = refs.logStream.scrollHeight;
  }

  function toggleLogs() {
    uiState.logsVisible = !uiState.logsVisible;
    refs.logContainer.hidden = !uiState.logsVisible;
    refs.logToggle.textContent = uiState.logsVisible
      ? 'Ocultar logs'
      : 'Mostrar logs';
    if (uiState.logsVisible && uiState.logCount === 0) {
      pushLog('Logs prontos. Clique no botão para iniciar o fluxo.');
    }
  }

  function ensurePluggyReady() {
    if (uiState.pluggyReadyPromise) {
      return uiState.pluggyReadyPromise;
    }

    uiState.pluggyReadyPromise = new Promise((resolve, reject) => {
      if (window.PluggyConnect) {
        resolve(window.PluggyConnect);
        return;
      }

      let attempts = 0;
      const maxAttempts = 80;
      const interval = setInterval(() => {
        if (window.PluggyConnect) {
          clearInterval(interval);
          resolve(window.PluggyConnect);
        } else if (attempts++ > maxAttempts) {
          clearInterval(interval);
          reject(new Error('SDK Pluggy não carregou a tempo.'));
        }
      }, 125);
    });

    return uiState.pluggyReadyPromise;
  }

  async function authenticatePluggy() {
    pushLog('Autenticando com Pluggy...');
    const response = await fetch(`${pluggyConfig.baseUrl}/auth`, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        clientId: pluggyConfig.clientId,
        clientSecret: pluggyConfig.clientSecret
      })
    });

    if (!response.ok) {
      const info = await response.text();
      throw new Error(`Falha na autenticação (${response.status}): ${info}`);
    }
    const data = await response.json();
    if (!data.apiKey) {
      throw new Error('API key não retornada pelo Pluggy.');
    }
    pushLog('API key recebida com sucesso.', 'success');
    return data.apiKey;
  }

  async function requestConnectToken(apiKey, userId) {
    pushLog('Gerando connect token...');
    const response = await fetch(`${pluggyConfig.baseUrl}/connect_token`, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-API-KEY': apiKey
      },
      body: JSON.stringify(
        userId ? { clientUserId: userId } : {}
      )
    });

    if (!response.ok) {
      const info = await response.text();
      throw new Error(`Erro ao gerar token (${response.status}): ${info}`);
    }

    const data = await response.json();
    if (!data.accessToken) {
      throw new Error('Pluggy não retornou accessToken.');
    }
    uiState.connectToken = data.accessToken;
    pushLog('Connect token pronto.', 'success');
    return data.accessToken;
  }

  function deriveUserId() {
    const email = refs.email.value.trim();
    if (email) {
      return email.toLowerCase();
    }
    return `financefly-web-${Date.now()}`;
  }

  function decorateItemId(itemId) {
    refs.itemId.textContent = itemId;
    refs.itemId.classList.add('highlight');
    refs.itemUpdated.textContent = `Última atualização ${formatTime(
      new Date()
    )}`;
  }

  function instantiatePluggy(PluggyConnect, options) {
    if (PluggyConnect && typeof PluggyConnect.create === 'function') {
      return Promise.resolve(PluggyConnect.create(options));
    }
    return Promise.resolve(new PluggyConnect(options));
  }

  function openPluggyInstance(instance, PluggyConnect) {
    if (instance && typeof instance.open === 'function') {
      instance.open();
      return instance;
    }
    if (PluggyConnect && typeof PluggyConnect.open === 'function') {
      PluggyConnect.open();
      return PluggyConnect;
    }
    throw new Error('SDK Pluggy indisponível: método open() não encontrado.');
  }

  function openPluggyWidget(token, metadata) {
    return ensurePluggyReady().then((PluggyConnect) => {
      pushLog('Abrindo widget Pluggy...');
      const options = {
        connectToken: token,
        includeSandbox: false,
        language: 'pt',
        theme: 'dark',
        userMetadata: metadata,
        onOpen: () => {
          setStatus('Widget aberto', 'success');
          pushLog('Widget aberto.', 'success');
        },
        onClose: () => pushLog('Widget fechado.'),
        onError: (err) => {
          pushLog(`Widget erro: ${err?.message || err}`, 'error');
          setStatus('Erro no widget', 'error');
        },
        onSuccess: (data) => {
          pushLog('Conta conectada e itemId retornado.', 'success');
          if (data?.itemId) {
            decorateItemId(data.itemId);
            setStatus('Item conectado', 'success');
          }
        }
      };

      return instantiatePluggy(PluggyConnect, options)
        .then((instance) => {
          const activeInstance = openPluggyInstance(instance, PluggyConnect);
          uiState.pluggyInstance = activeInstance;
          return activeInstance;
        })
        .catch((error) => {
          pushLog(`Falha ao inicializar widget: ${error?.message || error}`, 'error');
          setStatus('Erro: verifique os logs', 'error');
          throw error;
        });
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setStatus('Gerando token...', 'loading');

    try {
      const userId = deriveUserId();
      const apiKey = await authenticatePluggy();
      const connectToken = await requestConnectToken(apiKey, userId);
      const metadata = {
        name: refs.name.value.trim() || undefined,
        email: refs.email.value.trim() || undefined
      };
      await openPluggyWidget(connectToken, metadata);
    } catch (error) {
      console.error(error);
      pushLog(error.message || 'Erro inesperado', 'error');
      setStatus('Erro: verifique os logs', 'error');
    } finally {
      setLoading(false);
    }
  }

  function init() {
    if (refs.form) {
      refs.form.addEventListener('submit', handleSubmit);
    }
    if (refs.logToggle) {
      refs.logToggle.addEventListener('click', toggleLogs);
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
