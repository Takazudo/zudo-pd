import json
import unittest

import c5_dev_site


class CatalogNavigationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = c5_dev_site.outputs()
        cls.audit = json.loads((c5_dev_site.HERE / "c5-link-audit.json").read_text())

    def test_one_scoped_filterable_catalog_preserves_all_source_rows(self):
        page = self.outputs[c5_dev_site.DOCS / "catalog/lines.mdx"]
        pd = json.loads((c5_dev_site.ROOT / ".claude/skills/component-spec-audit/references/inventory.json").read_text())
        led = json.loads((c5_dev_site.LED / ".claude/skills/component-spec-audit/references/inventory.json").read_text())
        self.assertEqual(page.count("| PD:line-"), len(pd["lines"]))
        self.assertEqual(page.count("| LED:line-"), len(led["lines"]))
        self.assertIn('id="catalog-line-query"', page)
        self.assertIn('id="catalog-line-status"', page)
        self.assertIn('aria-live="polite"', page)
        self.assertIn('/assets/client/catalog-line-filter.js', page)
        for inventory, scope in ((pd, "PD"), (led, "LED")):
            for line in inventory["lines"]:
                self.assertEqual(page.count(f"| {scope}:{line['line_id']} |"), 1)
        self.assertIn("PD:line-c2678061", page)
        self.assertIn("LED:line-c2678061", page)
        self.assertNotIn("/assets/led-lamp/", page)

    def test_all_authored_routes_and_held_links_remain_scoped(self):
        pages = {str(path.relative_to(c5_dev_site.DOCS)): content
                 for path, content in self.outputs.items()
                 if path.is_relative_to(c5_dev_site.DOCS / "led-lamp")}
        self.assertEqual(len(pages), 34)
        by_source = {row["source_path"]: row for row in c5_dev_site.source_rows()}
        self.assertEqual(len([row for row in by_source.values() if row["class"] == "authored"]), 34)
        def content_for(source):
            row = by_source[source.removeprefix("products/led-lamp/")]
            route = row["proposed_route"].removeprefix("/docs/").strip("/")
            name = route + ("/index.mdx" if row["source_path"].endswith("/index.mdx") else ".mdx")
            return pages[name]
        authored = [row for row in self.audit["route_links"] if row["target_class"] == "authored"]
        generated = [row for row in self.audit["route_links"] if row["target_class"] == "generated"]
        self.assertEqual((len(authored), len(generated), len(self.audit["asset_links"])), (76, 60, 12))
        for row in authored:
            self.assertIn(row["proposed_route"], content_for(row["source"]))
        for row in generated + self.audit["asset_links"]:
            self.assertIn(c5_dev_site.OLD_HOST + row["url"], content_for(row["source"]))
        self.assertEqual(self.audit["old_routes_colliding_with_pd"],
                         ["/docs/architecture/", "/docs/architecture/board-p/", "/docs/research/"])
        for row in by_source.values():
            if row["class"] == "authored":
                self.assertIn(c5_dev_site.OLD_HOST + row["old_route"],
                              content_for("products/led-lamp/" + row["source_path"]))


if __name__ == "__main__":
    unittest.main()
