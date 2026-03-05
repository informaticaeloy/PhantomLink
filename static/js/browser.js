// static/js/browser.js
document.addEventListener('DOMContentLoaded', function() {
    const frame = document.getElementById('browser-frame');
    const input = document.getElementById('url-input');
    const loading = document.getElementById('loading');
    const errorMsg = document.getElementById('error-message');
    const currentUrlDisplay = document.getElementById('current-url-display');
    const ipAddress = document.getElementById('ip-address');
    const pingValue = document.getElementById('ping-value');

    let history = [];
    let historyIndex = -1;
    let updateInterval = null;

    // Inicializar historial
    function addToHistory(url) {
        history.push(url);
        historyIndex = history.length - 1;
    }

    // Actualizar información de red
    async function updateNetworkInfo(url) {
        if (!url) return;

        try {
            const response = await fetch('/api/network-info?url=' + encodeURIComponent(url));
            const data = await response.json();

            if (data.ip && data.ip !== 'N/A') {
                ipAddress.textContent = data.ip;
                pingValue.textContent = data.ping;
            } else {
                ipAddress.textContent = 'No disponible';
                pingValue.textContent = '-';
            }
        } catch (e) {
            console.log('Error obteniendo info de red:', e);
            ipAddress.textContent = 'Error';
            pingValue.textContent = '-';
        }
    }

    // Actualizar URL cuando el iframe carga
    frame.addEventListener('load', function() {
        loading.style.display = 'none';
        try {
            let frameUrl = frame.contentWindow.location.href;
            if (frameUrl && frameUrl.includes('/proxy/?url=')) {
                let urlPart = frameUrl.split('/proxy/?url=')[1];
                if (urlPart) {
                    let decodedUrl = decodeURIComponent(urlPart);
                    input.value = decodedUrl;
                    currentUrlDisplay.textContent = decodedUrl;

                    // Actualizar info de red
                    updateNetworkInfo(decodedUrl);

                    // Actualizar cada 30 segundos
                    if (updateInterval) clearInterval(updateInterval);
                    updateInterval = setInterval(() => updateNetworkInfo(decodedUrl), 30000);
                }
            }
        } catch(e) {
            console.log('No se puede acceder al iframe');
        }
    });

    // Navegar a URL
    window.navigateToUrl = function() {
        let url = input.value.trim();
        if (!url) return;

        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            url = 'https://' + url;
        }

        loading.style.display = 'block';
        errorMsg.style.display = 'none';

        try {
            new URL(url); // Validar URL
            frame.src = '/proxy/?url=' + encodeURIComponent(url);
            addToHistory(frame.src);
        } catch(e) {
            showError('URL inválida: ' + url);
        }
    };

    // Recargar página
    window.reloadPage = function() {
        if (frame.src) {
            loading.style.display = 'block';
            frame.src = frame.src;
        }
    };

    // Historial
    window.historyBack = function() {
        if (historyIndex > 0) {
            historyIndex--;
            frame.src = history[historyIndex];
            loading.style.display = 'block';
        }
    };

    window.historyForward = function() {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            frame.src = history[historyIndex];
            loading.style.display = 'block';
        }
    };

    // Página de inicio
    window.homePage = function() {
        input.value = 'https://www.google.com';
        navigateToUrl();
    };

    // Cerrar sesión
    window.logout = function() {
        window.location.href = '/logout';
    };

    // Mostrar error
    function showError(msg) {
        errorMsg.textContent = msg;
        errorMsg.style.display = 'block';
        loading.style.display = 'none';
        setTimeout(() => {
            errorMsg.style.display = 'none';
        }, 5000);
    }

    // Enter key
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') navigateToUrl();
    });

    // Cargar info inicial
    updateNetworkInfo('https://www.google.com');
});