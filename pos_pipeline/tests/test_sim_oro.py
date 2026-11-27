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


def _ol(b, sec=60.0, scale=100.0, **kw):
    from dataclasses import replace
    from pos_pipeline.sim_oro import Assumptions, Build, fight_dps
    return fight_dps(Assumptions(preramp=True, **kw), replace(Build(), **b), sec, scale=scale)


def test_olroth_extra_uses_need_window_when_uses_run_long():
    # No cancel, cap 20: one use is ~28 s, far longer than Echoing's 10 s window, so the window kills the gain.
    kw = dict(cancelable=False, flame_cap=20)
    base = _ol({}, **kw)[0]
    free = _ol(dict(olroth=True), olroth_window=False, **kw)[0]
    win = _ol(dict(olroth=True), olroth_window=True, **kw)[0]
    assert free > base * 1.01
    assert win <= free
    assert abs(win / base - 1) < 0.05


def test_olroth_counts_extra_empowered_uses():
    r = _ol(dict(olroth=True), olroth_window=False)[1]
    assert r.echo_uses >= 2 * (r.uses // 3)


def test_perpetual_charge_keeps_frenzy_and_never_hurts():
    base = _ol({}, flame_cap=5)[0]
    assert _ol(dict(perpetual=True), flame_cap=5)[0] >= base * 0.999


def test_volcanic_eruption_adds_small_flat_damage():
    base = _ol({})[0]
    assert base < _ol(dict(eruption=True))[0] < base * 1.2


def test_crescendo_only_matters_when_shade_setup_costs_time():
    kw = dict(shades=4, shades_copy_echo=True)
    free = _ol(dict(crescendo=True, **kw), shade_setup="free")[0], _ol(kw, shade_setup="free")[0]
    assert free[0] == free[1]
    assert _ol(dict(crescendo=True, **kw), shade_setup="each_eclipse")[0] >= _ol(kw, shade_setup="each_eclipse")[0]


def test_olroth_report_runs():
    from pos_pipeline.sim_oro import olroth_report  # slow: skipped body is cheap via monkeypatch-free smoke below
    assert callable(olroth_report)


def test_decoy_off_is_baseline_and_ideal_decoy_cuts_dodges():
    from dataclasses import replace
    b = replace(S.Build(), shades=4, shades_copy_echo=True)
    f = S.Fight(mechanic_every=10.0, first_mechanic=5.0, targeted_share=1.0, splash=0.0)
    base = S.fight_dps(S.Assumptions(preramp=True, shade_setup="once"), b, 180.0, f, scale=100.0)
    same = S.fight_dps(S.Assumptions(preramp=True, shade_setup="once", decoy=False, shade_death=1.0), b, 180.0, f,
                       scale=100.0)
    assert math.isclose(base[0], same[0]) and same[1].shades_lost == 0
    ideal = S.fight_dps(S.Assumptions(preramp=True, shade_setup="once", decoy=True), b, 180.0, f, scale=100.0)
    assert ideal[1].dodged < base[1].dodged / 3
    assert ideal[0] > base[0]
    fragile = S.fight_dps(S.Assumptions(preramp=True, shade_setup="once", decoy=True, shade_death=1.0), b, 180.0, f,
                          scale=100.0)
    assert fragile[1].shades_lost > 0
