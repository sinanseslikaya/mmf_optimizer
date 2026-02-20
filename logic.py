import us
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional

FIFTY_PERCENT_STATES = ["CA", "NY", "CT"]


@dataclass(frozen=True)
class TaxProportions:
    ps: float
    pm: float
    pg: float
    pt: float


@dataclass(frozen=True)
class YieldResults:
    after_tax_yield: float
    tax_equivalent_yield: float


def get_marginal_rate(income: float, brackets: List[Tuple[float, float]]) -> float:
    """Finds the marginal rate (the rate for the last dollar earned)."""
    current_rate = brackets[0][1]
    for threshold, rate in brackets:
        if income >= threshold:
            current_rate = rate
        else:
            break
    return current_rate


def find_state_in_fund_name(fund: Dict[str, Any], state: str) -> bool:
    if state in ["GEN", "NONE"]:
        return False
    if state == "DC":
        return True
    state_lookup = us.states.lookup(state)
    if not state_lookup:
        return False
    return state_lookup.name.lower() in fund["name"].lower()


def calculate_muni_percent(fund: Dict[str, Any]) -> float:
    if fund.get("category") not in ["OtherTaxExempt", "SingleState"]:
        return 0.0
    keys = [
        "variableRateDemandNote",
        "otherMunicipalSecurity",
        "tenderOptionBond",
        "investmentCompany",
        "nonFinancialCompanyCommercialPaper",
    ]
    return sum(fund.get(key, 0) or 0 for key in keys)


def calculate_ps(fund: Dict[str, Any], state: str) -> float:
    in_state_muni = find_state_in_fund_name(fund, state)
    muni_percent = calculate_muni_percent(fund)
    if in_state_muni and (state.lower() != "nj" or muni_percent >= 0.8):
        return muni_percent
    return 0.0


def calculate_pm(fund: Dict[str, Any], state: str) -> float:
    in_state_muni = find_state_in_fund_name(fund, state)
    return calculate_muni_percent(fund) if not in_state_muni else 0.0


def calculate_pg(fund: Dict[str, Any], state: str) -> float:
    usgo_percent = (fund.get("usTreasuryDebt", 0) or 0) + (
        fund.get("usGovernmentAgencyDebt", 0) or 0
    )
    if state in FIFTY_PERCENT_STATES and usgo_percent < 0.5:
        return 0.0
    return usgo_percent


def calculate_tax_proportions(fund: Dict[str, Any], state: str) -> TaxProportions:
    ps, pm, pg = (
        calculate_ps(fund, state),
        calculate_pm(fund, state),
        calculate_pg(fund, state),
    )
    return TaxProportions(ps, pm, pg, 1.0 - (ps + pm + pg))


def calculate_after_tax_yield(
    fund_yield: float,
    fed_rate: float,
    state_rate: float,
    ps: float,
    pm: float,
    pg: float,
    pt: float,
) -> float:
    return fund_yield * (
        ps
        + pm * (1 - state_rate)
        + pg * (1 - fed_rate)
        + pt * (1 - fed_rate - state_rate)
    )


def calculate_tax_equivalent_yield(
    fund_yield: float,
    fed_rate: float,
    state_rate: float,
    ps: float,
    pm: float,
    pg: float,
    pt: float,
) -> float:
    denom = 1 - fed_rate - state_rate
    if denom <= 0:
        return fund_yield
    return fund_yield * (
        ps / denom + pm * (1 - state_rate) / denom + pg * (1 - fed_rate) / denom + pt
    )


def process_fund(
    fund: Dict[str, Any], state: str, fed_rate: float, state_rate: float
) -> Dict[str, Any]:
    props = calculate_tax_proportions(fund, state)
    yields = YieldResults(
        after_tax_yield=calculate_after_tax_yield(
            fund["yield"], fed_rate, state_rate, props.ps, props.pm, props.pg, props.pt
        ),
        tax_equivalent_yield=calculate_tax_equivalent_yield(
            fund["yield"], fed_rate, state_rate, props.ps, props.pm, props.pg, props.pt
        ),
    )
    return {**fund, **yields.__dict__}


def filter_funds(
    fund: Dict[str, Any], investment_amount: float, issuer: Optional[str]
) -> bool:
    if fund["minimumInitialInvestment"] > investment_amount:
        return False
    if issuer and issuer.lower() not in fund["name"].lower():
        return False
    return True
