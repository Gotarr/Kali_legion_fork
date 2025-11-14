"""
Simple HTTP test server with Basic Authentication.

Credentials: admin:123456!
Port: 8080

Usage:
    python test_server.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import base64


class AuthHandler(BaseHTTPRequestHandler):
    """HTTP handler with Basic Authentication."""
    
    # Valid credentials (Base64 encoded: admin:123456!)
    VALID_AUTH = base64.b64encode(b'admin:123456!').decode('ascii')
    
    def do_GET(self):
        """Handle GET requests with authentication."""
        # Get Authorization header
        auth_header = self.headers.get('Authorization')
        
        # Check authentication for ALL paths
        if not auth_header or not auth_header.startswith('Basic '):
            self.send_auth_required()
            return
        
        # Extract credentials
        auth_decoded = auth_header[6:]  # Remove "Basic " prefix
        
        # Validate credentials
        if auth_decoded != self.VALID_AUTH:
            self.send_auth_required()
            return
        
        # Authentication successful
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authenticated!</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f0f0f0;
                }
                .success {
                    background: #d4edda;
                    color: #155724;
                    padding: 20px;
                    border-radius: 5px;
                    border: 1px solid #c3e6cb;
                }
                .info {
                    background: #d1ecf1;
                    color: #0c5460;
                    padding: 15px;
                    margin-top: 20px;
                    border-radius: 5px;
                    border: 1px solid #bee5eb;
                }
                h1 { margin-top: 0; }
                code {
                    background: #e9ecef;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }
            </style>
        </head>
        <body>
            <div class="success">
                <h1>✅ Authentication Successful!</h1>
                <p>You are logged in as: <strong>admin</strong></p>
            </div>
            <div class="info">
                <h2>Test Server Info</h2>
                <p><strong>Port:</strong> 8080</p>
                <p><strong>Valid Credentials:</strong></p>
                <ul>
                    <li>Username: <code>admin</code></li>
                    <li>Password: <code>123456!</code></li>
                </ul>
                <p><strong>Path:</strong> {path}</p>
            </div>
        </body>
        </html>
        """.format(path=self.path)
        
        self.wfile.write(html.encode('utf-8'))
    
    def do_HEAD(self):
        """Handle HEAD requests."""
        self.do_GET()
    
    def do_POST(self):
        """Handle POST requests."""
        self.do_GET()
    
    def send_auth_required(self):
        """Send 401 Unauthorized response."""
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Test Server"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Required</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f0f0f0;
                }
                .error {
                    background: #f8d7da;
                    color: #721c24;
                    padding: 20px;
                    border-radius: 5px;
                    border: 1px solid #f5c6cb;
                }
            </style>
        </head>
        <body>
            <div class="error">
                <h1>🔒 401 - Authentication Required</h1>
                <p>You need valid credentials to access this resource.</p>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Custom log format."""
        # Extract auth status from message
        status = args[1] if len(args) > 1 else "???"
        
        if status == "200":
            print(f"✅ [AUTH OK]  {self.address_string()} - {args[0]}")
        elif status == "401":
            print(f"❌ [DENIED]  {self.address_string()} - {args[0]}")
        else:
            print(f"ℹ️  [{status}]  {self.address_string()} - {args[0]}")


def run_server(port=8080):
    """
    Start HTTP test server.
    
    Args:
        port: Port number (default: 8080)
    """
    server_address = ('', port)
    httpd = HTTPServer(server_address, AuthHandler)
    
    print("=" * 70)
    print("🌐 HTTP Basic Auth Test Server")
    print("=" * 70)
    print(f"📡 Listening on: http://127.0.0.1:{port}")
    print(f"🔐 Valid Credentials:")
    print(f"   Username: admin")
    print(f"   Password: 123456!")
    print(f"   Base64: {AuthHandler.VALID_AUTH}")
    print("=" * 70)
    print("💡 Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⚠️  Server stopped by user")
        httpd.shutdown()


if __name__ == "__main__":
    run_server()
