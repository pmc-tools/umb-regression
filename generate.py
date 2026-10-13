"""Generate the umbi-made regression models and refresh manifest.json.

Models produced by other tools (Storm, Prism, Modest) should be dropped into
models/ by hand and listed in manifest.json with `"source"` naming the tool and
version that wrote them; this script only owns the entries with source "umbi".
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import umbi.ats
from umbi.ats import examples

HERE = Path(__file__).parent
MODELS = HERE / "models"
MANIFEST = HERE / "manifest.json"

GRID = """\
i.gx
.x..
...g
"""


def _two_state_dtmc() -> umbi.ats.SimpleAts:
    """Lazy chain: 0 -> {0: 1/2, 1: 1/2}, 1 absorbing; label `done` on state 1."""
    ats = umbi.ats.SimpleAts()
    ats.time = umbi.ats.TimeType.DISCRETE
    ats.num_players = 1
    ats.num_states = 2
    ats.initial_states = [0]
    c0 = ats.new_state_choice(state=0)
    ats.new_choice_branch(choice=c0, target=0, prob=Fraction(1, 2))
    ats.new_choice_branch(choice=c0, target=1, prob=Fraction(1, 2))
    c1 = ats.new_state_choice(state=1)
    ats.new_choice_branch(choice=c1, target=1)
    ats.new_ap_annotation(name="done").state_values = [False, True]
    ats.validate()
    return ats


def _three_state_ctmc() -> umbi.ats.SimpleAts:
    """CTMC 0 -(2.0)-> 1 -(3.0)-> 2, state 2 absorbing (exit rate 0)."""
    ats = umbi.ats.SimpleAts()
    ats.time = umbi.ats.TimeType.STOCHASTIC
    ats.num_players = 1
    ats.num_states = 3
    ats.initial_states = [0]
    exit_rates = [2.0, 3.0, 0.0]
    for state, target in [(0, 1), (1, 2)]:
        choice = ats.new_state_choice(state=state)
        ats.new_choice_branch(choice=choice, target=target, prob=1.0)
    choice = ats.new_state_choice(state=2)
    ats.new_choice_branch(choice=choice, target=2, prob=1.0)
    ats.state_to_exit_rate = exit_rates
    ats.validate()
    return ats


def _generated() -> dict[str, umbi.ats.SimpleAts]:
    return {
        "dtmc_two_state.umb": _two_state_dtmc(),
        "ctmc_chain.umb": _three_state_ctmc(),
        "mdp_grid_3x4.umb": examples.grid(GRID),
    }


def main() -> None:
    MODELS.mkdir(exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"models": {}}
    manifest["models"] = {k: v for k, v in manifest["models"].items() if v.get("source") != "umbi"}
    for name, ats in _generated().items():
        umbi.ats.write(ats, MODELS / name)
        manifest["models"][name] = {
            "source": "umbi",
            "states": ats.num_states,
            "branches": ats.num_branches,
        }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
