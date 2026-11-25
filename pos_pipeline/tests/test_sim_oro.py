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


def _x(b, **kw):
    from dataclasses import replace
    from pos_pipeline.sim_oro import Assumptions, Build, fight_dps, rare_dps
    bb = replace(Build(), **b)
    return fight_dps(Assumptions(preramp=True, **kw), bb, 60.0)[0] / rare_dps(bb)


def test_host_options_off_by_default_and_help_when_on():
    base = _x({})
    assert 25 < base < 45  # unchanged baseline
    assert _x(dict(thrilling_chase=True)) > base
    assert _x(dict(shades=3)) > base
    assert _x(dict(shades=3, shades_copy_echo=True)) > _x(dict(shades=3))
    assert _x(dict(time_snap=True)) >= base


def test_shades_need_echo_replay_to_matter_more_and_ignore_no_eclipse():
    assert _x(dict(shades=3, eclipse=False)) == _x(dict(eclipse=False))
    assert _x(dict(shades=3, shades_copy_echo=True), echo_mode="none") == _x(dict(shades=3), echo_mode="none")


def test_witchhunter_slows_boss_mechanics():
    from dataclasses import replace
    from pos_pipeline.sim_oro import Assumptions, Build, Fight, fight_dps
    f = Fight(mechanic_every=15.0, first_mechanic=7.5)
    a = Assumptions(preramp=True)
    slow = fight_dps(a, replace(Build(), boss_cdr_less=0.5), 180.0, f, scale=100.0)[1]
    base = fight_dps(a, Build(), 180.0, f, scale=100.0)[1]
    assert slow.mechanics / slow.ttk < base.mechanics / base.ttk


def test_defence_report_runs():
    from pos_pipeline.sim_oro import defence_report
    assert "Witchhunter" in defence_report()
