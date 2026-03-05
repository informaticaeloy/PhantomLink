![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3.x-black?logo=flask)
![License](https://img.shields.io/badge/License-MIT-green?logo=opensourceinitiative&logoColor=white)
![Code Style](https://img.shields.io/badge/Code%20Style-PEP%208-ff69b4?logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/Dependencies-requests%20%7C%20beautifulsoup4%20%7C%20lxml-blue)
![GitHub Stars](https://img.shields.io/github/stars/YOUR_USERNAME/phantomlink?style=social)
![GitHub Forks](https://img.shields.io/github/forks/YOUR_USERNAME/phantomlink?style=social)
![GitHub Issues](https://img.shields.io/github/issues/YOUR_USERNAME/phantomlink)
![GitHub PRs](https://img.shields.io/github/issues-pr/YOUR_USERNAME/phantomlink)
![Python Version](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)
![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

# PhantomLink

Plataforma de navegación controlada basada en Flask con proxy, inspección de URLs, registro de peticiones y diagnósticos de red.

PhantomLink proporciona un entorno de navegación web controlado diseñado para análisis de seguridad, navegación controlada e inspección de tráfico. Permite a los usuarios navegar por sitios web externos a través de un proxy interno mientras recopila información de diagnóstico y registros.

----------------------------------------------------------------------- 

<img width="400" height="400" alt="PhantomLink_logo" src="https://github.com/user-attachments/assets/130347ab-8e86-418d-8610-3d37fa8b1d6d" />

# Capturas de Pantalla

## Configuración de Usuarios
[INSERTAR CAPTURA DE PANTALLA DE LA CONFIGURACIÓN DE USUARIOS AQUÍ]

## Configuración de URLs Permitidas
[INSERTAR CAPTURA DE PANTALLA DE LA CONFIGURACIÓN DE URLs PERMITIDAS AQUÍ]

## Logs del Sistema
[INSERTAR CAPTURA DE PANTALLA DE LOS LOGS DEL SISTEMA AQUÍ]

# Usuarios por Defecto

El sistema incluye los siguientes usuarios preconfigurados:

| Usuario | Contraseña | Rol | Descripción |
|---------|------------|-----|-------------|
| admin | admin123 | Administrador | Acceso completo a todas las funcionalidades |
| usuario | usuario123 | Usuario estándar | Acceso solo a navegación y diagnóstico |

----------------------------------------------------------------------- 

# Características

- Navegación web por proxy
- Inspección de URLs
- Registro de peticiones
- Diagnóstico de red (IP, latencia)
- Control de acceso y autenticación
- Gestión de sesiones de usuario
- Registro de actividad
- Monitorización de errores
- Reescritura de HTML para compatibilidad con iframe
- Historial de navegación interno
- Interfaz de navegador embebida
- Entorno de navegación controlado

----------------------------------------------------------------------- 

# Arquitectura

PhantomLink actúa como un proxy intermedio entre el usuario y los sitios web externos.

    User Browser
          │
          ▼
    PhantomLink (Flask)
          │
          ▼
    External Website

Todas las peticiones pasan por el proxy y son opcionalmente registradas para análisis.

----------------------------------------------------------------------- 

# Flujo de Navegación Interna

    User
     │
     ▼
    Browser Interface
     │
     ▼
    URL Input
     │
     ▼
    /proxy/?url=https://example.com
     │
     ▼
    Flask Backend
     │
     ▼
    requests.get()
     │
     ▼
    HTML Processing (BeautifulSoup)
     │
     ▼
    Resource rewriting
     │
     ▼
    Rendered inside iframe

----------------------------------------------------------------------- 

# Tecnologías

- Python
- Flask
- Requests
- BeautifulSoup
- lxml
- HTML
- CSS
- JavaScript

----------------------------------------------------------------------- 

# Instalación

Clona el repositorio:

    git clone https://github.com/YOUR_USERNAME/phantomlink.git
    cd phantomlink

Crea un entorno virtual:

Linux / macOS

    python3 -m venv venv
    source venv/bin/activate

Windows

    python -m venv venv
    venv\Scripts\activate

Instala las dependencias:

    pip install -r requirements.txt

Ejemplo de requirements.txt:

    Flask
    requests
    beautifulsoup4
    lxml

Ejecuta la aplicación:

    python main.py

El servidor se iniciará en:

    http://127.0.0.1:5000

----------------------------------------------------------------------- 

# Uso

Abre tu navegador y accede a:

    http://localhost:5000

Inicia sesión con las credenciales por defecto:

    Administrador: admin / admin123
    Usuario estándar: usuario / usuario123

Introduce una URL en la barra de navegación:

    https://example.com

La petición será procesada a través del proxy interno:

    /proxy/?url=https://example.com

La página será recuperada por el backend y renderizada dentro del navegador embebido.

----------------------------------------------------------------------- 

# Mecanismo del Proxy

El endpoint del proxy realiza las siguientes operaciones:

1. Recibe la URL solicitada
2. Envía una petición HTTP usando la librería requests
3. Recupera el HTML remoto
4. Lo parsea con BeautifulSoup
5. Reescribe las URLs de los recursos (imágenes, scripts, CSS)
6. Devuelve el HTML modificado al navegador

Esto permite eludir algunas restricciones como:

- X-Frame-Options
- frame-ancestors
- Restricciones de embedding

Ten en cuenta que algunos sitios web pueden bloquear el acceso por proxy.

----------------------------------------------------------------------- 

# Diagnóstico de Red

PhantomLink incluye diagnóstico de red básico para URLs inspeccionadas.

Características incluidas:

- Resolución DNS
- Identificación de dirección IP
- Medición de latencia
- Prueba de conectividad

Ejemplo de flujo de diagnóstico:

    URL
     │
     ▼
    DNS resolution
     │
     ▼
    IP detection
     │
     ▼
    Latency measurement

----------------------------------------------------------------------- 

# Registro (Logging)

La plataforma registra la actividad de navegación para fines de análisis.

Datos registrados:

- URLs solicitadas
- Marcas de tiempo
- Códigos de respuesta
- Errores de conexión
- Diagnóstico de red

Los logs pueden utilizarse para:

- Inspección de tráfico
- Depuración
- Investigación
- Monitorización del entorno controlado

----------------------------------------------------------------------- 

# Pruebas de Conectividad

Para verificar si el entorno de alojamiento puede alcanzar un sitio web específico, ejecuta:

    curl -I https://example.com

o

    wget --spider https://example.com

Ejemplo de prueba en Python:

    import requests

    try:
        r = requests.get("https://example.com", timeout=10)
        print("Status:", r.status_code)
    except Exception as e:
        print("Connection error:", e)

----------------------------------------------------------------------- 

# Limitaciones Conocidas

Algunos sitios web pueden no cargarse correctamente debido a:

- Políticas CSP estrictas
- Bloqueo de proxies
- Restricciones de red del proveedor de alojamiento
- Uso de WebSockets
- Frameworks JavaScript complejos

Además, algunos proveedores de alojamiento pueden forzar el tráfico saliente a través de proxies internos.

----------------------------------------------------------------------- 

# Despliegue

PhantomLink puede ejecutarse en múltiples entornos:

- Máquina local de desarrollo
- Servidores VPS
- Entornos contenedorizados
- Plataformas cloud
- Replit

Para entornos de producción, se recomienda utilizar un servidor WSGI.

Ejemplo usando Waitress:

    pip install waitress

Ejecutar:

    waitress-serve --port=8000 main:app

----------------------------------------------------------------------- 

# Estructura del Proyecto

    phantomlink/
    │
    ├── main.py
    ├── proxy.py
    ├── auth.py
    ├── config.py
    ├── requirements.txt
    │
    ├── templates/
    │   ├── index.html
    │   ├── login.html
    │   └── admin/
    │       ├── users.html
    │       ├── urls.html
    │       └── logs.html
    │
    ├── static/
    │   ├── css/
    │   ├── js/
    │   └── images/
    │
    └── README.md

----------------------------------------------------------------------- 

# Roadmap

Mejoras futuras pueden incluir:

- Inspección avanzada de tráfico
- Análisis de cabeceras de respuesta
- Huella digital de tecnologías
- Replay de peticiones
- Módulos de análisis de seguridad
- Optimización del rendimiento del proxy

----------------------------------------------------------------------- 

# Aviso Legal

Este proyecto está destinado a:

- Fines educativos
- Investigación de seguridad
- Entornos controlados
- Pruebas y experimentación

No utilices esta herramienta para violar las políticas o la seguridad de sistemas de terceros.

----------------------------------------------------------------------- 

# Licencia

MIT License
