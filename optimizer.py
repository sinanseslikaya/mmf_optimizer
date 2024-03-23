import argparse
import requests
import us

fifty_percent_states = ["CA", "NY", "CT"]


def get_fund_data():
    """
    Retrieves fund data from a specified URL.

    Returns:
        dict: A dictionary containing the fund data in JSON format.
            Returns None if the data retrieval fails.
    """
    url = "https://moneymarket.fun/data/fundYields.json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to retrieve data from the server.")
        return None


def find_state_in_fund_name(fund, state):
    """
    Checks if a given state is present in the name of a fund.

    Args:
        fund (dict): A dictionary representing a fund.
        state (str): The state to search for in the fund name.

    Returns:
        bool: True if the state is found in the fund name, False otherwise.
    """
    if state in ["GEN", "NONE"]:
        return False

    if state == "DC":
        return True

    state_full_name = us.states.lookup(state).name
    return state_full_name.lower() in fund["name"].lower()


def calculate_after_tax_yield(
    fund_yield, federal_tax_rate, state_tax_rate, Ps, Pm, Pg, Pt
):
    """
    Calculate the after-tax yield of a fund.

    Args:
        fund_yield (float): The yield of the fund before taxes.
        federal_tax_rate (float): The federal tax rate as a decimal.
        state_tax_rate (float): The state tax rate as a decimal.
        Ps (float): The proportion of the yield subject to state tax.
        Pm (float): The proportion of the yield subject to municipal tax.
        Pg (float): The proportion of the yield subject to federal tax.
        Pt (float): The proportion of the yield subject to both federal and state tax.

    Returns:
        float: The after-tax yield of the fund.

    """
    after_tax_yield = (
        fund_yield * Ps
        + fund_yield * Pm * (1 - state_tax_rate)
        + fund_yield * Pg * (1 - federal_tax_rate)
        + fund_yield * Pt * (1 - federal_tax_rate - state_tax_rate)
    )
    return after_tax_yield


def calculate_tax_equivalent_yield(
    fund_yield, federal_tax_rate, state_tax_rate, Ps, Pm, Pg, Pt
):
    """
    Calculates the tax equivalent yield based on the given parameters.

    Args:
        fund_yield (float): The yield of the fund.
        federal_tax_rate (float): The federal tax rate.
        state_tax_rate (float): The state tax rate.
        Ps (float): The proportion of the yield subject to state tax.
        Pm (float): The proportion of the yield subject to municipal tax.
        Pg (float): The proportion of the yield subject to federal tax.
        Pt (float): The proportion of the yield subject to other taxes.

    Returns:
        float: The tax equivalent yield.

    """
    tax_equivalent_yield = (
        fund_yield * Ps / (1 - federal_tax_rate - state_tax_rate)
        + fund_yield
        * Pm
        * (1 - state_tax_rate)
        / (1 - federal_tax_rate - state_tax_rate)
        + fund_yield
        * Pg
        * (1 - federal_tax_rate)
        / (1 - federal_tax_rate - state_tax_rate)
        + fund_yield * Pt
    )
    return tax_equivalent_yield


def calculate_Ps(fund, state):
    """
    Calculate the value of Ps based on the given fund and state.

    Args:
        fund (dict): A dictionary representing the fund.
        state (str): The state for which Ps needs to be calculated.

    Returns:
        float: The calculated value of Ps.

    """
    Ps = 0
    in_state_muni = find_state_in_fund_name(fund, state)

    muni_percent = 0

    if fund["category"] in ["OtherTaxExempt", "SingleState"]:
        muni_percent = sum(
            value
            for value in [
                fund.get("variableRateDemandNote", 0),
                fund.get("otherMunicipalSecurity", 0),
                fund.get("tenderOptionBond", 0),
                fund.get("investmentCompany", 0),
                fund.get("nonFinancialCompanyCommercialPaper", 0),
            ]
            if value is not None
        )

    # all states besides NJ
    if in_state_muni and state.lower() != "nj":
        Ps = muni_percent
    # NJ has a 80% rule for muni
    elif in_state_muni and muni_percent >= 0.8:
        Ps = muni_percent

    return Ps


def calculate_Pm(fund, state):
    """
    Calculate the value of Pm based on the given fund and state.

    Parameters:
    - fund (dict): A dictionary representing the fund.
    - state (str): The state for which Pm needs to be calculated.

    Returns:
    - Pm (float): The calculated value of Pm.

    """
    Pm = 0
    in_state_muni = find_state_in_fund_name(fund, state)

    muni_percent = 0

    if fund["category"] in ["OtherTaxExempt", "SingleState"]:
        muni_percent = sum(
            value
            for value in [
                fund.get("variableRateDemandNote", 0),
                fund.get("otherMunicipalSecurity", 0),
                fund.get("tenderOptionBond", 0),
                fund.get("investmentCompany", 0),
                fund.get("nonFinancialCompanyCommercialPaper", 0),
            ]
            if value is not None
        )

    if not in_state_muni:
        Pm = muni_percent

    return Pm


