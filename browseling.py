#!/usr/bin/env python3
"""
Proxy Web Profesional con Administración de Usuarios, URLs y Logs de navegación
"""

from flask import Flask, request, Response, render_template, session, redirect, url_for, flash, jsonify, send_file
import requests
from urllib.parse import urlparse, unquote
import logging
import os
import re
from functools import wraps
import hashlib
import secrets
from datetime import datetime, timedelta
import csv
import socket
import time
import json
import ipaddress
import threading
from collections import deque
from config import Config
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__,
            template_folder=Config.TEMPLATES_DIR,
            static_folder=Config.STATIC_DIR)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# SISTEMA DE LOGS DE NAVEGACIÓN
# ============================================

class NavigationLogger:
    """Sistema de logs de navegación por usuario"""

    def __init__(self, logs_dir):
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)
        self.user_logs = {}
        self.lock = threading.Lock()

    def _get_user_log_file(self, username, date=None):
        """Obtener el archivo de log para un usuario y fecha"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        user_dir = os.path.join(self.logs_dir, username)
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, f'navigation_{date}.log')

    def _rotate_if_needed(self, filepath):
        """Rotar archivo de log si es necesario"""
        if os.path.exists(filepath) and os.path.getsize(filepath) > Config.MAX_LOG_SIZE:
            # Renombrar archivos existentes
            for i in range(Config.MAX_LOG_FILES - 1, 0, -1):
                old_file = f"{filepath}.{i}"
                new_file = f"{filepath}.{i + 1}" if i < Config.MAX_LOG_FILES - 1 else f"{filepath}.{Config.MAX_LOG_FILES}"
                if os.path.exists(old_file):
                    os.rename(old_file, new_file)
            # Rotar el actual
            os.rename(filepath, f"{filepath}.1")

    def log_navigation(self, username, url, ip=None, status='success', error=None):
        """Registrar una navegación de un usuario"""
        with self.lock:
            try:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'username': username,
                    'url': url,
                    'ip': ip,
                    'status': status,
                    'error': error,
                    'user_agent': request.headers.get('User-Agent', 'Unknown') if request else 'Unknown'
                }

                log_file = self._get_user_log_file(username)
                self._rotate_if_needed(log_file)

                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

                # Mantener en memoria los últimos 100 logs por usuario
                if username not in self.user_logs:
                    self.user_logs[username] = deque(maxlen=100)
                self.user_logs[username].append(log_entry)

            except Exception as e:
                logger.error(f"Error guardando log de navegación: {e}")

    def get_user_logs(self, username, limit=100, from_date=None, to_date=None):
        """Obtener logs de un usuario"""
        logs = []

        # Primero obtener de memoria
        if username in self.user_logs:
            logs.extend(list(self.user_logs[username]))

        # Luego leer de archivos si es necesario
        try:
            user_dir = os.path.join(self.logs_dir, username)
            if os.path.exists(user_dir):
                for filename in sorted(os.listdir(user_dir), reverse=True):
                    if filename.startswith('navigation_') and filename.endswith('.log'):
                        filepath = os.path.join(user_dir, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            for line in f:
                                try:
                                    log_entry = json.loads(line.strip())
                                    # Filtrar por fechas si es necesario
                                    if from_date:
                                        log_date = datetime.fromisoformat(log_entry['timestamp']).date()
                                        if log_date < from_date:
                                            continue
                                    if to_date:
                                        log_date = datetime.fromisoformat(log_entry['timestamp']).date()
                                        if log_date > to_date:
                                            continue
                                    logs.append(log_entry)
                                except:
                                    continue
        except Exception as e:
            logger.error(f"Error leyendo logs de {username}: {e}")

        # Ordenar por timestamp descendente y limitar
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return logs[:limit]

    def get_all_users_logs_summary(self):
        """Obtener resumen de logs de todos los usuarios"""
        summary = {}
        if os.path.exists(self.logs_dir):
            for username in os.listdir(self.logs_dir):
                user_dir = os.path.join(self.logs_dir, username)
                if os.path.isdir(user_dir):
                    total_visits = 0
                    last_visit = None
                    success_count = 0
                    error_count = 0
                    blocked_count = 0

                    for filename in os.listdir(user_dir):
                        if filename.startswith('navigation_') and filename.endswith('.log'):
                            filepath = os.path.join(user_dir, filename)
                            try:
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    for line in f:
                                        try:
                                            log_entry = json.loads(line.strip())
                                            total_visits += 1

                                            # Contar por estado
                                            status = log_entry.get('status', '')
                                            if status == 'success':
                                                success_count += 1
                                            elif status == 'blocked':
                                                blocked_count += 1
                                            elif status == 'error':
                                                error_count += 1

                                            if not last_visit or log_entry['timestamp'] > last_visit:
                                                last_visit = log_entry['timestamp']
                                        except:
                                            continue
                            except:
                                continue

                    summary[username] = {
                        'total_visits': total_visits,
                        'last_visit': last_visit,
                        'success_count': success_count,
                        'error_count': error_count,
                        'blocked_count': blocked_count
                    }
        return summary


# Inicializar logger de navegación
nav_logger = NavigationLogger(Config.LOGS_DIR)


# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

def load_users():
    """Cargar usuarios desde CSV"""
    users = {}
    try:
        if os.path.exists(Config.USERS_CSV):
            with open(Config.USERS_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Asegurar que tenemos todos los campos
                    users[row['username']] = {
                        'password_hash': row['password_hash'],
                        'role': row.get('role', 'user'),
                        'created_at': row.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                        'last_login': row.get('last_login', '')
                    }
            logger.info(f"Usuarios cargados: {len(users)}")
        else:
            # Usuarios por defecto si no existe archivo
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            users = {
                'admin': {
                    'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
                    'role': 'admin',
                    'created_at': now,
                    'last_login': ''
                },
                'usuario': {
                    'password_hash': hashlib.sha256('password123'.encode()).hexdigest(),
                    'role': 'user',
                    'created_at': now,
                    'last_login': ''
                }
            }
            save_users(users)
    except Exception as e:
        logger.error(f"Error cargando usuarios: {e}")
        # Usuarios de emergencia
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        users = {
            'admin': {
                'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
                'role': 'admin',
                'created_at': now,
                'last_login': ''
            }
        }
    return users


def save_users(users):
    """Guardar usuarios en CSV"""
    try:
        # Asegurar que el directorio data existe
        os.makedirs(Config.DATA_DIR, exist_ok=True)

        with open(Config.USERS_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['username', 'password_hash', 'role', 'created_at', 'last_login'])
            for username, data in users.items():
                writer.writerow([
                    username,
                    data['password_hash'],
                    data.get('role', 'user'),
                    data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    data.get('last_login', '')
                ])
        logger.info("Usuarios guardados correctamente")
    except Exception as e:
        logger.error(f"Error guardando usuarios: {e}")


def load_allowed_urls():
    """Cargar URLs/dominios permitidos desde CSV"""
    urls = []
    try:
        if os.path.exists(Config.ALLOWED_URLS_CSV):
            with open(Config.ALLOWED_URLS_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Verificar que existe la columna 'pattern'
                    if 'pattern' in row:
                        urls.append({
                            'pattern': row['pattern'],
                            'description': row.get('description', ''),
                            'created_at': row.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        })
            logger.info(f"URLs permitidas cargadas: {len(urls)}")

            # Si no hay URLs, usar por defecto
            if len(urls) == 0:
                logger.warning("No hay URLs permitidas, usando por defecto")
                urls = get_default_allowed_urls()
        else:
            # Si no existe el archivo, crear con URLs por defecto
            logger.warning(f"Archivo {Config.ALLOWED_URLS_CSV} no existe, creando con valores por defecto")
            urls = get_default_allowed_urls()
            save_allowed_urls(urls)
    except Exception as e:
        logger.error(f"Error cargando URLs: {e}")
        urls = get_default_allowed_urls()

    return urls

def get_default_allowed_urls():
    """Obtener URLs permitidas por defecto"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return [
        {'pattern': 'google.com', 'description': 'Buscador Google', 'created_at': now},
        {'pattern': '*.google.com', 'description': 'Subdominios Google', 'created_at': now},
        {'pattern': '*.edu', 'description': 'Instituciones educativas', 'created_at': now},
        {'pattern': '*.gov', 'description': 'Sitios gubernamentales', 'created_at': now},
        {'pattern': '*.org', 'description': 'Organizaciones', 'created_at': now},
    ]


