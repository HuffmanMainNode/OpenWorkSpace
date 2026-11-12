from openworkspace.policy import authorize


def test_policy_defaults_to_deny():
    decisions = authorize(["filesystem.read", "network.connect"], set())
    assert [decision.allowed for decision in decisions] == [False, False]


def test_only_exact_explicit_grant_is_allowed():
    decisions = authorize(["filesystem.read", "filesystem.write"], {"filesystem.read"})
    assert [decision.allowed for decision in decisions] == [True, False]
