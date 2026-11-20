import unittest

import c5_dev_site
from c5_editorial import EDITORIAL


class EditorialTest(unittest.TestCase):
    def test_exact_scope_and_operational_context(self):
        outputs = c5_dev_site.outputs()
        led_pages = {path: content for path, content in outputs.items()
                     if path.is_relative_to(c5_dev_site.DOCS / "led-lamp")}
        marked = {path for path, content in led_pages.items()
                  if "**Integrated context.**" in content}
        self.assertEqual(len(led_pages), 38)
        bridges = {path: content for path, content in led_pages.items()
                   if path.is_relative_to(c5_dev_site.DOCS / "led-lamp/components")}
        self.assertEqual(len(bridges), 4)
        self.assertTrue(all("**Navigation pointer.**" in content
                            and "**Integrated context.**" not in content
                            for content in bridges.values()))
        self.assertEqual(len(marked), len(EDITORIAL), 25)
        held = {path for path, content in led_pages.items() if "**Held legacy references.**" in content}
        self.assertEqual(len(held), 9)
        for name in ("architecture/board-p.mdx", "getting-started/installation.mdx",
                     "how-to/ci-cloudflare-setup.mdx", "power/charger-compatibility.mdx"):
            content = led_pages[c5_dev_site.DOCS / "led-lamp" / name]
            self.assertIn("**Integrated context.**", content)
        cloudflare = led_pages[c5_dev_site.DOCS / "led-lamp/how-to/ci-cloudflare-setup.mdx"]
        self.assertIn("No LED-host redirect or cutover is authorized here", cloudflare)
        board = led_pages[c5_dev_site.DOCS / "led-lamp/architecture/board-p.mdx"]
        self.assertIn("neither P15 nor PD20's Board P r3", board)
        self.assertIn('title: "Historical LED Board P net table"', board)
        self.assertIn("[original LED page](https://zudo-led-lamp.takazudomodular.com/docs/architecture/board-p/)", board)


if __name__ == "__main__":
    unittest.main()
