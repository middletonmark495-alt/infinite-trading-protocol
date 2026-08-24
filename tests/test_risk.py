import unittest

from services.analytics.risk import RiskInputs, score_portfolio


class RiskScoreTests(unittest.TestCase):
    def test_score_is_bounded_and_explainable(self):
        result = score_portfolio(RiskInputs(0.8, 0.7, 0.6, 0.2))
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
        self.assertEqual(set(result["components"]), {
            "concentration", "volatility", "liquidity", "non_stable_exposure"
        })

    def test_clamping(self):
        result = score_portfolio(RiskInputs(2, -1, 0.5, 0.5))
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)

    def test_more_stable_exposure_reduces_score(self):
        risky = score_portfolio(RiskInputs(0.5, 0.5, 0.5, 0.0))["score"]
        stable = score_portfolio(RiskInputs(0.5, 0.5, 0.5, 1.0))["score"]
        self.assertLess(stable, risky)


if __name__ == "__main__":
    unittest.main()
