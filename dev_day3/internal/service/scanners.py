import socket
import ssl
import time
import urllib.request
import json

def is_local_host(ip: str) -> bool:
    """
    Yêu cầu bảo mật: CHỈ cho phép quét các dải IP nội bộ, Private hoặc Loopback
    để tránh vi phạm pháp luật khi thực hiện Active Scan.
    """
    local_prefixes = [
        "127.", "10.", "192.168.",
        "172.16.", "172.17.", "172.18.", "172.19.", "172.20.",
        "172.21.", "172.22.", "172.23.", "172.24.", "172.25.",
        "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31."
    ]
    return any(ip.startswith(prefix) for prefix in local_prefixes) or ip == "localhost"

class IPScanner:
    """Bài 1.1: Quét Geolocation và ASN của IP public qua API miễn phí"""
    @staticmethod
    def scan(ip_address: str) -> dict:
        # Nếu là IP nội bộ thì không cần truy vấn bên ngoài
        if is_local_host(ip_address):
            return {
                "ip_address": ip_address,
                "geolocation": {"country": "Local", "city": "Internal Network", "isp": "Private LAN"},
                "asn": {"number": 0, "name": "PRIVATE"},
                "reverse_dns": "localhost"
            }
        try:
            # Sử dụng API công khai ip-api.com để lấy thông tin GeoIP và ASN
            url = f"http://ip-api.com/json/{ip_address}?fields=status,country,countryCode,regionName,city,lat,lon,isp,org,as"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get("status") == "success":
                    # Tách chuỗi ASN (Ví dụ: "AS13335 Cloudflare, Inc." -> 13335)
                    as_info = data.get("as", "")
                    asn_num = int(as_info.split()[0].replace("AS", "")) if as_info else 0
                    
                    return {
                        "ip_address": ip_address,
                        "geolocation": {
                            "country": data.get("country"),
                            "country_code": data.get("countryCode"),
                            "city": data.get("city"),
                            "region": data.get("regionName"),
                            "latitude": data.get("lat"),
                            "longitude": data.get("lon"),
                            "isp": data.get("isp"),
                            "org": data.get("org")
                        },
                        "asn": {
                            "number": asn_num,
                            "name": data.get("isp", "").upper().replace(" ", ""),
                            "description": data.get("org")
                        },
                        "reverse_dns": "N/A"
                    }
        except Exception:
            pass
        return {"ip_address": ip_address, "error": "Không thể lấy thông tin IP"}

class PortScanner:
    """Bài 1.2: Thiết kế công cụ Active Port Scan giới hạn trong mạng LAN/Local"""
    @staticmethod
    def scan(ip_address: str) -> dict:
        # KIỂM TRA BẢO MẬT: Chặn ngay nếu người dùng cố tình quét IP bên ngoài Internet!
        if not is_local_host(ip_address):
            raise PermissionError("CẢNH BÁO: Chỉ được phép thực hiện Port Scan trên địa chỉ IP nội bộ/localhost!")

        # Danh sách các cổng phổ biến cần kiểm tra
        target_ports = [22, 80, 443, 5432, 8080]
        open_ports = []
        start_time = time.time()

        # Dịch vụ mặc định tương ứng với từng Port
        services_map = {22: "ssh", 80: "http", 443: "https", 5432: "postgresql", 8080: "http-alt"}

        for port in target_ports:
            # Tạo một TCP Socket kết nối tầm thấp
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5) # Timeout ngắn để tăng tốc độ quét công cụ
            result = s.connect_ex((ip_address, port)) # Trả về 0 nếu kết nối thành công (Cổng Mở)
            
            if result == 0:
                version_banner = ""
                try:
                    # Gửi một chuỗi nhỏ để cố gắng bốc banner thông tin phiên bản (Banner Grabbing)
                    if port == 80:
                        s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
                        version_banner = s.recv(100).decode('utf-8', errors='ignore').split('\r\n')[0]
                except Exception:
                    pass
                
                open_ports.append({
                    "port": port,
                    "protocol": "tcp",
                    "state": "open",
                    "service": services_map.get(port, "unknown"),
                    "version": version_banner if version_banner else "Phát hiện dịch vụ"
                })
            s.close()

        duration = int((time.time() - start_time) * 1000)
        return {
            "ip_address": ip_address,
            "open_ports": open_ports,
            "closed_ports": len(target_ports) - len(open_ports),
            "total_scanned": len(target_ports),
            "scan_duration_ms": duration
        }

