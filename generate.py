"""Generate the umbi-made regression models and refresh manifest.json.

Models produced by other tools (Storm, Prism, Modest) should be dropped into
models/ by hand and listed in manifest.json with `"source"` naming the tool and
version that wrote them; this script only owns the entries with source "umbi".
"""
from __future__ import annotations

import json
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
    ats.new_choice_branch(choice=c0, target=0, prob=0.5)
    ats.new_choice_branch(choice=c0, target=1, prob=0.5)
    c1 = ats.new_state_choice(state=1)
    ats.new_choice_branch(choice=c1, target=1)
    ats.new_ap_annotation(name="done").state_values = [False, True]
    ats.validate()
    return ats


def _initial_not_zero() -> umbi.ats.SimpleAts:
    """Chain 0 <- 1 -> 2 with initial state 1 (Modest requires state 0 to be initial)."""
    ats = umbi.ats.SimpleAts()
    ats.time = umbi.ats.TimeType.DISCRETE
    ats.num_players = 1
    ats.num_states = 3
    ats.initial_states = [1]
    c0 = ats.new_state_choice(state=0)
    ats.new_choice_branch(choice=c0, target=0)
    c1 = ats.new_state_choice(state=1)
    ats.new_choice_branch(choice=c1, target=0, prob=0.5)
    ats.new_choice_branch(choice=c1, target=2, prob=0.5)
    c2 = ats.new_state_choice(state=2)
    ats.new_choice_branch(choice=c2, target=2)
    ats.validate()
    return ats


def _three_state_ctmc() -> umbi.ats.SimpleAts:
    """CTMC 0 -(2.0)-> 1 -(3.0)-> 2, state 2 absorbing (exit rate 0)."""
    ats = umbi.ats.SimpleAts()
    ats.time = umbi.ats.TimeType.STOCHASTIC
    ats.num_players = 0
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


def _as_doubles(ats: umbi.ats.SimpleAts) -> umbi.ats.SimpleAts:
    """The umbi examples use exact rationals and integer rewards; not every tool reads those
    (Prism needs -exact, Storm rejects int rewards), so convert to doubles."""
    probabilities = ats.branch_to_probability
    probabilities[:] = [float(p) for p in probabilities]
    for name in ats.reward_annotation_names:
        annotation = ats.get_reward_annotation(name)
        for attr in ("state_values", "choice_values", "branch_values"):
            try:
                values = getattr(annotation, attr)
            except ValueError:  # this annotation has no values of that kind
                continue
            values[:] = [float(v) for v in values]
    ats.validate()
    return ats


def _generated() -> dict[str, umbi.ats.SimpleAts]:
    return {
        "dtmc_initial_not_zero.umb": _initial_not_zero(),
        "dtmc_two_state.umb": _two_state_dtmc(),
        "ctmc_chain.umb": _three_state_ctmc(),
        "mdp_grid_3x4.umb": _as_doubles(examples.grid(GRID)),
    }


# Tolerated reading failures of the umbi-written files, per tool (see tests/test_regression.py).
KNOWN_ISSUES = {
    "ModestCLI": "umbi 0.2.12 writes format-version 0 / revision 1; Modest requires version 1 / revision 0",
}
# Additional known issues of single models, on top of KNOWN_ISSUES.
MODEL_ISSUES = {
    "dtmc_initial_not_zero.umb": {
        "ModestCLI": "Modest does not support models where state 0 is not the initial state "
        "(besides the umbi format version problem)",
    },
}


def main() -> None:
    MODELS.mkdir(exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"models": {}}
    manifest["models"] = {k: v for k, v in manifest["models"].items() if v.get("source") != "umbi"}
    for name, ats in _generated().items():
        umbi.ats.write(ats, MODELS / name)
        manifest["models"][name] = {
            "source": "umbi",
            "known_issues": {**KNOWN_ISSUES, **MODEL_ISSUES.get(name, {})},
        }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
