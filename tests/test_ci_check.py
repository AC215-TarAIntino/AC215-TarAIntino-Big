"""
Temporary test to verify CI fails when tests fail.
TODO: Remove this file after CI verification.
"""


def test_ci_verification_failure():
    """
    This test is intentionally failing to verify that the CI pipeline
    correctly fails when tests fail (after removing || true).

    Once CI has been verified to fail, this test file should be removed.
    """
    # assert False # "CI CHECK: This test should cause the CI to fail. Uncomment line below and comment this one instead to fix."
    assert True
