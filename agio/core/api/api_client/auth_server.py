import threading
import logging
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from requests_oauthlib import OAuth2Session

from agio.tools.network import get_free_port

logger = logging.getLogger(__name__)

def _get_template_content(name):
    page_file_path = Path(__file__).parent.parent / f'templates/{name}.html'
    if not page_file_path.exists():
        raise FileNotFoundError(f"File {page_file_path} not found")
    return page_file_path.read_text()

def _success_page_text():
    return _get_template_content('success_page')


def _error_page_text():
    return _get_template_content('error_page')



def run_oauth_server(
        client_id,
        scope,
        authorization_base_url,
        token_url,
        stop_event: threading.Event,
        port=None,
):
    token = {}
    port = port or get_free_port()
    redirect_uri = f'http://localhost:{port}/oauth_callback'
    logger.info('Callback URL: %s', redirect_uri)
    oauth = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)
    authorization_url, state = oauth.authorization_url(authorization_base_url)

    class RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal token
            if self.path.startswith('/oauth_callback'):
                parsed_url = urlparse(self.path)
                code = parse_qs(parsed_url.query).get('code')
                if code:
                    code = code[0]
                    token.update(oauth.fetch_token(token_url, client_secret='', code=code))
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(_success_page_text().encode())
                    stop_event.set()
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(_error_page_text().encode())
            else:
                self.send_response(302)
                self.send_header('Location', authorization_url)
                self.end_headers()

    server = HTTPServer(('localhost', port), RequestHandler)
    server.timeout = 1

    def serve():
        logger.info(f'Auth URL: {authorization_url}')
        webbrowser.open(authorization_url)
        try:
            while not stop_event.is_set():
                server.handle_request()
        except KeyboardInterrupt:
            server.shutdown()
    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    logger.info(f'Waiting callback on http://localhost:{port}')
    return token, thread
