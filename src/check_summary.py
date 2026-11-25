"""Check run_summary(), the epsilon setting and the time limit per run.

Run:  venv/Scripts/python src/check_summary.py
"""

import copy
import sys

from horizons import ROOT, load_state
from simulate import DAY_S, build_simulation, load_config, run, run_summary

CONFIG = ROOT / "configs" / "single_run.json"


def with_settings(config, **changes):
    """Copy of config with some second-moon settings replaced."""
    config = copy.deepcopy(config)
    config["second_moon"].update(changes)
    return config


def check_same_ending(state, config):
    """run() and run_summary() must agree for every kind of ending."""
    cases = {
        "survived": {**config, "duration_days": 365},
        "collision": with_settings(config, eccentricity=0.97, true_anomaly_deg=180.0),
        "ejection": with_settings(config, distance_lunar=6.0),
    }
    for expected, case in cases.items():
        full, short = run(state, case), run_summary(state, case)
        same = (full.outcome == short.outcome == expected
                and full.involved == short.involved
                and full.end_time_s == short.end_time_s)
        if not same:
            return False, f"{expected}: {full.outcome} vs {short.outcome}"
    return True, "survived, collision and ejection are identical"


def check_epsilon(state, config):
    """The accuracy setting must reach the integrator and change the path a little."""
    normal = {**config, "bodies": ["sun", "earth", "moon"], "duration_days": 365}
    strict = {**normal, "epsilon": 1e-11}
    values = [build_simulation(state, c).integrator.epsilon for c in (normal, strict)]
    a, b = run(state, normal), run(state, strict)
    shift = float(abs(a.relative("moon") - b.relative("moon")).max())
    ok = values == [1e-9, 1e-11] and 0 < shift < 0.001
    return ok, f"epsilon {values}, Moon differs by at most {shift * 1e6:.3g} mm in a year"


def check_time_limit(state, config):
    result = run_summary(state, {**config, "max_seconds": 0.0})
    ok = result.outcome == "timeout" and result.end_time_s < config["duration_days"] * DAY_S
    return ok, f"{result.outcome} after {result.end_time_s / DAY_S:.2f} simulated days"


def check_finished_run_is_not_timeout(state, config):
    """A run that reaches its end counts as survived, however slow it was."""
    # Zero length: the first output is also the last, with no time left.
    result = run_summary(state, {**config, "duration_days": 0, "max_seconds": 0.0})
    return result.outcome == "survived", result.outcome


def main():
    state, config = load_state(), load_config(CONFIG)
    passed = True
    for label, check in (
        ("Summary matches full run", check_same_ending),
        ("Epsilon setting", check_epsilon),
        ("Time limit", check_time_limit),
        ("Finished run", check_finished_run_is_not_timeout),
    ):
        ok, detail = check(state, config)
        passed &= bool(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}", flush=True)
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