def save_allowed_urls(urls):
    """Guardar URLs permitidas en CSV"""
    try:
        # Asegurar que el directorio data existe
        os.makedirs(Config.DATA_DIR, exist_ok=True)

        with open(Config.ALLOWED_URLS_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['pattern', 'allowed', 'description', 'created_at'])
            for url in urls:
                writer.writerow([
                    url['pattern'],
                    'true',
                    url.get('description', ''),
                    url.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                ])
        logger.info(f"URLs guardadas correctamente: {len(urls)}")
    except Exception as e:
        logger.error(f"Error guardando URLs: {e}")


def normalize_url_pattern(pattern):
    """Normalizar un patrón de URL"""
    pattern = pattern.strip().lower()

    # Si es una URL completa, extraer el dominio
    if pattern.startswith(('http://', 'https://')):
        parsed = urlparse(pattern)
        pattern = parsed.netloc or parsed.path

    # Quitar www. si existe
    if pattern.startswith('www.'):
        pattern = pattern[4:]

    # Quitar puerto si existe
    if ':' in pattern:
        pattern = pattern.split(':')[0]

    # Quitar barras al final
    pattern = pattern.rstrip('/')

    return pattern


def is_url_allowed(url, allowed_patterns):
    """Verificar si una URL está permitida según los patrones"""
    # Si no hay patrones, permitir todo (con advertencia)
    if not allowed_patterns or len(allowed_patterns) == 0:
        logger.warning(f"No hay URLs permitidas configuradas. Permitiendo todas las URLs temporalmente.")
        return True

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Quitar puerto si existe
        if ':' in domain:
            domain = domain.split(':')[0]

        # Quitar www. si existe
        if domain.startswith('www.'):
            domain = domain[4:]

        logger.debug(f"Verificando dominio: {domain}")

        for pattern_dict in allowed_patterns:
            pattern = pattern_dict['pattern'].lower()

            # Caso 1: Patrón exacto
            if pattern == domain:
                logger.debug(f"✓ Coincidencia exacta: {domain} == {pattern}")
                return True

            # Caso 2: Wildcard al inicio (*.dominio.com)
            if pattern.startswith('*.'):
                base_domain = pattern[2:]  # quitar *.
                if domain.endswith(base_domain):
                    logger.debug(f"✓ Wildcard: {domain} termina en {base_domain}")
                    return True

            # Caso 3: Subdominio de dominio permitido
            if domain.endswith('.' + pattern):
                logger.debug(f"✓ Subdominio: {domain} termina en .{pattern}")
                return True

            # Caso 4: Wildcard simple
            if pattern.startswith('*'):
                base_pattern = pattern[1:]  # quitar *
                if domain.endswith(base_pattern):
                    logger.debug(f"✓ Wildcard simple: {domain} termina en {base_pattern}")
                    return True

        logger.debug(f"✗ No hay coincidencia para {domain}")
        return False

    except Exception as e:
        logger.error(f"Error verificando URL {url}: {e}")
        # En caso de error, permitir por seguridad (mejor denegar en producción)
        return True


