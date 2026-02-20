# MMF Optimizer

A high-performance terminal utility to calculate and compare the top 5 Money Market Funds (MMFs) based on your specific **after-tax yield** and **tax-equivalent yield**. It automatically accounts for **2026** federal and state tax brackets based on your income and residency.

## Features

- **Income-Based Tax Lookup:** Automatically estimates your marginal federal and state tax rates based on your taxable income and filing status for all 50 states + DC (using 2026 inflation-adjusted brackets).
- **State-Specific Tax Rules:** Includes specific logic for complex state rules, such as New Jersey's 80% municipal rule and the 50% US Government threshold for CA, NY, and CT.
- **Modern TUI:** A clean, color-coded terminal interface using the `Rich` library.
- **Persistence:** Saves your tax configuration (rates and state) for 30 days so you don't have to re-enter them every time.
- **Bank Comparison:** Compare found funds against your current high-yield savings account (HYSA) APY.
- **Functional & Modular:** Rewritten in a clean, functional style with separated business logic and data layers.

## Installation

### Prerequisites
- **Python 3.14+** (Recommended)
- `pip` or your preferred package manager

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mmf_optimizer.git
   cd mmf_optimizer
   ```

2. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```

## Usage

You can run the optimizer in two ways: **Interactive Mode** (recommended) or **CLI Mode**.

### 1. Interactive Mode
Simply run the script without arguments. It will clear the terminal and guide you through the setup:
```bash
python3 optimizer.py
```
It will prompt you for:
- State Abbreviation (e.g., NY, CA, WA)
- Annual Taxable Income (to estimate tax rates)
- Investment Amount
- Bank APY (optional comparison)
- Issuer Filter (optional, e.g., "Vanguard")

### 2. CLI Mode (Manual Override)
Provide arguments directly to skip prompts or automate execution:
```bash
python3 optimizer.py --federal_tax_rate 24 --state_tax_rate 5 --state NY --investment_amount 10000
```

**Full Argument List:**
- `--federal_tax_rate`: Marginal federal rate (e.g., 22)
- `--state_tax_rate`: Marginal state rate (e.g., 6.5)
- `--state`: Two-letter state code (e.g., WA)
- `--investment_amount`: Total dollars to invest
- `--bank_apy`: Current bank yield to compare (optional)
- `--issuer`: Filter for a specific fund provider (optional)

## Project Structure

- `optimizer.py`: The entry point. Handles the TUI, user input, and orchestration.
- `logic.py`: Core business logic, yield formulas, and fund processing.
- `tax_data.py`: 2025/2026 Federal and 50-state marginal tax brackets.
- `tests/`: A comprehensive test suite verifying calculation accuracy and edge cases.

## Testing

Run the suite using `pytest`:
```bash
python3 -m pytest tests/test_optimizer.py
```

## Disclaimer
*This tool provides estimates based on 2025 tax law data. It is not financial or tax advice. Always consult with a certified tax professional regarding your specific tax situation.*
