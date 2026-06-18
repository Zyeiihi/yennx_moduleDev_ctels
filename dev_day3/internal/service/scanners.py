# FILE: internal/service/scanners.py
"""
Scanner implementations for each scan type.
All scanners expose a static `scan(target) -> dict` method.
"""
import json
import socket
import ssl
import time
import urllib.request
import urllib.parse

try:
    import dns.resolver
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False


# ---------------------------------------------------------------------------
# Safety helpers
# ---------------------------------------------------------------------------

def is_local_host(ip: str) -> bool:
    """
    Security check: return True for private/loopback address ranges.
    Active scans (port) are ONLY permitted on local/private IPs.
    """
    local_prefixes = [
        "127.", "10.", "192.168.",
        "172.16.", "172.17.", "172.18.", "172.19.", "172.20.",
        "172.21.", "172.22.", "172.23.", "172.24.", "172.25.",
        "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31."
    ]
    return any(ip.startswith(p) for p in local_prefixes) or ip == "localhost"


# ---------------------------------------------------------------------------
# DNS Scanner — real lookups using dnspython or socket fallback
# ---------------------------------------------------------------------------

class DNSScanner:
    """Performs real DNS record lookups (A, MX, NS, TXT)."""
    @staticmethod
    def scan(domain: str) -> dict:
        records = {}
        if HAS_DNSPYTHON:
            for rtype in ("A", "MX", "NS", "TXT"):
                try:
                    answers = dns.resolver.resolve(domain, rtype, lifetime=5)
                    records[rtype] = [str(r) for r in answers]
                except Exception:
                    records[rtype] = []
        else:
            # Fallback: only A records via socket
            try:
                infos = socket.getaddrinfo(domain, None)
                records["A"] = list({i[4][0] for i in infos})
            except Exception:
                records["A"] = []

        return {"target": domain, "records": records}


# ---------------------------------------------------------------------------
# WHOIS Scanner — socket-based WHOIS query
# ---------------------------------------------------------------------------

class WhoisScanner:
    """Performs a basic WHOIS query via the standard port 43."""
    WHOIS_SERVERS = {
        "com": "whois.verisign-grs.com",
        "net": "whois.verisign-grs.com",
        "org": "whois.pir.org",
        "io":  "whois.nic.io",
        "co":  "whois.nic.co",
    }

    @staticmethod
    def scan(domain: str) -> dict:
        tld = domain.rsplit(".", 1)[-1].lower()
        server = WhoisScanner.WHOIS_SERVERS.get(tld, "whois.iana.org")
        try:
            sock = socket.create_connection((server, 43), timeout=5)
            sock.sendall(f"{domain}\r\n".encode())
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            sock.close()
            text = response.decode("utf-8", errors="ignore")

            # Parse a few key fields
            def _extract(keyword):
                for line in text.splitlines():
                    if line.strip().lower().startswith(keyword.lower()):
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            return parts[1].strip()
                return "N/A"

            return {
                "target": domain,
                "registrar": _extract("Registrar:"),
                "creation_date": _extract("Creation Date:"),
                "expiry_date": _extract("Registry Expiry Date:"),
                "status": _extract("Domain Status:"),
                "raw": text[:500],  # Truncated raw output
            }
        except Exception as e:
            return {"target": domain, "error": f"WHOIS query failed: {str(e)}"}


# ---------------------------------------------------------------------------
# Subdomain Scanner — passive certificate transparency lookup
# ---------------------------------------------------------------------------

class SubdomainScanner:
    """Discovers subdomains using crt.sh certificate transparency logs."""
    @staticmethod
    def scan(domain: str) -> dict:
        try:
            encoded = urllib.parse.quote(domain)
            url = f"https://crt.sh/?q=%.{encoded}&output=json"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            subdomains = sorted({
                entry["name_value"].strip().lstrip("*.")
                for entry in data
                if "name_value" in entry
            })
            return {"target": domain, "subdomains": subdomains[:50]}
        except Exception as e:
            return {"target": domain, "subdomains": [], "error": f"crt.sh query failed: {str(e)}"}


# ---------------------------------------------------------------------------
# IP Scanner — GeoIP + ASN via ip-api.com
# ---------------------------------------------------------------------------

