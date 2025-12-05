import datetime
from dataclasses import dataclass


@dataclass
class PensionInputs:
    """
    Input parameters for Norwegian pension calculations.

    This dataclass contains all necessary parameters to simulate pension
    accumulation across three components: Folketrygd (state pension),
    OTP (occupational pension), and personal savings.

    Attributes:
        current_age: Current age of the person (years)
        birth_year: Year of birth
        current_folketrygd_balance: Current balance in state pension account (NOK)
        current_otp_balance: Current balance in occupational pension account (NOK)
        current_savings: Current private savings balance (NOK)
        annual_savings: Annual contribution to private savings (NOK/year)
        annual_rental_savings: Annual rental income saved (NOK/year)
        g_amount: Base amount 'G' (grunnbeløp) for pension calculations (NOK)
        salary_in_g: Annual salary expressed as multiples of G
        state_accrual_rate: Accrual rate for state pension (typically 0.18 = 18%)
        otp_below_rate: OTP rate for salary below 7.1G (typically 0.07 = 7%)
        otp_above_rate: OTP rate for salary above 7.1G (typically 0.18 = 18%)
        folketrygd_growth: Annual growth/regulation rate for state pension
        otp_growth: Annual growth rate for occupational pension
        savings_growth: Annual return rate for private savings
        life_expectancy: Expected age at death (years)
    """
    current_age: int
    birth_year: int
    current_folketrygd_balance: float
    current_otp_balance: float
    current_savings: float
    annual_savings: float
    annual_rental_savings: float
    g_amount: float
    salary_in_g: float
    state_accrual_rate: float
    otp_below_rate: float
    otp_above_rate: float
    folketrygd_growth: float
    otp_growth: float
    savings_growth: float
    life_expectancy: int

    def __post_init__(self):
        """Validate input parameters after initialization."""
        # Validate age ranges
        if not 0 <= self.current_age <= 120:
            raise ValueError(f"current_age must be between 0 and 120, got {self.current_age}")

        if self.life_expectancy <= self.current_age:
            raise ValueError(
                f"life_expectancy ({self.life_expectancy}) must be greater than "
                f"current_age ({self.current_age})"
            )

        # Validate birth year
        current_year = datetime.date.today().year
        if not 1900 <= self.birth_year <= current_year:
            raise ValueError(
                f"birth_year must be between 1900 and {current_year}, got {self.birth_year}"
            )

        # Validate monetary amounts are non-negative
        if self.current_folketrygd_balance < 0:
            raise ValueError("current_folketrygd_balance cannot be negative")
        if self.current_otp_balance < 0:
            raise ValueError("current_otp_balance cannot be negative")
        if self.current_savings < 0:
            raise ValueError("current_savings cannot be negative")
        if self.annual_savings < 0:
            raise ValueError("annual_savings cannot be negative")
        if self.annual_rental_savings < 0:
            raise ValueError("annual_rental_savings cannot be negative")

        # Validate G amount
        if self.g_amount <= 0:
            raise ValueError(f"g_amount must be positive, got {self.g_amount}")

        if self.salary_in_g < 0:
            raise ValueError(f"salary_in_g cannot be negative, got {self.salary_in_g}")
