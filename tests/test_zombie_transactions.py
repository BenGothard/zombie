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


if __name__ == "__main__":
    unittest.main()

