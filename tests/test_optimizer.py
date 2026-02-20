import pytest
from logic import (
    find_state_in_fund_name,
    calculate_after_tax_yield,
    calculate_tax_equivalent_yield,
    calculate_Ps,
    calculate_Pm,
    calculate_Pg,
)


def test_find_state_in_fund_name():
    # Mock fund objects
    ny_fund = {"name": "Vanguard New York Municipal Money Market Fund"}
    ca_fund = {"name": "Fidelity California Municipal Money Market Fund"}
    gen_fund = {"name": "Schwab Value Advantage Money Fund"}

    assert find_state_in_fund_name(ny_fund, "NY") is True
    assert find_state_in_fund_name(ca_fund, "CA") is True
    assert find_state_in_fund_name(ny_fund, "CA") is False
    assert find_state_in_fund_name(gen_fund, "GEN") is False
    assert find_state_in_fund_name(gen_fund, "NONE") is False
    assert find_state_in_fund_name(gen_fund, "DC") is True


def test_calculate_after_tax_yield():
    # yield=5.0, fed=0.2, state=0.1, Ps=0, Pm=0, Pg=0, Pt=1.0
    res = calculate_after_tax_yield(5.0, 0.2, 0.1, 0, 0, 0, 1.0)
    assert res == pytest.approx(3.5)

    res = calculate_after_tax_yield(5.0, 0.2, 0.1, 1.0, 0, 0, 0)
    assert res == pytest.approx(5.0)


def test_calculate_tax_equivalent_yield():
    # yield=3.5, fed=0.2, state=0.1, Ps=0, Pm=0, Pg=0, Pt=1.0
    res = calculate_tax_equivalent_yield(3.5, 0.2, 0.1, 0, 0, 0, 1.0)
    assert res == pytest.approx(3.5)

    # Ps = 1.0, yield=3.5
    res = calculate_tax_equivalent_yield(3.5, 0.2, 0.1, 1.0, 0, 0, 0)
    assert res == pytest.approx(5.0)


def test_calculate_Ps():
    fund = {
        "category": "SingleState",
        "name": "Vanguard New York Municipal Money Market Fund",
        "variableRateDemandNote": 0.5,
        "otherMunicipalSecurity": 0.3,
        "tenderOptionBond": 0.1,
        "investmentCompany": 0.05,
        "nonFinancialCompanyCommercialPaper": 0.05,
    }
    assert calculate_Ps(fund, "NY") == pytest.approx(1.0)
    assert calculate_Ps(fund, "CA") == 0


def test_calculate_Pm():
    fund = {
        "category": "OtherTaxExempt",
        "name": "General Muni Fund",
        "variableRateDemandNote": 0.9,
    }
    assert calculate_Pm(fund, "NY") == 0.9


def test_calculate_Pg():
    fund = {"usTreasuryDebt": 0.4, "usGovernmentAgencyDebt": 0.2}
    assert calculate_Pg(fund, "WA") == pytest.approx(0.6)
    assert calculate_Pg(fund, "CA") == pytest.approx(0.6)

    fund_low = {"usTreasuryDebt": 0.3, "usGovernmentAgencyDebt": 0.1}
    assert calculate_Pg(fund_low, "CA") == 0


def test_main_top_5(mocker, capsys):
    # Mock data
    mock_fund_data = [
        {
            "ticker": "HIGH",
            "name": "High Yield Fund",
            "yield": 5.0,
            "minimumInitialInvestment": 1000,
            "category": "OtherTaxExempt",
            "investorType": "Retail",
        }
    ]
    mocker.patch("optimizer.get_fund_data", return_value=mock_fund_data)

    # Mock sys.argv
    import sys

    mocker.patch.object(
        sys,
        "argv",
        [
            "optimizer.py",
            "--federal_tax_rate",
            "20",
            "--state_tax_rate",
            "5",
            "--state",
            "WA",
            "--investment_amount",
            "5000",
        ],
    )

    # Mock Confirmation to avoid interactive input in tests
    from optimizer import Config

    mocker.patch("optimizer.get_tax_info", return_value=(0.20, 0.05, "WA"))
    mocker.patch("optimizer.Config.save", return_value=None)
    mocker.patch("optimizer.Config.load", return_value=Config())
    mocker.patch("optimizer.Prompt.ask", return_value="")

    from optimizer import main

    main()

    captured = capsys.readouterr()
    assert "1" in captured.out
    assert "HIGH" in captured.out
