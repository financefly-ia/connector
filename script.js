'use strict';

(function () {
  const refs = {
    form: document.getElementById('connect-form'),
    name: document.getElementById('user-name'),
    email: document.getElementById('user-email'),
    button: document.getElementById('connect-btn'),
    statusChip: document.getElementById('status-chip'),
    itemId: document.getElementById('item-id'),
    itemUpdated: document.getElementById('item-updated'),
    logToggle: document.getElementById('log-toggle'),
    logContainer: document.getElementById('log-container'),
    logStream: document.getElementById('log-stream'),
    successModal: document.getElementById('success-modal'),
    successDismiss: document.getElementById('success-dismiss'),
    ctaConnect: document.getElementById('cta-connect'),
    ctaHow: document.getElementById('cta-how'),
    howSection: document.getElementById('how-it-works')
  };

  const uiState = {
    logsVisible: false,
    logCount: 0,
    connectToken: null,
    pluggyInstance: null,
    pluggyReadyPromise: null,
    currentClientUserId: null
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
    if (refs.logToggle) {
      refs.logToggle.textContent = uiState.logsVisible
        ? 'Ocultar logs'
        : 'Mostrar logs';
    }
    if (uiState.logsVisible && uiState.logCount === 0) {
      pushLog('Logs prontos. Clique no botão para iniciar o fluxo.');
    }
  }

  function deriveUserId() {
    const email = refs.email.value.trim();
    if (email) {
      return email.toLowerCase();
    }
    return `financefly-web-${Date.now()}`;
  }

  async function getConnectToken(clientUserId, itemId) {
    const response = await fetch('/api/connect-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clientUserId, itemId })
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Erro ao gerar token (${response.status}): ${text}`);
    }

    const data = await response.json();
    if (!data.accessToken) {
      throw new Error('Token indisponível no backend.');
    }
    return data.accessToken;
  }

  async function saveItem(payload) {
    const response = await fetch('/api/save-item', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Erro ao salvar item (${response.status}): ${text}`);
    }

    return response.json();
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

  function showSuccessModal() {
    if (refs.successModal) {
      refs.successModal.classList.add('visible');
      refs.successModal.setAttribute('aria-hidden', 'false');
    }
  }

  function hideSuccessModal() {
    if (refs.successModal) {
      refs.successModal.classList.remove('visible');
      refs.successModal.setAttribute('aria-hidden', 'true');
    }
  }

  async function openPluggyWidget(token, metadata) {
    try {
      const PluggyConnect = await ensurePluggyReady();
      pushLog('Abrindo widget Pluggy...');

      const widget = new PluggyConnect({
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
        onSuccess: async (data) => {
          console.log('🔍 PLUGGY SUCCESS DATA:', JSON.stringify(data, null, 2));
          pushLog('Conta conectada e itemId retornado.', 'success');
          try {
            const clientUserId = uiState.currentClientUserId || deriveUserId();
            const itemId =
              data?.item?.id ||
              data?.itemId ||
              data?.item?.itemId ||
              data?.id ||
              null;
            const institutionId =
              data?.institution?.id ||
              data?.item?.institution?.id ||
              data?.item?.institutionId ||
              data?.connector?.id ||
              data?.item?.connector?.id ||
              null;
            const institutionName =
              data?.institution?.name ||
              data?.institution?.providerName ||
              data?.institution?.fullName ||
              data?.item?.institution?.name ||
              data?.item?.institution?.fullName ||
              data?.item?.institution?.providerName ||
              data?.item?.institutionName ||
              data?.connector?.name ||
              data?.item?.connector?.name ||
              null;

            if (itemId) {
              refs.itemId.textContent = itemId;
              refs.itemId.classList.add('highlight');
              refs.itemUpdated.textContent = `Última atualização ${formatTime(
                new Date()
              )}`;
              setStatus('Item conectado', 'success');
            }

            await saveItem({
              clientUserId,
              itemId,
              userName: refs.name.value.trim(),
              userEmail: refs.email.value.trim(),
              institutionId,
              institutionName
            });

            pushLog('Dados enviados ao backend.', 'success');
            showSuccessModal();
          } catch (error) {
            console.error(error);
            pushLog(`Erro ao salvar item: ${error.message || error}`, 'error');
          }
        }
      });

      uiState.pluggyInstance = widget;
      await widget.init();
      await widget.open();
      return widget;
    } catch (error) {
      pushLog(`Falha ao inicializar widget: ${error?.message || error}`, 'error');
      setStatus('Erro: verifique os logs', 'error');
      throw error;
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setStatus('Gerando token...', 'loading');

    try {
      const clientUserId = deriveUserId();
      uiState.currentClientUserId = clientUserId;
      pushLog('Solicitando token ao backend...');
      const connectToken = await getConnectToken(clientUserId);
      uiState.connectToken = connectToken;
      pushLog('Connect token pronto.', 'success');

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
    if (refs.successDismiss) {
      refs.successDismiss.addEventListener('click', hideSuccessModal);
    }
    if (refs.ctaConnect) {
      refs.ctaConnect.addEventListener('click', (e) => {
        e.preventDefault();
        if (refs.form) {
          refs.form.scrollIntoView({ behavior: 'smooth', block: 'center' });
          setTimeout(() => refs.button?.click(), 400);
        }
      });
    }
    if (refs.ctaHow && refs.howSection) {
      refs.ctaHow.addEventListener('click', (e) => {
        e.preventDefault();
        refs.howSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