def get_ip_and_ping(domain):
    """Obtener IP y latencia de un dominio"""
    try:
        # Quitar protocolo y puerto
        if '://' in domain:
            domain = domain.split('://')[1]
        if '/' in domain:
            domain = domain.split('/')[0]
        if ':' in domain:
            domain = domain.split(':')[0]

        # Obtener IP
        ip = socket.gethostbyname(domain)

        # Medir ping
        start_time = time.time()
        socket.create_connection((domain, 80), timeout=2)
        ping = int((time.time() - start_time) * 1000)

        return ip, ping
    except Exception as e:
        logger.error(f"Error obteniendo IP/ping para {domain}: {e}")
        return 'N/A', 'N/A'


def verificar_password(password, hash_almacenado):
    """Verificar contraseña"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest() == hash_almacenado


def login_required(f):
    """Decorador para requerir autenticación"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Decorador para requerir rol de administrador"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))

        users = load_users()
        if session['username'] not in users or users[session['username']].get('role') != 'admin':
            flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
            return redirect(url_for('index'))

        return f(*args, **kwargs)

    return decorated_function


# ============================================
# RUTAS DE AUTENTICACIÓN
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        users = load_users()

        if username in users and verificar_password(password, users[username]['password_hash']):
            session.clear()
            session['username'] = username
            session['role'] = users[username].get('role', 'user')
            session.permanent = True

            # Actualizar último login con fecha y hora COMPLETA
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            users[username]['last_login'] = now
            save_users(users)

            logger.info(f"Login exitoso: {username} a las {now}")
            flash(f'Bienvenido {username}!', 'success')
            return redirect(url_for('index'))

        logger.warning(f"Login fallido: {username}")
        flash('Usuario o contraseña incorrectos', 'error')
        return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Cerrar sesión"""
    username = session.get('username', 'Desconocido')
    session.clear()
    logger.info(f"Logout: {username}")
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('login'))


# ============================================
# API PARA INFORMACIÓN DE RED
# ============================================

@app.route('/api/network-info')
@login_required
def network_info():
    """API para obtener IP y ping de una URL"""
    url = request.args.get('url', '')
    if not url:
        return jsonify({'error': 'No URL provided'})

    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path

        ip, ping = get_ip_and_ping(domain)
        return jsonify({
            'ip': ip,
            'ping': ping,
            'domain': domain
        })
    except Exception as e:
        return jsonify({'error': str(e)})


# ============================================
# RUTAS PRINCIPALES
# ============================================

@app.route('/')
@login_required
def index():
    """Página principal del navegador"""
    try:
        # En lugar de cargar Google, mostramos la página de inicio
        return render_template('browser.html',
                             username=session.get('username', 'Usuario'),
                             role=session.get('role', 'user'),
                             start_page=True)  # Indicamos que es la página de inicio
    except Exception as e:
        logger.error(f"Error en index: {e}")
        return f"Error cargando la página: {str(e)}", 500

def rewrite_proxy_urls(soup, base_url):
    """
    Reescribe todas las URLs de recursos para que pasen por el proxy
    """

    tags_attrs = {
        "a": "href",
        "img": "src",
        "script": "src",
        "iframe": "src",
        "link": "href",
        "form": "action",
        "video": "src",
        "audio": "src",
        "source": "src"
    }

    for tag_name, attr in tags_attrs.items():
        for tag in soup.find_all(tag_name):
            if tag.has_attr(attr):

                original_url = tag[attr]

                # Ignorar anclas y javascript
                if original_url.startswith("#") or original_url.startswith("javascript:"):
                    continue

                # Convertir a URL absoluta
                absolute_url = urljoin(base_url, original_url)

                # Reescribir hacia el proxy
                tag[attr] = f"/proxy/?url={absolute_url}"

                # Evitar abrir nuevas ventanas
                if tag_name == "a":
                    tag["target"] = "browser-frame"

    return soup


@app.route('/proxy/')
@login_required
def proxy():
    """Endpoint proxy con fallback HTTPS → HTTP y logs mejorados"""
    url = request.args.get('url')
    username = session.get('username', 'unknown')

    if not url:
        return "URL no especificada", 400

    # Normalizar URL
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            url = 'https://' + url
            parsed = urlparse(url)
    except Exception as e:
        return f"URL inválida: {str(e)}", 400

    # Verificar URLs permitidas
    allowed_urls = load_allowed_urls()
    if not is_url_allowed(url, allowed_urls):
        return render_template(
            'error.html',
            error_code=403,
            error_message="Acceso denegado",
            error_details="La URL no está en la lista de permitidas"
        ), 403

    req_session = requests.Session()
    req_session.trust_env = False
    headers = {
        'User-Agent': request.headers.get('User-Agent', Config.USER_AGENT),
        'Accept': request.headers.get('Accept', '*/*'),
    }

    try:
        # Intentar HTTPS primero
        try:
            resp = req_session.get(url, headers=headers, timeout=Config.TIMEOUT, allow_redirects=True, verify=True)
        except requests.exceptions.ConnectionError as e_https:
            logger.warning(f"HTTPS falló para {url}: {e_https}")
            # Intentar HTTP si HTTPS falla
            if url.startswith("https://"):
                url_http = url.replace("https://", "http://", 1)
                logger.info(f"Intentando fallback HTTP: {url_http}")
                resp = req_session.get(url_http, headers=headers, timeout=Config.TIMEOUT, allow_redirects=True, verify=False)
            else:
                raise e_https

        # Registrar IP/ping
        try:
            ip, _ = get_ip_and_ping(parsed.netloc)
        except Exception as e_ip:
            logger.warning(f"No se pudo obtener IP/ping de {parsed.netloc}: {e_ip}")
            ip = None

        nav_logger.log_navigation(username, url, ip=ip, status='success')

        content_type = resp.headers.get('Content-Type', '')

        # Procesar HTML
        if 'text/html' in content_type:
            soup = BeautifulSoup(resp.text, 'lxml')

            # Forzar scroll
            style_tag = soup.new_tag("style")
            style_tag.string = "html, body { overflow: auto !important; max-width: none !important; }"
            if soup.head:
                soup.head.append(style_tag)

            # Base tag
            base_tag = soup.new_tag("base", href=f"/proxy/?url={url}")
            if soup.head:
                soup.head.insert(0, base_tag)

            # Reescribir recursos
            soup = rewrite_proxy_urls(soup, url)
            content = str(soup)
        else:
            content = resp.content

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded_headers]

        return Response(content, status=resp.status_code, headers=response_headers)

    except Exception as e:
        logger.error(f"Error proxy: {e}")
        nav_logger.log_navigation(username, url, ip=None, status='error', error=str(e))
        return render_template(
            'error.html',
            error_code=500,
            error_message="Error interno del proxy",
            error_details=str(e)
        ), 500
# ============================================
# RUTAS DE ADMINISTRACIÓN - CORREGIDAS
# ============================================

@app.route('/admin')
@admin_required
def admin_panel():
    """Panel de administración"""
    try:
        users = load_users()
        allowed_urls = load_allowed_urls()
        logs_summary = nav_logger.get_all_users_logs_summary()

        return render_template('admin.html',
                               users=users,
                               allowed_urls=allowed_urls,
                               logs_summary=logs_summary,
                               username=session.get('username'))
    except Exception as e:
        logger.error(f"Error en admin_panel: {e}")
        flash(f'Error cargando panel de administración: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/admin/users')
@admin_required
def admin_users():
    """Página de administración de usuarios"""
    try:
        users = load_users()
        logs_summary = nav_logger.get_all_users_logs_summary()

        # Calcular estadísticas
        total_users = len(users)
        admin_count = sum(1 for u in users.values() if u.get('role') == 'admin')
        user_count = total_users - admin_count
        active_users = len(logs_summary)

        return render_template('admin_users.html',
                               users=users,
                               logs_summary=logs_summary,
                               total_users=total_users,
                               admin_count=admin_count,
                               user_count=user_count,
                               active_users=active_users,
                               username=session.get('username'))
    except Exception as e:
        logger.error(f"Error en admin_users: {e}")
        import traceback
        logger.error(traceback.format_exc())
        flash(f'Error cargando administración de usuarios: {str(e)}', 'error')
        return redirect(url_for('index'))
    

@app.route('/admin/urls')
@admin_required
def admin_urls():
    """Página de administración de URLs"""
    try:
        allowed_urls = load_allowed_urls()

        # Calcular estadísticas en Python (no en el template)
        wildcard_count = sum(1 for url in allowed_urls if url['pattern'].startswith('*.'))
        exact_count = len(allowed_urls) - wildcard_count

        return render_template('admin_urls.html',
                               allowed_urls=allowed_urls,
                               wildcard_count=wildcard_count,
                               exact_count=exact_count,
                               username=session.get('username'))
    except Exception as e:
        logger.error(f"Error en admin_urls: {e}")
        import traceback
        logger.error(traceback.format_exc())
        flash(f'Error cargando administración de URLs: {str(e)}', 'error')
        return redirect(url_for('index'))

    
@app.route('/admin/user/<username>/logs')
@admin_required
def view_user_logs(username):
    """Ver logs de un usuario específico"""
    try:
        users = load_users()
        if username not in users:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('admin_panel'))

        # Obtener parámetros de filtro
        limit = request.args.get('limit', 100, type=int)
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        # Convertir fechas si existen
        from_date_obj = None
        to_date_obj = None
        if from_date:
            try:
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            except:
                pass
        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            except:
                pass

        logs = nav_logger.get_user_logs(username, limit=limit, from_date=from_date_obj, to_date=to_date_obj)

        return render_template('user_logs.html',
                               username=username,
                               user_info=users[username],
                               logs=logs,
                               limit=limit,
                               from_date=from_date,
                               to_date=to_date,
                               admin_user=session.get('username'))
    except Exception as e:
        logger.error(f"Error en view_user_logs: {e}")
        flash(f'Error cargando logs: {str(e)}', 'error')
        return redirect(url_for('admin_panel'))


@app.route('/admin/logs')
@admin_required
def view_all_logs():
    """Ver todos los logs de todos los usuarios"""
    try:
        users = load_users()

        # Obtener parámetros de filtro
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        selected_user = request.args.get('user', '')
        status_filter = request.args.get('status', '')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        # Convertir fechas
        from_date_obj = None
        to_date_obj = None
        if from_date:
            try:
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            except:
                pass
        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            except:
                pass

        # Recopilar logs de todos los usuarios
        all_logs = []
        for username in users.keys():
            if selected_user and username != selected_user:
                continue
            user_logs = nav_logger.get_user_logs(username, limit=1000)
            all_logs.extend(user_logs)

        # Aplicar filtros adicionales
        filtered_logs = []
        for log in all_logs:
            # Filtrar por estado
            if status_filter and log.get('status') != status_filter:
                continue

            # Filtrar por fecha
            try:
                log_date = datetime.fromisoformat(log['timestamp']).date()
                if from_date_obj and log_date < from_date_obj:
                    continue
                if to_date_obj and log_date > to_date_obj:
                    continue
            except:
                pass

            filtered_logs.append(log)

        # Ordenar por timestamp descendente
        filtered_logs.sort(key=lambda x: x['timestamp'], reverse=True)

        total_logs = len(filtered_logs)
        total_pages = max(1, (total_logs + limit - 1) // limit)

        # Asegurar que page esté en rango válido
        page = max(1, min(page, total_pages))

        # Paginar
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_logs = filtered_logs[start_idx:end_idx]

        return render_template('all_logs.html',
                               logs=paginated_logs,
                               users=users.keys(),
                               total_logs=total_logs,
                               page=page,
                               total_pages=total_pages,
                               username=session.get('username'))
    except Exception as e:
        logger.error(f"Error en view_all_logs: {e}")
        flash(f'Error cargando logs: {str(e)}', 'error')
        return redirect(url_for('admin_panel'))


@app.route('/admin/logs/export')
@admin_required
def export_all_logs():
    """Exportar todos los logs a CSV"""
    try:
        users = load_users()

        # Recopilar todos los logs
        all_logs = []
        for username in users.keys():
            user_logs = nav_logger.get_user_logs(username, limit=5000)  # Límite alto para exportación
            all_logs.extend(user_logs)

        # Ordenar por timestamp descendente
        all_logs.sort(key=lambda x: x['timestamp'], reverse=True)

        # Crear archivo temporal
        import tempfile

        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        writer = csv.writer(temp_file)

        # Escribir headers
        writer.writerow(['Timestamp', 'Usuario', 'URL', 'IP', 'Status', 'Error', 'User Agent'])

        # Escribir logs
        for log in all_logs:
            writer.writerow([
                log.get('timestamp', ''),
                log.get('username', ''),
                log.get('url', ''),
                log.get('ip', ''),
                log.get('status', ''),
                log.get('error', ''),
                log.get('user_agent', '')
            ])

        temp_file.close()

        return send_file(temp_file.name,
                         as_attachment=True,
                         download_name=f'todos_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                         mimetype='text/csv')
    except Exception as e:
        logger.error(f"Error exportando logs: {e}")
        flash(f'Error exportando logs: {str(e)}', 'error')
        return redirect(url_for('admin_panel'))


@app.route('/admin/add_user', methods=['POST'])
@admin_required
def add_user():
    """Añadir nuevo usuario"""
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'user')

        if not username or not password:
            flash('Usuario y contraseña requeridos', 'error')
            return redirect(url_for('admin_users'))

        users = load_users()

        if username in users:
            flash('El usuario ya existe', 'error')
            return redirect(url_for('admin_users'))

        # Fecha y hora ACTUAL completa
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        users[username] = {
            'password_hash': hashlib.sha256(password.encode('utf-8')).hexdigest(),
            'role': role,
            'created_at': now,
            'last_login': ''
        }

        save_users(users)
        flash(f'Usuario {username} creado correctamente el {now}', 'success')
        logger.info(f"Usuario {username} creado el {now}")

    except Exception as e:
        logger.error(f"Error añadiendo usuario: {e}")
        flash(f'Error añadiendo usuario: {str(e)}', 'error')

    return redirect(url_for('admin_users'))


@app.route('/admin/change_password/<username>', methods=['POST'])
@admin_required
def change_password(username):
    """Cambiar contraseña de un usuario"""
    try:
        new_password = request.form.get('new_password', '')

        if not new_password:
            flash('La nueva contraseña no puede estar vacía', 'error')
            return redirect(url_for('admin_panel'))

        users = load_users()

        if username not in users:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('admin_panel'))

        users[username]['password_hash'] = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
        save_users(users)

        flash(f'Contraseña de {username} actualizada correctamente', 'success')
    except Exception as e:
        logger.error(f"Error cambiando contraseña: {e}")
        flash(f'Error cambiando contraseña: {str(e)}', 'error')

    return redirect(url_for('admin_panel'))


@app.route('/admin/delete_user/<username>')
@admin_required
def delete_user(username):
    """Eliminar usuario"""
    try:
        if username == 'admin':
            flash('No se puede eliminar el usuario administrador principal', 'error')
            return redirect(url_for('admin_panel'))

        users = load_users()

        if username in users:
            del users[username]
            save_users(users)
            flash(f'Usuario {username} eliminado correctamente', 'success')
        else:
            flash('Usuario no encontrado', 'error')
    except Exception as e:
        logger.error(f"Error eliminando usuario: {e}")
        flash(f'Error eliminando usuario: {str(e)}', 'error')

    return redirect(url_for('admin_panel'))


@app.route('/admin/add_url', methods=['POST'])
@admin_required
def add_url():
    """Añadir URL/dominio permitido"""
    try:
        pattern = request.form.get('pattern', '').strip()
        description = request.form.get('description', '').strip()

        if not pattern:
            flash('El patrón de URL es requerido', 'error')
            return redirect(url_for('admin_urls'))

        # Normalizar el patrón
        normalized_pattern = normalize_url_pattern(pattern)

        allowed_urls = load_allowed_urls()

        # Verificar si ya existe
        for url in allowed_urls:
            if url['pattern'] == normalized_pattern:
                flash(f'El patrón {normalized_pattern} ya existe', 'error')
                return redirect(url_for('admin_urls'))

        # Fecha y hora ACTUAL completa
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        allowed_urls.append({
            'pattern': normalized_pattern,
            'description': description or f'URL permitida: {normalized_pattern}',
            'created_at': now
        })

        save_allowed_urls(allowed_urls)
        flash(f'URL permitida añadida: {normalized_pattern} el {now}', 'success')
        logger.info(f"URL {normalized_pattern} añadida el {now}")

    except Exception as e:
        logger.error(f"Error añadiendo URL: {e}")
        flash(f'Error añadiendo URL: {str(e)}', 'error')

    return redirect(url_for('admin_urls'))


@app.route('/admin/delete_url/<path:pattern>')
@admin_required
def delete_url(pattern):
    """Eliminar URL permitida"""
    try:
        allowed_urls = load_allowed_urls()

        # Verificar si es la última URL
        if len(allowed_urls) <= 1:
            flash('No se puede eliminar la última URL permitida. Debe haber al menos una URL en la lista.', 'error')
            return redirect(url_for('admin_panel'))

        # Filtrar la URL a eliminar
        original_count = len(allowed_urls)
        allowed_urls = [url for url in allowed_urls if url['pattern'] != pattern]

        if len(allowed_urls) == original_count:
            flash('URL no encontrada', 'error')
        else:
            save_allowed_urls(allowed_urls)
            flash(f'URL eliminada: {pattern}', 'success')
    except Exception as e:
        logger.error(f"Error eliminando URL: {e}")
        flash(f'Error eliminando URL: {str(e)}', 'error')

    return redirect(url_for('admin_panel'))


@app.route('/admin/reset_default_urls')
@admin_required
def reset_default_urls():
    """Restablecer URLs por defecto"""
    try:
        default_urls = get_default_allowed_urls()
        save_allowed_urls(default_urls)
        flash('URLs restablecidas a los valores por defecto', 'success')
    except Exception as e:
        logger.error(f"Error restableciendo URLs: {e}")
        flash(f'Error restableciendo URLs: {str(e)}', 'error')

    return redirect(url_for('admin_panel'))


# ============================================
# MANEJO DE ERRORES
# ============================================

@app.errorhandler(404)
def not_found(e):
    """Página no encontrada"""
    if 'username' in session:
        return render_template('error.html',
                               error_code=404,
                               error_message="Página no encontrada",
                               error_details="La URL solicitada no existe"), 404
    return redirect(url_for('login'))


@app.errorhandler(500)
def internal_error(e):
    """Error interno"""
    logger.error(f"Error 500: {e}")
    if 'username' in session:
        return render_template('error.html',
                               error_code=500,
                               error_message="Error interno del servidor",
                               error_details="Contacte al administrador"), 500
    return redirect(url_for('login'))


# ============================================
# INICIALIZACIÓN
# ============================================

# Crear directorios si no existen
os.makedirs(Config.TEMPLATES_DIR, exist_ok=True)
os.makedirs(os.path.join(Config.STATIC_DIR, 'css'), exist_ok=True)
os.makedirs(os.path.join(Config.STATIC_DIR, 'js'), exist_ok=True)
os.makedirs(Config.LOGS_DIR, exist_ok=True)

# Cargar usuarios y URLs iniciales
load_users()
load_allowed_urls()

# Para PythonAnywhere
application = app

if __name__ == '__main__':
    print("=" * 60)
    print("🌐 PROXY WEB PROFESIONAL CON LOGS")
    print("=" * 60)
    print(f"\n📁 Directorio base: {Config.BASE_DIR}")
    print(f"📁 Logs: {Config.LOGS_DIR}")
    print(f"👤 Usuario actual: admin")
    print(f"👥 Usuarios: {Config.USERS_CSV}")
    print(f"🌍 URLs permitidas: {Config.ALLOWED_URLS_CSV}")
    print("\n👤 Usuarios por defecto:")
    print("   • admin / admin123")
    print("   • usuario / password123")
    print("\n🌐 URLs por defecto cargadas")
    print("\n🚀 Servidor iniciado en:")
    print("   • http://localhost:5000")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=False)