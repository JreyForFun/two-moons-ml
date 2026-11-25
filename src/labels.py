"""Turn how a run ended into one label.

The raw outcome and the bodies involved are always saved too, so labels can be
changed later without simulating again.
"""

LABELS = ("survived", "hit_earth", "hit_moon", "ejected", "moon_lost", "other",
          "timeout", "error")


def make_label(outcome, involved):
    """Label for one run. involved holds the names of the bodies in the event."""
    if outcome in ("survived", "timeout", "error"):
        return outcome
    bodies = frozenset(involved)
    if outcome == "collision":
        if bodies == {"earth", "moon2"}:
            return "hit_earth"
        if bodies == {"moon", "moon2"}:
            return "hit_moon"
        if bodies == {"earth", "moon"}:
            return "moon_lost"
    if outcome == "ejection":
        if bodies == {"moon2"}:
            return "ejected"
        if bodies == {"moon"}:
            return "moon_lost"
    return "other"
