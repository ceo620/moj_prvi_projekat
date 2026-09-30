from src.calculations.debt import annuity_payment


def test_annuity_payment_positive():
    assert annuity_payment(1_000_000, 0.06, 5) > 0
