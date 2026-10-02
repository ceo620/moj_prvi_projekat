import http.server
import socketserver
import subprocess
import os

PORT = 8888

HTML = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TITAN GRID 888</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #0f172a; color: white; padding: 20px; margin: 0; }
        h1 { color: #38bdf8; text-align: center; font-size: 20px; margin-bottom: 5px; }
        .sub { text-align: center; color: #94a3b8; font-size: 12px; margin-bottom: 20px; }
        .card { background: #1e293b; border-radius: 10px; padding: 15px; margin-bottom: 15px; border: 1px solid #334155; }
        .btn { display: block; width: 100%; padding: 14px 0; background: #0284c7; color: white; border: none; border-radius: 6px; font-weight: bold; margin-top: 10px; text-align: center; font-size: 15px; }
        .btn-green { background: #16a34a; }
        .btn-purple { background: #9333ea; }
        #out { background: #0f172a; padding: 12px; border-radius: 6px; font-family: monospace; color: #4ade80; margin-top: 10px; min-height: 40px; word-break: break-all; font-size: 13px; }
    </style>
</head>
<body>
    <h1>TITAN GRID 888</h1>
    <div class="sub">iPhone Node | PROTOKOL-888</div>

    <div class="card">
        <h3>📄 Dokumenti</h3>
        <button class="btn" onclick="run('/api/memorandum')">Generiši Memorandum</button>
        <button class="btn btn-green" onclick="run('/api/ugovor')">Generiši Ugovor</button>
    </div>

    <div class="card">
        <h3>🔍 Dijagnostika</h3>
        <button class="btn btn-purple" onclick="run('/api/ast')">Pokreni AST Validaciju</button>
    </div>

    <div class="card">
        <h3>📌 Status</h3>
        <div id="out">Sistem je spreman.</div>
    </div>

    <script>
        function run(ep) {
            document.getElementById('out').innerText = 'Izvršavam...';
            fetch(ep)
                .then(r => r.text())
                .then(d => { document.getElementById('out').innerText = d; })
                .catch(e => { document.getElementById('out').innerText = 'Greška: ' + e; });
        }
    </script>
</body>
</html>"""

class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode('utf-8'))
        elif self.path == '/api/memorandum':
            try:
                import src.memorandum_factory as mf
                if hasattr(mf, 'generisi_memorandum'):
                    mf.generisi_memorandum()
                res = '[OK] Memorandum uspešno generisan na iPhone čvoru.'
            except Exception as e:
                res = f'[-] Greška: {e}'
            self._send(res)
        elif self.path == '/api/ugovor':
            try:
                import src.ugovor_factory as uf
                if hasattr(uf, 'generisi_ugovor'):
                    uf.generisi_ugovor()
                res = '[OK] Ugovor uspešno generisan na iPhone čvoru.'
            except Exception as e:
                res = f'[-] Greška: {e}'
            self._send(res)
        elif self.path == '/api/ast':
            res = subprocess.getoutput('python3 -m src.ast_validator')
            self._send(res)

    def _send(self, msg):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(msg.encode('utf-8'))

with socketserver.TCPServer(("", PORT), H) as httpd:
    print(f"[+] TITAN Dashboard pokrenut na http://localhost:{PORT}")
    httpd.serve_forever()
