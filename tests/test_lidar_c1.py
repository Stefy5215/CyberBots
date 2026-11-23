import unittest

from lidar_c1 import decode_measurement_node, is_standard_scan_descriptor


class LidarC1ProtocolTests(unittest.TestCase):
    def test_decodes_standard_measurement_node(self):
        # Quality 20, start-of-revolution, 90 degrees, and 1000 mm.
        raw = bytes((0x51, 0x01, 0x2D, 0xA0, 0x0F))
        node = decode_measurement_node(raw)

        self.assertIsNotNone(node)
        self.assertEqual(node.quality, 20)
        self.assertAlmostEqual(node.angle_deg, 90.0)
        self.assertAlmostEqual(node.distance_mm, 1000.0)
        self.assertTrue(node.starts_revolution)

    def test_rejects_bad_checkbit_and_sync_pair(self):
        self.assertIsNone(decode_measurement_node(bytes((0x51, 0x00, 0x2D, 0xA0, 0x0F))))
        self.assertIsNone(decode_measurement_node(bytes((0x50, 0x01, 0x2D, 0xA0, 0x0F))))

    def test_accepts_c1_standard_scan_descriptor(self):
        descriptor = bytes((0xA5, 0x5A, 0x05, 0x00, 0x00, 0x40, 0x81))
        self.assertTrue(is_standard_scan_descriptor(descriptor))
        self.assertFalse(is_standard_scan_descriptor(descriptor[:-1] + b"\x82"))


if __name__ == "__main__":
    unittest.main()