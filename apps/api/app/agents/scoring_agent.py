from app.models.domain import ScoreReason, Signal


class ScoringAgent:
    def score(self, signals: list[Signal], reasons: list[ScoreReason]) -> tuple[int, int, int]:
        if not signals:
            return 0, 0, 0

        signal_strength = sum(signal.strength for signal in signals) / len(signals)
        reason_impact = sum(reason.impact for reason in reasons) / max(len(reasons), 1)
        diversity_bonus = min(len({signal.type for signal in signals}) * 3, 15)

        score = round((signal_strength * 0.55) + (reason_impact * 0.35) + diversity_bonus)
        score = min(score, 99)
        confidence = min(round(60 + len(signals) * 8 + len(reasons) * 4), 98)
        probability = min(round((score * 0.72) + (confidence * 0.28)), 99)
        return score, confidence, probability

