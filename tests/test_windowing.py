import unittest

from bot.windowing import ClientRect


class ClientRectTests(unittest.TestCase):
    def test_translates_between_client_and_desktop_coordinates(self):
        rect = ClientRect(left=960, top=31, width=960, height=1000)

        self.assertEqual((1080, 271), rect.to_desktop((120, 240)))
        self.assertEqual((120, 240), rect.to_client((1080, 271)))

    def test_builds_mss_monitor_mapping(self):
        rect = ClientRect(left=-1920, top=0, width=1920, height=1080)

        self.assertEqual(
            {"left": -1920, "top": 0, "width": 1920, "height": 1080},
            rect.as_mss_monitor(),
        )


if __name__ == "__main__":
    unittest.main()
