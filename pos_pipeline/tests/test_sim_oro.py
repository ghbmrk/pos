import math

from pos_pipeline import sim_oro as S


def _dps(**kw):
    return S.fight_dps(S.Assumptions(preramp=True, **kw), S.Build(), 60.0)[0]


def test_failures_reduce_dps():
    base = _dps()
    assert _dps(echo_mode="first") < base
    assert _dps(echo_mode="none") <= _dps(echo_mode="first")
    assert _dps(oros_stack=False) < base
    assert _dps(flame_cap=5) < base


def test_no_mercy_average_matches_closed_form():
    # Concentration = 30% of life; the bonus ramps 0->40% over the first 30% of damage, then stays at 40%.
    assert math.isclose(S.no_mercy_avg(), 1.33, abs_tol=0.01)


def test_static_stack_reproduced_without_mechanics():
    # No mechanics, pre-ramped: time-domain gain over plain Infernal Step should be near the doc's static x25
    # (x137 / x5.5), less Echoing and Eclipse downtime.
    f = S.Fight(mechanic_every=1e9, first_mechanic=1e9)
    plain = S.Build(two_oros=False, witchhunter=False, eclipse=False, echoing=False)
    a = S.Assumptions(preramp=True)
    gain = S.fight_dps(a, S.Build(), 180.0, f)[0] / S.fight_dps(a, plain, 180.0, f)[0]
    assert 15 < gain < 27
