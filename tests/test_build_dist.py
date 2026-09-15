import unittest

import build_dist


class BuildDistTests(unittest.TestCase):
    def test_build_is_deterministic_and_has_no_timestamp(self):
        first = build_dist.build_text()
        second = build_dist.build_text()

        self.assertEqual(first, second)
        self.assertNotIn("Generated:", first)

    def test_committed_export_is_current(self):
        self.assertEqual(build_dist.build(check=True), 0)


if __name__ == "__main__":
    unittest.main()
