"""HTTPS 反向代理 (仅供局域网演示): 让手机浏览器可以调用摄像头

背景：浏览器安全策略规定，非 localhost 的 HTTP 页面禁止 navigator.mediaDevices（实时摄像头）。
本脚本在 5443 端口提供 HTTPS，把请求转发到本机正在运行的 Vite 前端 (默认 5173)，
从而手机可以通过 https://<本机IP>:5443 打开门禁终端并使用实时摄像头。

用法:
    python scripts/https_proxy.py                # 默认 5443 -> 5173
    python scripts/https_proxy.py --port 5443 --target 5173

首次运行会在 scripts/certs/ 自动生成自签名证书（手机访问时会提示"不安全"，选择继续即可）。
"""
import argparse
import http.client
import ipaddress
import os
import socket
import ssl
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CERT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs")
CERT_FILE = os.path.join(CERT_DIR, "server.crt")
KEY_FILE = os.path.join(CERT_DIR, "server.key")

HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade",
}


def local_ipv4_list():
    ips = ["127.0.0.1"]
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None):
            ip = item[4][0]
            if ip.startswith("127.") or ip in ips:
                continue
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                continue
            if ":" in ip:  # 跳过 IPv6
                continue
            ips.append(ip)
    except Exception:
        pass
    return ips


def ensure_cert():
    """生成自签名证书（含本机所有 IPv4 的 SAN）"""
    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        return
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
    except ImportError:
        print("[ERROR] 缺少 cryptography，请先执行: pip install cryptography")
        sys.exit(1)

    import datetime as dt

    os.makedirs(CERT_DIR, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "SmartDormitory Local HTTPS")])
    san = [x509.DNSName("localhost")] + [
        x509.IPAddress(ipaddress.ip_address(ip)) for ip in local_ipv4_list()
    ]
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(dt.datetime.utcnow() - dt.timedelta(days=1))
        .not_valid_after(dt.datetime.utcnow() + dt.timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName(san), critical=False)
        .sign(key, hashes.SHA256())
    )
    with open(KEY_FILE, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    with open(CERT_FILE, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"[HTTPS] 已生成自签名证书: {CERT_DIR}")


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    target_host = "127.0.0.1"
    target_port = 5173

    def log_message(self, fmt, *args):
        if os.environ.get("PROXY_VERBOSE"):
            super().log_message(fmt, *args)

    def do_GET(self):
        self._proxy()

    def do_POST(self):
        self._proxy()

    def do_PUT(self):
        self._proxy()

    def do_DELETE(self):
        self._proxy()

    def do_OPTIONS(self):
        self._proxy()

    def _proxy(self):
        if self.headers.get("Upgrade", "").lower() == "websocket":
            # 不支持 WebSocket（HMR），前端页面与接口不受影响
            self.send_error(501, "WebSocket not supported by demo proxy")
            return

        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None

        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_BY_HOP}
        headers["Host"] = f"{self.target_host}:{self.target_port}"
        headers["X-Forwarded-Proto"] = "https"

        conn = http.client.HTTPConnection(self.target_host, self.target_port, timeout=60)
        try:
            conn.request(self.command, self.path, body=body, headers=headers)
            resp = conn.getresponse()
            data = resp.read()
        except Exception as exc:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"上游服务不可用: {exc}".encode("utf-8"))
            return
        finally:
            conn.close()

        self.send_response(resp.status)
        for k, v in resp.getheaders():
            if k.lower() not in HOP_BY_HOP and k.lower() != "content-length":
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass


def main():
    parser = argparse.ArgumentParser(description="局域网 HTTPS 代理（供手机摄像头使用）")
    parser.add_argument("--port", type=int, default=5443, help="HTTPS 监听端口，默认 5443")
    parser.add_argument("--target", type=int, default=5173, help="转发目标端口（Vite），默认 5173")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址，默认 0.0.0.0")
    args = parser.parse_args()

    ensure_cert()
    ProxyHandler.target_port = args.target

    httpd = ThreadingHTTPServer((args.host, args.port), ProxyHandler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT_FILE, KEY_FILE)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)

    print("=" * 62)
    print("  智慧宿舍 HTTPS 代理已启动（手机实时摄像头入口）")
    for ip in local_ipv4_list():
        print(f"  https://{ip}:{args.port}/terminal")
    print(f"  转发目标: http://127.0.0.1:{args.target}")
    print("  手机访问时若提示证书不安全，请选择「继续访问」")
    print("=" * 62)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[HTTPS] 已停止")


if __name__ == "__main__":
    main()
