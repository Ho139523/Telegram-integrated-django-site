class FraudDetector:

    @staticmethod
    def calculate_risk_score(profile, amount):

        score = 0

        # Example rules
        if amount > 10000000:
            score += 40

        # TODO: add ML model later

        return score