class IPScanner:
    """Retrieves geolocation and ASN information for IP addresses."""
    @staticmethod
    def scan(ip_address: str) -> dict:
        if is_local_host(ip_address):
            return {
                "ip_address": ip_address,
                "geolocation": {
                    "country": "Local", "city": "Internal Network", "isp": "Private LAN"
                },
                "asn": {"number": 0, "name": "PRIVATE", "description": "Private IP range"},
                "reverse_dns": "localhost",
            }
        try:
            url = (
                f"http://ip-api.com/json/{ip_address}"
                f"?fields=status,country,countryCode,regionName,city,lat,lon,isp,org,as"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            if data.get("status") == "success":
                as_info = data.get("as", "")
                asn_num = int(as_info.split()[0].replace("AS", "")) if as_info else 0
                # Reverse DNS
                try:
                    reverse_dns = socket.gethostbyaddr(ip_address)[0]
                except Exception:
                    reverse_dns = "N/A"
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
                        "org": data.get("org"),
                    },
                    "asn": {
                        "number": asn_num,
                        "name": data.get("isp", "").upper().replace(" ", ""),
                        "description": data.get("org"),
                    },
                    "reverse_dns": reverse_dns,
                }
        except Exception:
            pass
        return {"ip_address": ip_address, "error": "Failed to retrieve IP information"}


# ---------------------------------------------------------------------------
# Port Scanner — TCP connect scan (LOCALHOST / PRIVATE IPs ONLY)
# ---------------------------------------------------------------------------

class PortScanner:
    """
    Active TCP port scanner.
    SECURITY: Only allowed on private/loopback IP ranges.
    """
    COMMON_PORTS = [21, 22, 25, 53, 80, 443, 3000, 3306, 5432, 6379, 8080, 8443, 27017]
    SERVICES = {
        21: "ftp", 22: "ssh", 25: "smtp", 53: "dns",
        80: "http", 443: "https", 3000: "http-dev",
        3306: "mysql", 5432: "postgresql", 6379: "redis",
        8080: "http-alt", 8443: "https-alt", 27017: "mongodb",
    }

    @staticmethod
    def scan(ip_address: str) -> dict:
        # SECURITY GUARDRAIL: block external IPs
        if not is_local_host(ip_address):
            raise PermissionError(
                "SECURITY: Active port scanning is ONLY permitted on "
                "private/localhost IP addresses (RFC 1918)."
            )

        open_ports = []
        start = time.time()
        for port in PortScanner.COMMON_PORTS:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            if s.connect_ex((ip_address, port)) == 0:
                version = ""
                try:
                    if port == 80:
                        s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
                        version = s.recv(200).decode("utf-8", errors="ignore").split("\r\n")[0]
                except Exception:
                    pass
                open_ports.append({
                    "port": port,
                    "protocol": "tcp",
                    "state": "open",
                    "service": PortScanner.SERVICES.get(port, "unknown"),
                    "version": version or "Service detected",
                })
            s.close()

        duration_ms = int((time.time() - start) * 1000)
        total = len(PortScanner.COMMON_PORTS)
        return {
            "ip_address": ip_address,
            "open_ports": open_ports,
            "closed_ports": total - len(open_ports),
            "total_scanned": total,
            "scan_duration_ms": duration_ms,
        }


# ---------------------------------------------------------------------------
# SSL/TLS Scanner
# ---------------------------------------------------------------------------

class SSLScanner:
    """Audits TLS configuration and SSL certificate details."""
    @staticmethod
    def scan(domain: str) -> dict:
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    subject = dict(x[0] for x in cert.get("subject", []))
                    issuer  = dict(x[0] for x in cert.get("issuer", []))
                    san = [x[1] for x in cert.get("subjectAltName", []) if x[0] == "DNS"]

                    # Parse expiry
                    not_after_str = cert.get("notAfter", "")
                    not_before_str = cert.get("notBefore", "")
                    try:
                        import datetime as dt
                        not_after = dt.datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z")
                        days_left = (not_after - dt.datetime.utcnow()).days
                        is_expired = days_left < 0
                    except Exception:
                        days_left = -1
                        is_expired = False

                    # TLS grade heuristic
                    tls_ver = ssock.version() or ""
                    grade = "A" if "TLS 1.3" in tls_ver or "TLS 1.2" in tls_ver else "B"

                    return {
                        "domain": domain,
                        "certificate": {
                            "subject": f"CN={subject.get('commonName', domain)}",
                            "issuer": (
                                f"CN={issuer.get('commonName', '')}, "
                                f"O={issuer.get('organizationName', '')}"
                            ),
                            "valid_from": not_before_str,
                            "valid_until": not_after_str,
                            "days_until_expiry": days_left,
                            "is_expired": is_expired,
                            "is_self_signed": subject == issuer,
                            "san": san,
                        },
                        "connection": {
                            "tls_version": tls_ver,
                            "cipher_suite": cipher[0] if cipher else "unknown",
                            "key_exchange": cipher[1] if cipher and len(cipher) > 1 else "unknown",
                        },
                        "grade": grade,
                        "issues": ["Certificate expired"] if is_expired else [],
                    }
        except Exception as e:
            return {"domain": domain, "error": f"SSL scan failed: {str(e)}"}