class SSLScanner:
    """Bài 1.3 (Bonus): Kiểm tra cấu hình mật mã TLS và chứng chỉ số SSL"""
    @staticmethod
    def scan(domain: str) -> dict:
        try:
            # Tạo ngữ cảnh SSL chuẩn
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=4) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    # Lấy thông tin chứng chỉ và phiên bản TLS
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    
                    # Trích xuất thông tin Subject và Issuer
                    subject = dict(x[0] for x in cert.get('subject', []))
                    issuer = dict(x[0] for x in cert.get('issuer', []))
                    
                    # Lấy danh sách SAN (Subject Alternative Names)
                    san = [x[1] for x in cert.get('subjectAltName', []) if x[0] == 'DNS']

                    return {
                        "domain": domain,
                        "certificate": {
                            "subject": f"CN={subject.get('commonName')}",
                            "issuer": f"CN={issuer.get('commonName')}, O={issuer.get('organizationName')}",
                            "valid_from": cert.get('notBefore'),
                            "valid_until": cert.get('notAfter'),
                            "is_expired": False,
                            "san": san
                        },
                        "connection": {
                            "tls_version": ssock.version(),
                            "cipher_suite": cipher[0]
                        },
                        "grade": "A"
                    }
        except Exception as e:
            return {"domain": domain, "error": f"Không thể lấy SSL certificate: {str(e)}"}

class TechScanner:
    """Bài 1.4 (Bonus): Phân tích HTTP Headers để nhận diện dấu vết công nghệ (Fingerprinting)"""
    @staticmethod
    def scan(domain: str) -> dict:
        try:
            url = f"http://{domain}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as response:
                headers = {k.lower(): v for k, v in response.getheaders()}
                technologies = []
                
                # Fingerprinting thông qua trường Server hoặc X-Powered-By
                server_header = headers.get('server', '')
                if 'nginx' in server_header.lower():
                    technologies.append({"name": "nginx", "category": "Web Server", "confidence": 100})
                if 'cloudflare' in server_header.lower():
                    technologies.append({"name": "Cloudflare", "category": "CDN", "confidence": 100})

                return {
                    "domain": domain,
                    "technologies": technologies if technologies else [{"name": "Generic Web", "category": "Web Server"}],
                    "headers": headers
                }
        except Exception as e:
            return {"domain": domain, "error": f"Không thể nhận diện công nghệ: {str(e)}"}

class DummyPassiveScanners:
    """Giả lập các scan type có sẵn từ trước của hệ thống"""
    @staticmethod
    def scan_dns(target): return {"target": target, "records": {"A": ["1.1.1.1"], "MX": ["mail.example.com"]}}
    @staticmethod
    def scan_whois(target): return {"target": target, "registrar": "GoDaddy", "owner": "Privacy Protection"}
    @staticmethod
    def scan_subdomain(target): return {"target": target, "subdomains": ["www", "api", "dev"]}


class CVEScanner:
    """Bài 6 (Bonus): Kiểm tra các dịch vụ mở để phát hiện lỗ hổng CVE tương ứng"""
    @staticmethod
    def check_cve(service_name: str, version: str) -> list:
        # Giả lập cơ sở dữ liệu lỗ hổng cục bộ của CVE cho các dịch vụ cũ
        cve_database = {
            "ssh": [
                {"cve_id": "CVE-2024-6387", "severity": "CRITICAL", "desc": "regreSSHion: RCE trong OpenSSH Server OpenBSD"},
                {"cve_id": "CVE-2023-38408", "severity": "HIGH", "desc": "RCE qua cơ chế chuyển tiếp tác nhân SSH Agent"}
            ],
            "postgresql": [
                {"cve_id": "CVE-2024-4317", "severity": "MEDIUM", "desc": "Lỗi leo thang đặc quyền privilege escalation"}
            ]
        }
        return cve_database.get(service_name.lower(), [])