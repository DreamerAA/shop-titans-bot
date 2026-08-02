import unittest

from bot.windowing import ClientRect, GameWindow, WindowLocator


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


class WindowIdentityTests(unittest.TestCase):
    @staticmethod
    def window(process_name, title):
        rect = ClientRect(0, 0, 1920, 1080)
        return GameWindow(1, 2, process_name, title, rect, rect, False)

    def test_rejects_browser_title_when_process_name_is_known(self):
        browser = self.window("firefox.exe", "Your Heroes - Shop Titans Hero Tracker")

        matches = WindowLocator._matches_window_identity(
            browser,
            "shoptitan.exe",
            "shop titans",
        )

        self.assertFalse(matches)

    def test_uses_title_only_when_process_name_is_unavailable(self):
        unreadable_process = self.window(None, "Shop Titans")

        matches = WindowLocator._matches_window_identity(
            unreadable_process,
            "shoptitan.exe",
            "shop titans",
        )

        self.assertTrue(matches)


if __name__ == "__main__":
    unittest.main()