def calculate_Pg(fund, state):
    """
    Calculate the value of Pg (Percent of US Government) based on the given fund and state.

    Parameters:
    - fund (dict): A dictionary representing the fund, containing information about different debt sources.
    - state (str): The state for which the Pg value is being calculated.

    Returns:
    - Pg (float): The calculated value of Pg.

    """
    Pg = 0
    # Summarize All sources of USGO into one value for tax calculations.
    usgo_percent = sum(
        value
        for value in [
            fund.get("usTreasuryDebt", 0),
            fund.get("usGovernmentAgencyDebt", 0),
        ]
        if value is not None
    )
    # If this is a state with a 50% threshold, then only put the value in if the USGO is greater than .5

    if state in fifty_percent_states and usgo_percent >= 0.5:
        Pg = usgo_percent
    elif state not in fifty_percent_states:
        Pg = usgo_percent

    return Pg


def main():
    parser = argparse.ArgumentParser(
        description="Calculate top 5 money market funds based on after-tax yield"
    )
    parser.add_argument(
        "--federal_tax_rate",
        type=float,
        help="Marginal federal tax rate",
        required=True,
    )
    parser.add_argument(
        "--state_tax_rate", type=float, help="Marginal state tax rate", required=True
    )
    parser.add_argument("--state", type=str, help="State name")
    parser.add_argument("--investment_amount", type=float, help="Investment amount")
    parser.add_argument("--bank_apy", type=float, help="Current bank APY")
    parser.add_argument("--issuer", type=str, help="Issuer name", required=False)
    parser.add_argument(
        "--institutional", type=bool, help="include institutional funds", required=False
    )
    args = parser.parse_args()

    # if not all(vars(args).values()):
    #     parser.error("All arguments are required.")

    fund_data = get_fund_data()
    if fund_data:
        top_funds = []
        for fund in fund_data:

            # these should all be skip conditions
            if fund["minimumInitialInvestment"] > args.investment_amount:
                continue

            if args.issuer and args.issuer.lower() not in fund["name"].lower():
                continue

            # if not args.institutional and fund["investorType"] == "Institutional":
            #     continue  
            # not including this currently 

            # end of skip conditions

            # calculate the proportion of the yield subject to each tax
            Ps = calculate_Ps(fund, args.state)
            Pm = calculate_Pm(fund, args.state)
            Pg = calculate_Pg(fund, args.state)
            Pt = 1 - (Ps + Pm + Pg)

            # if fund["ticker"] in ["SWPXX", "SNSXX", "SNOXX", "SNVXX", "SWVXX"]:
            #     print(fund["ticker"])
            #     print(f"Ps: {Ps}")
            #     print(f"Pm: {Pm}")
            #     print(f"Pg: {Pg}")
            #     print(f"Pt: {Pt}")

            after_tax_yield = calculate_after_tax_yield(
                fund["yield"],
                args.federal_tax_rate / 100,
                args.state_tax_rate / 100,
                Ps,
                Pm,
                Pg,
                Pt,
            )

            tax_equivalent_yield = calculate_tax_equivalent_yield(
                fund["yield"],
                args.federal_tax_rate / 100,
                args.state_tax_rate / 100,
                Ps,
                Pm,
                Pg,
                Pt,
            )

            fund["after_tax_yield"] = after_tax_yield
            fund["tax_equivalent_yield"] = tax_equivalent_yield
            top_funds.append(fund)

        top_funds.sort(key=lambda x: x["tax_equivalent_yield"], reverse=True)
        print("Top 5 Money Market Funds based on tax_equivalent_yield:")
        for i, fund in enumerate(top_funds[:5], start=1):
            print(f"Rank: {i}")
            print(f"Ticker: {fund['ticker']}")
            print(f"Name: {fund['name']}")
            print(f"After-tax Yield: {fund['after_tax_yield']:.2f}%")
            print(f"Tax Equivalent Yield: {fund['tax_equivalent_yield']:.2f}%")
            print(
                f"After Tax Distributions on ${args.investment_amount:,.2f} over 12 months: ${args.investment_amount * fund['after_tax_yield'] / 100:,.2f}"
            )
            print("--------------")

        # make same calculations on user bank apy if it was provided
        if args.bank_apy:
            bank_after_tax_yield = args.bank_apy * (1 - args.federal_tax_rate / 100)
            bank_after_tax_distributions = (
                args.investment_amount * bank_after_tax_yield / 100
            )
            print(f"Bank After-tax Yield: {bank_after_tax_yield:.2f}%")
            print(
                f"Bank After Tax Distributions on ${args.investment_amount:,.2f} over 12 months: ${bank_after_tax_distributions:,.2f}"
            )
            print("--------------")


if __name__ == "__main__":
    main()
