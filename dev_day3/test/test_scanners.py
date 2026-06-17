# ĐƯỜNG DẪN FILE: test/test_scanners.py
import unittest
from internal.model.asset import Asset
from internal.storage.memory import db
from internal.service.scanners import is_local_host, PortScanner

class TestEASMComponents(unittest.TestCase):
    
    def setUp(self):
        # Reset dữ liệu sạch trước mỗi ca kiểm thử
        db._assets = {}
        db._scan_jobs = {}

    def test_local_host_validation(self):
        """Hàm test bắt đầu bằng test_ -> HỢP LỆ"""
        self.assertTrue(is_local_host("127.0.0.1"))
        self.assertTrue(is_local_host("192.168.1.1"))
        self.assertFalse(is_local_host("8.8.8.8"))

    def test_storage_asset_operations(self):
        """Hàm test bắt đầu bằng test_ -> HỢP LỆ"""
        asset = Asset(name="127.0.0.1", asset_type="ip")
        db.save_asset(asset)
        
        retrieved = db.get_asset(asset.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "127.0.0.1")

    def test_security_port_scanner_block(self):
        """Hàm test bắt đầu bằng test_ -> HỢP LỆ"""
        with self.assertRaises(PermissionError):
            PortScanner.scan("8.8.8.8")

if __name__ == '__main__':
    unittest.main()