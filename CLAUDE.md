# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Norwegian pension planning simulation tool built as a proof-of-concept. It allows users to model different pension scenarios based on salary (measured in G-units), retirement age, and personal savings to plan for early retirement (FIRE scenarios) or international retirement.

## Common Commands

```bash
# Run the Streamlit application
streamlit run app.py

# Install dependencies
pip install -r requirements.txt

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

**Note**: There are no formal test, lint, or build commands configured. This is a POC project.

## Tech Stack

- **Python 3.11**
- **Streamlit**: Interactive web application framework
- **Pandas**: Data manipulation and tabular display

## Architecture

The application is organized into three modules following clean separation of concerns:

### 1. Data Model Layer (`models.py`)

- `PensionInputs` dataclass: Defines all input parameters for the simulation

### 2. Business Logic Layer (`pension_calculator.py`)

- `DELINGSFAKTOR_1963`: Division factor table for NAV life expectancy adjustment
- `get_delingsfaktor_nav()`: Calculates NAV-style division factors for pension age
- `simulate_until_pension_age()`: Core simulation engine that calculates annual pension accumulation
- `annual_pension_from_balance()`: Converts accumulated balances to annual pension amounts

### 3. User Interface Layer (`app.py`)

Streamlit-based interactive UI with:
- **Sidebar**: Input controls (sliders for G-units, ages, percentages)
- **Main content**: Results display with pension calculations
- Multiple pension ages comparison (user can select 55, 62, 65, 67, 70)

## Norwegian Pension Model

The simulation models three pension components:

1. **Folketrygd (NAV - State Pension)**
   - Based on capped salary (7.1G limit where G = grunnbeløp/base amount)
   - 18% accrual rate
   - Managed by Norwegian Labor and Welfare Administration (NAV)

2. **OTP (Occupational Pension)**
   - Two-tier system:
     - 7% on salary below 7.1G
     - 18% on salary above 7.1G (up to 12G cap)
   - Employer-provided pension scheme

3. **Personal Savings**
   - User's own investment portfolio
   - Configurable growth rates

**Annual Accumulation Logic**:
- Each working year accumulates new pension credits (if still working)
- Applies annual growth/return rates to all existing balances
- All thresholds based on G-beløp (Norwegian pension base amount)

## Component Flow

```
app.py (UI Layer)
    User Input (Sidebar)
        ↓

models.py (Data Layer)
    PensionInputs dataclass
        ↓

pension_calculator.py (Business Logic)
    simulate_until_pension_age()
        ↓
    Pension balances (NAV, OTP, savings)
        ↓
    annual_pension_from_balance()
        ↓

app.py (UI Layer)
    Pandas DataFrames
        ↓
    Streamlit display (st.dataframe)
```

## Domain Context

**G-units (Grunnbeløp)**: Norwegian pension base amount, updated annually. All salary and pension thresholds are expressed as multiples of G (e.g., 7.1G, 12G).

**Target Users**: Norwegian workers planning:
- Early retirement (FIRE - Financial Independence, Retire Early)
- International retirement (Thailand, Sweden scenarios mentioned in docs)
- Salary optimization (comparing 6G vs 7.1G vs 8G salary levels)

**Key Terminology**:
- **Folketrygd**: Norwegian state pension system
- **OTP**: Occupational pension (employer-provided)
- **Pensjonsalder**: Retirement age

## Important Notes

1. **Simplified Model**: This simulation is NOT NAV-accurate. It's designed to show "how different choices affect pension" rather than precise calculations.

2. **Purpose**: Comparative analysis tool for understanding trade-offs between salary levels, retirement ages, and savings strategies.

3. **Documentation**: See `/docs/experts.md` for domain expertise context on Norwegian pension rules, tax implications, and retirement planning scenarios.

## Code Quality Standards

### Key Constants (pension_calculator.py)
- `SALARY_CAP_IN_G = 7.1`: Folketrygd salary cap in G-units
- `MIN_NAV_PENSION_AGE = 62`: Minimum age for NAV pension
- `STANDARD_PENSION_AGE = 67`: Standard retirement age
- `MAX_NAV_PENSION_AGE = 75`: Maximum age for NAV pension calculation
- `ANNUAL_DIVISOR_REDUCTION = 0.9`: Yearly reduction in divisor after age 67

### Input Validation
- All monetary inputs have min_value constraints in the UI
- `PensionInputs` dataclass validates all parameters in `__post_init__`
- `simulate_until_pension_age()` validates that pension_age > current_age and pension_age <= life_expectancy
- Empty pension_ages selection is validated with a warning message

### Error Handling
- Try/except blocks wrap PensionInputs creation and calculation loops
- User-friendly error messages are displayed via Streamlit
- Calculation errors for individual pension ages don't crash the entire app

### Type Hints
- All functions have complete type hints for parameters and return values
- Constants are type-annotated
- Uses `typing.Dict` and `typing.Tuple` for complex types

## Testing Recommendations

While no formal tests exist (POC project), future test coverage should include:

### Unit Tests Needed
1. **models.py**
   - Test `PensionInputs` validation in `__post_init__`
   - Test boundary conditions (negative values, zero values, age > life_expectancy)
   - Test age/birth_year consistency

2. **pension_calculator.py**
   - Test `get_delingsfaktor_nav()` for all age ranges (55-75)
   - Test edge cases: pension_age = current_age + 1, pension_age = life_expectancy
   - Test `simulate_until_pension_age()` with various scenarios
   - Test zero balances, zero growth rates
   - Test `annual_pension_from_balance()` with use_nav_style True/False

3. **app.py**
   - Integration tests using Streamlit testing framework
   - Test calculation flow end-to-end
   - Test invalid input handling

### Test Coverage Goals
- Aim for 80%+ coverage on business logic (`pension_calculator.py`)
- Focus on edge cases and boundary conditions
- Test all validation logic

## Development Guidelines

1. **Dependencies**: Version constraints are specified in `requirements.txt` (`>=1.28.0,<2.0.0` format)
2. **Documentation**: All classes and functions have comprehensive docstrings
3. **Constants**: Extract magic numbers into named constants at module level
4. **Validation**: Validate inputs as early as possible (UI → dataclass → functions)
5. **Error Messages**: Provide clear, user-friendly error messages in Norwegian (UI language)