# ---------------------------------------------------------------------------
# Tech Fingerprint Scanner
# ---------------------------------------------------------------------------

class TechScanner:
    """Fingerprints web technologies via HTTP response headers and body."""
    SIGNATURES = {
        "nginx":      ("server", "nginx",      "Web Server"),
        "apache":     ("server", "apache",     "Web Server"),
        "cloudflare": ("server", "cloudflare", "CDN"),
        "iis":        ("server", "iis",        "Web Server"),
        "express":    ("x-powered-by", "express", "Web Framework"),
        "php":        ("x-powered-by", "php",      "Language"),
        "django":     ("x-frame-options", "sameorigin", "Web Framework"),
        "react":      (None, "react",  "JavaScript Framework"),
        "vue":        (None, "vue.js", "JavaScript Framework"),
    }

    @staticmethod
    def scan(domain: str) -> dict:
        technologies = []
        headers_out = {}
        for scheme in ("https", "http"):
            try:
                url = f"{scheme}://{domain}"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    headers_out = {k.lower(): v for k, v in resp.getheaders()}
                    body_snippet = resp.read(4096).decode("utf-8", errors="ignore").lower()

                for key, (header, value, category) in TechScanner.SIGNATURES.items():
                    if header:
                        hval = headers_out.get(header, "").lower()
                        if value in hval:
                            technologies.append({
                                "name": key,
                                "category": category,
                                "version": None,
                                "confidence": 100,
                            })
                    else:
                        if value in body_snippet:
                            technologies.append({
                                "name": key,
                                "category": category,
                                "version": None,
                                "confidence": 80,
                            })
                break  # stop after first successful response
            except Exception:
                continue

        if not technologies:
            technologies = [{"name": "Generic Web", "category": "Web Server", "confidence": 50}]

        return {
            "domain": domain,
            "technologies": technologies,
            "headers": headers_out,
            "meta_tags": {},
        }


# ---------------------------------------------------------------------------
# CVE Scanner — correlates open ports with known CVEs
# ---------------------------------------------------------------------------

class CVEScanner:
    """Correlates discovered services with known CVE vulnerabilities."""
    # Local CVE knowledge base (mock data for educational purposes)
    CVE_DB = {
        "ssh": [
            {"cve_id": "CVE-2024-6387", "severity": "CRITICAL",
             "description": "regreSSHion: RCE in OpenSSH Server on Linux glibc systems"},
            {"cve_id": "CVE-2023-38408", "severity": "HIGH",
             "description": "RCE via ssh-agent forwarding mechanism"},
        ],
        "http": [
            {"cve_id": "CVE-2021-41773", "severity": "CRITICAL",
             "description": "Apache HTTP Server path traversal and RCE"},
        ],
        "postgresql": [
            {"cve_id": "CVE-2024-4317", "severity": "MEDIUM",
             "description": "Privilege escalation in PostgreSQL"},
        ],
        "redis": [
            {"cve_id": "CVE-2022-0543", "severity": "CRITICAL",
             "description": "Lua sandbox escape in Redis"},
        ],
        "ftp": [
            {"cve_id": "CVE-2010-4221", "severity": "HIGH",
             "description": "ProFTPD stack-based buffer overflow"},
        ],
    }

    @staticmethod
    def scan_from_ports(port_results: list) -> list:
        """Given a list of open-port dicts, return matching CVEs."""
        findings = []
        for port_info in port_results:
            service = port_info.get("service", "").lower()
            cves = CVEScanner.CVE_DB.get(service, [])
            if cves:
                findings.append({
                    "service": service,
                    "port": port_info.get("port"),
                    "cves": cves,
                })
        return findings

    @staticmethod
    def check_cve(service_name: str, version: str = "") -> list:
        return CVEScanner.CVE_DB.get(service_name.lower(), [])
