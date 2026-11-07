import unittest
from r1.scripts.hk2.hk2_occupancy import OccupancyError, classify_processes


class OccupancyClassificationTests(unittest.TestCase):
    def test_startup_records_all_and_applies_exact_boundary(self):
        rows = [dict(pid=1, type='G', memory_mib=2000, owned_descendant=False),
                dict(pid=2, type='C', memory_mib=255, owned_descendant=False),
                dict(pid=3, type='C+G', memory_mib=256, owned_descendant=True)]
        out = classify_processes(rows, startup=True, ignore_below_mib=256)
        self.assertEqual([r['classification'] for r in out], ['graphics', 'below_threshold', 'blocking'])
        self.assertEqual([r['pid'] for r in out], [1, 2, 3])
        self.assertEqual([r['blocking'] for r in out], [False, False, True])

    def test_later_ignores_only_confirmed_own_descendant(self):
        rows = [dict(pid=1, type='C', memory_mib=1000, owned_descendant=True),
                dict(pid=2, type='C', memory_mib=1000, owned_descendant=False)]
        out = classify_processes(rows, startup=False, ignore_below_mib=256)
        self.assertEqual([r['classification'] for r in out], ['owned_descendant', 'blocking'])

    def test_unknown_fields_and_duplicates_stop(self):
        valid = dict(pid=1, type='C', memory_mib=300, owned_descendant=False)
        for change in [dict(memory_mib=None), dict(memory_mib=True), dict(type='?'),
                       dict(owned_descendant=None), dict(pid=0)]:
            with self.subTest(change=change), self.assertRaises(OccupancyError):
                classify_processes([dict(valid, **change)], startup=False, ignore_below_mib=256)
        with self.assertRaises(OccupancyError):
            classify_processes([valid, valid], startup=False, ignore_below_mib=256)

    def test_explicit_threshold_and_mode_are_required(self):
        for startup, threshold in [(1, 256), (True, True), (True, -1)]:
            with self.subTest(startup=startup, threshold=threshold), self.assertRaises(OccupancyError):
                classify_processes([], startup=startup, ignore_below_mib=threshold)


if __name__ == '__main__': unittest.main()
