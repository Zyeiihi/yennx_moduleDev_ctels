class ScanAnalyzer:
    """Task 6.4: Compare historical scan results to detect new attack surfaces (Delta/Diff)"""
    @staticmethod
    def compare_port_scans(old_scan_results: dict, new_scan_results: dict) -> dict:
        if not old_scan_results or "open_ports" not in old_scan_results:
            return {"status": "baseline", "new_ports_detected": []}
            
        old_ports = {p["port"] for p in old_scan_results.get("open_ports", [])}
        new_ports = {p["port"] for p in new_scan_results.get("open_ports", [])}
        
        # Tìm các cổng mới xuất hiện ở lần quét sau mà lần trước không có
        diff_ports = new_ports - old_ports
        
        return {
            "status": "drifted" if diff_ports else "stable",
            "new_ports_detected": list(diff_ports)
        }