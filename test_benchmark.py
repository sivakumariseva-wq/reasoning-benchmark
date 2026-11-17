import unittest

from benchmark import baseline_solver, extract_answer, is_correct, run


class TestExtraction(unittest.TestCase):
    def test_explicit_answer_line(self):
        self.assertEqual(extract_answer("3 + 4 = 7\nAnswer: 7"), 7)

    def test_last_explicit_answer_wins(self):
        self.assertEqual(extract_answer("Answer: 5 ... wait, recheck. Answer: 6"), 6)

    def test_boxed(self):
        self.assertEqual(extract_answer(r"so the result is \boxed{42}"), 42)

    def test_commas_and_decimals(self):
        self.assertEqual(extract_answer("Answer: 12,600"), 12600)
        self.assertEqual(extract_answer("Answer: 2.5"), 2.5)

    def test_fallback_last_number(self):
        self.assertEqual(extract_answer("first 10 then 20 then 30"), 30)

    def test_no_number(self):
        self.assertIsNone(extract_answer("I am not sure."))


class TestScoring(unittest.TestCase):
    def test_is_correct(self):
        self.assertTrue(is_correct(22.0, 22))
        self.assertFalse(is_correct(None, 22))
        self.assertFalse(is_correct(21.0, 22))

    def test_run_reports_accuracy(self):
        problems = [
            {"id": "a", "category": "x", "question": "2 and 3", "answer": 5},
            {"id": "b", "category": "x", "question": "2 and 3", "answer": 6},
        ]
        report = run(problems, baseline_solver)
        self.assertEqual(report["accuracy"], 0.5)
        self.assertEqual(report["failures"][0]["id"], "b")


if __name__ == "__main__":
    unittest.main()
