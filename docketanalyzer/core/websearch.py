import os
import time
import requests
from docketanalyzer import DATA_DIR, WEB_SEARCH_PORT


limiter_content = """
[botdetection.ip_limit]
# activate link_token method in the ip_limit method
link_token = true
"""


uwsgi_content = """
[uwsgi]
# Who will run the code
uid = searxng
gid = searxng

# Number of workers (usually CPU count)
# default value: %k (= number of CPU core, see Dockerfile)
workers = %k

# Number of threads per worker
# default value: 4 (see Dockerfile)
threads = 4

# The right granted on the created socket
chmod-socket = 666

# Plugin to use and interpreter config
single-interpreter = true
master = true
plugin = python3
lazy-apps = true
enable-threads = 4

# Module to import
module = searx.webapp

# Virtualenv and python path
pythonpath = /usr/local/searxng/
chdir = /usr/local/searxng/searx/

# automatically set processes name to something meaningful
auto-procname = true

# Disable request logging for privacy
disable-logging = true
log-5xx = true

# Set the max size of a request (request-body excluded)
buffer-size = 8192

# No keep alive
# See https://github.com/searx/searx-docker/issues/24
add-header = Connection: close

# uwsgi serves the static files
static-map = /static=/usr/local/searxng/searx/static
# expires set to one day
static-expires = /* 86400
static-gzip-all = True
offload-threads = 4
"""


settings_content = """
# see https://docs.searxng.org/admin/settings/settings.html#settings-use-default-settings
use_default_settings: true

server:
  secret_key: "adsfasdfasdf"
  limiter: false
  image_proxy: true
  port: 8080
  bind_address: "0.0.0.0"

ui:
  static_use_hash: true

search:
  safe_search: 0
  autocomplete: ""
  default_lang: ""
  formats:
    - html
    - json
"""


class WebSearch:
    def __init__(self, host='127.0.0.1', port=WEB_SEARCH_PORT):
        self.host = host
        self.port = port
        self.config_dir = DATA_DIR / 'local' / 'searxng'
        self.started = False
        self.cache = {}
    
    @property
    def url(self):
        return f'http://{self.host}:{self.port}'
    
    @property
    def running(self):
        try:
            r = requests.get(self.url)
            return r.status_code == 200
        except:
            return False

    def start(self):
        if not self.running:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            limiter_path = self.config_dir / 'limiter.toml'
            if not limiter_path.exists():
                limiter_path.write_text(limiter_content)
            uwsgi_path = self.config_dir / 'uwsgi.ini'
            if not uwsgi_path.exists():
                uwsgi_path.write_text(uwsgi_content)
            settings_path = self.config_dir / 'settings.yml'
            if not settings_path.exists():
                settings_path.write_text(settings_content)
            docker_cmd = f"docker run -d --name searxng -p {self.port}:8080 -v {self.config_dir}:/etc/searxng --restart always searxng/searxng:latest"
            os.system(docker_cmd)
            elapsed = 0
            while 1:
                print("Waiting for web search service to start...")
                if self.running:
                    break
                time.sleep(1)
                elapsed += 1
                if elapsed > 30:
                    raise Exception("Failed to start web search service in 30 seconds.")
        self.started = True

    def search(self, query, format='json', return_response=False, **kwargs):
        if not self.started:
            self.start()
        r = requests.get(f'{self.url}/search', params={'q': query, 'format': format, **kwargs})
        if return_response:
            return r
        if format == 'json':
            return r.json()
        return r.text
