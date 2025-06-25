import io
import unittest
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from zombie_transactions import find_recurring_transactions


SAMPLE_CSV = """Date,Description,Amount
2024-01-15,ServiceA,10.00
2024-02-15,ServiceA,10.00
2024-03-15,ServiceA,10.00
2024-01-10,ServiceB,5.00
2024-02-11,ServiceC,7.00
2024-03-11,ServiceC,7.00
"""


class ZombieTest(unittest.TestCase):
    def test_recurring_detection(self):
        with io.StringIO(SAMPLE_CSV) as f:
            # write to temp file because function expects a path
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tf:
                tf.write(f.getvalue())
                path = tf.name

            results = find_recurring_transactions(path, months_threshold=2)
            self.assertIn(("ServiceA", 10.0), results)
            self.assertIn(("ServiceC", 7.0), results)
            self.assertNotIn(("ServiceB", 5.0), results)

    def test_ignore_invalid_rows(self):
        invalid_csv = """Date,Description,Amount
2024-01-01,ServiceX,9.99
bad-date,ServiceX,9.99
2024-02-01,ServiceX,9.99
2024-03-01,,10
2024-03-05,ServiceX,notanumber
"""
        with io.StringIO(invalid_csv) as f:
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tf:
                tf.write(f.getvalue())
                path = tf.name

            results = find_recurring_transactions(path, months_threshold=2)
            self.assertIn(("ServiceX", 9.99), results)

    def test_txt_input(self):
        with io.StringIO(SAMPLE_CSV) as f:
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False) as tf:
                tf.write(f.getvalue())
                path = tf.name

            results = find_recurring_transactions(path, months_threshold=2)
            self.assertIn(("ServiceA", 10.0), results)


if __name__ == "__main__":
    unittest.main()

