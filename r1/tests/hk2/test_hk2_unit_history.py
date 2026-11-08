import unittest
from r1.scripts.hk2.hk2_unit_history import UnitHistoryError, assess_history


def row(n, outcome, unit='unit-a'):
    return {'unit_id': unit, 'attempt': n, 'outcome': outcome}


class UnitHistoryTest(unittest.TestCase):
    def test_first_or_one_cut_are_not_execution_authority(self):
        self.assertEqual(assess_history('unit-a', [])['state'], 'FRESH_ATTEMPT_POSSIBLE')
        result = assess_history('unit-a', [row(1, 'interrupted')])
        self.assertEqual((result['state'], result['cuts']), ('FRESH_ATTEMPT_POSSIBLE', 1))

    def test_second_cut_stops_and_completed_is_terminal(self):
        self.assertEqual(assess_history('unit-a', [row(1, 'interrupted'), row(2, 'interrupted')])['state'], 'STOP_CUT_TWICE')
        self.assertEqual(assess_history('unit-a', [row(1, 'interrupted'), row(2, 'complete')])['state'], 'COMPLETE')
        with self.assertRaises(UnitHistoryError): assess_history('unit-a', [row(1, 'complete'), row(2, 'interrupted')])
        with self.assertRaises(UnitHistoryError): assess_history('unit-a', [row(1, 'interrupted'), row(2, 'interrupted'), row(3, 'complete')])

    def test_missing_duplicates_wrong_identity_and_unknown_stop(self):
        for attempts in ([row(2, 'complete')], [row(1, 'interrupted'), row(1, 'complete')],
                         [row(True, 'complete')], [row(1, 'complete', 'another')],
                         [row(1, 'failed')], [row(1, 'running')]):
            with self.subTest(attempts=attempts), self.assertRaises(UnitHistoryError):
                assess_history('unit-a', attempts)
        with self.assertRaises(UnitHistoryError): assess_history('', [])
        with self.assertRaises(UnitHistoryError): assess_history('unit-a', None)


if __name__ == '__main__': unittest.main()
