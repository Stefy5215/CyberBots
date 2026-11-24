import unittest

from lidar_c1 import ScanNode
from robot_c3_lidar import decide_command, summarize_scan


def node(angle: float, distance: float) -> ScanNode:
    return ScanNode(quality=20, angle_deg=angle, distance_mm=distance, starts_revolution=False)


class RobotNavigationTests(unittest.TestCase):
    def test_stops_when_front_is_critically_close(self):
        command = decide_command({"front": 250, "left": 1200, "right": 900}, 75)
        self.assertEqual(command[1], 0)

    def test_turns_toward_more_open_side_and_slows(self):
        angle, speed, _ = decide_command({"front": 600, "left": 1500, "right": 700}, 75)
        self.assertEqual(angle, 25)
        self.assertLess(speed, 75)

    def test_stops_if_front_or_lateral_data_is_missing(self):
        self.assertEqual(decide_command({"front": None, "left": 1000, "right": 1000}, 75)[1], 0)
        self.assertEqual(decide_command({"front": 2000, "left": None, "right": 1000}, 75)[1], 0)

    def test_summarizes_front_and_side_angles_in_millimeters(self):
        distances = summarize_scan([node(2, 700), node(90, 1200), node(270, 900)])
        self.assertEqual(distances, {"front": 700, "left": 1200, "right": 900})


if __name__ == "__main__":
    unittest.main()