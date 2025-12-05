from typing import Dict, Tuple

from models import PensionInputs


# Constants for Norwegian pension system
SALARY_CAP_IN_G: float = 7.1  # Folketrygd salary cap in G-units
MIN_NAV_PENSION_AGE: int = 62  # Minimum age for NAV pension
STANDARD_PENSION_AGE: int = 67  # Standard retirement age
MAX_NAV_PENSION_AGE: int = 75  # Maximum age for NAV pension calculation
ANNUAL_DIVISOR_REDUCTION: float = 0.9  # Yearly reduction in divisor after age 67

# Delingstall-tabell (eksempel) for 1963-kullet, 62–67 år.
# Brukes som NAV-lignende levealdersjustering for yngre kull også.
# Kilde: typiske delingstall-eksempler for 1963-kullet i folketrygd/offentlig ordning.
DELINGSFAKTOR_1963: Dict[int, float] = {
    62: 20.06,
    63: 19.25,
    64: 18.44,
    65: 17.63,
    66: 16.83,
    67: 16.02,
}


def get_delingsfaktor_nav(pension_age: int, birth_year: int, life_expectancy: int) -> float:
    """
    Forenklet NAV-lignende delingsfaktor:
    - For 62–67 år bruker vi tabellverdier fra 1963-kullet (som representativt nivå).
    - For 68–75 år antar vi at delingstallet synker omtrent 0.9 per år etter 67.
    - For andre aldre faller vi tilbake til en enkel (life_expectancy - age)-modell.

    Merk:
    - For ditt kull (1989) vil faktiske delingstall trolig være litt høyere (lavere årlig pensjon),
      så denne modellen er litt optimistisk for folketrygden – men god til å sammenligne scenarier.
    """

    # NAV: alderspensjon fra 62–75 år
    if MIN_NAV_PENSION_AGE <= pension_age <= STANDARD_PENSION_AGE:
        base = DELINGSFAKTOR_1963.get(pension_age)
        if base is not None:
            return base

    if STANDARD_PENSION_AGE + 1 <= pension_age <= MAX_NAV_PENSION_AGE:
        # Grovt anslag: ta utgangspunkt i 67-års delingsfaktor og reduser med ca. 0.9 per år.
        base67 = DELINGSFAKTOR_1963[STANDARD_PENSION_AGE]
        adjustment = ANNUAL_DIVISOR_REDUCTION * (pension_age - STANDARD_PENSION_AGE)
        approx = max(1.0, base67 - adjustment)
        return approx

    # For alle andre aldre (f.eks. 55 i din app): bruk enkel lineær modell
    years = max(1, life_expectancy - pension_age)
    return float(years)


def simulate_until_pension_age(
    inputs: PensionInputs,
    work_until_age: int,
    pension_age: int,
) -> Tuple[float, float, float]:
    """
    Simulerer:
    - årlig opptjening i folketrygd og OTP frem til pensjonsalder
    - årlig sparing
    - årlig avkastning/regulering på alle tre beholdninger

    Returnerer beholdning ved pensjonsalder:
        (folketrygd, otp, savings)

    Raises:
        ValueError: If pension_age is not greater than current_age
    """

    # Validate inputs
    if pension_age <= inputs.current_age:
        raise ValueError(
            f"pension_age ({pension_age}) must be greater than current_age ({inputs.current_age})"
        )
    if pension_age > inputs.life_expectancy:
        raise ValueError(
            f"pension_age ({pension_age}) cannot exceed life_expectancy ({inputs.life_expectancy})"
        )

    folketrygd = float(inputs.current_folketrygd_balance)
    otp = float(inputs.current_otp_balance)
    savings = float(inputs.current_savings)

    for age in range(inputs.current_age, pension_age):
        salary = inputs.g_amount * inputs.salary_in_g
        is_working = age < work_until_age

        if is_working:
            # Folketrygd-opptjening (ny modell: 18,1 % av pensjonsgivende inntekt opp til 7,1 G – her forenklet til state_accrual_rate)
            cap_salary = min(salary, inputs.g_amount * SALARY_CAP_IN_G)
            folketrygd += cap_salary * inputs.state_accrual_rate

            # OTP-opptjening (typisk 7 % opp til 7,1 G, opptil 18 % over)
            below_cap = cap_salary
            above_cap = max(0.0, salary - cap_salary)
            otp += below_cap * inputs.otp_below_rate + above_cap * inputs.otp_above_rate

            # Egen sparing (inkl. leieinntekter som pløyes rett inn)
            savings += inputs.annual_savings + inputs.annual_rental_savings

        # Årlig regulering/avkastning
        folketrygd *= (1 + inputs.folketrygd_growth)
        otp *= (1 + inputs.otp_growth)
        savings *= (1 + inputs.savings_growth)

    return folketrygd, otp, savings


def annual_pension_from_balance(
    balance: float,
    pension_age: int,
    birth_year: int,
    life_expectancy: int,
    use_nav_style: bool = True,
) -> float:
    """
    Konverterer en pensjonsbeholdning til årlig pensjon.

    Hvis use_nav_style:
        - Bruker NAV-lignende delingsfaktor (levealdersjustering)
    Ellers:
        - Bruker enkel (life_expectancy - pension_age)-modell
    """

    if balance <= 0:
        return 0.0

    if use_nav_style and pension_age >= MIN_NAV_PENSION_AGE:
        divisor = get_delingsfaktor_nav(pension_age, birth_year, life_expectancy)
    else:
        years = max(1, life_expectancy - pension_age)
        divisor = float(years)

    return balance / divisor
