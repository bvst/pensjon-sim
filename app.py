import math
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import streamlit as st


# ==========================
#     MODELLDATA
# ==========================

@dataclass
class PensionInputs:
    current_age: int
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
    life_expectancy: int = 90


def simulate_until_pension_age(inputs: PensionInputs, work_until_age: int, pension_age: int) -> Dict[str, float]:

    folketrygd = inputs.current_folketrygd_balance
    otp = inputs.current_otp_balance
    savings = inputs.current_savings

    for age in range(inputs.current_age, pension_age):

        salary = inputs.g_amount * inputs.salary_in_g
        is_working = age < work_until_age

        if is_working:
            # Folketrygd-opptjening
            cap_salary = min(salary, inputs.g_amount * 7.1)
            folketrygd += cap_salary * inputs.state_accrual_rate

            # OTP-opptjening
            below_cap = cap_salary
            above_cap = max(0, salary - below_cap)
            otp += below_cap * inputs.otp_below_rate + above_cap * inputs.otp_above_rate

            # Egen sparing
            savings += inputs.annual_savings + inputs.annual_rental_savings

        # Årlig avkastning / regulering
        folketrygd *= (1 + inputs.folketrygd_growth)
        otp *= (1 + inputs.otp_growth)
        savings *= (1 + inputs.savings_growth)

    return {
        "folketrygd": folketrygd,
        "otp": otp,
        "savings": savings,
    }


def annual_pension_from_balance(balance: float, pension_age: int, life_expectancy: int):
    years = max(1, life_expectancy - pension_age)
    return balance / years



# ==========================
#     STREAMLIT UI
# ==========================

st.set_page_config(page_title="Pensjonssimulator – POC", layout="wide")
st.title("🧮 Pensjonssimulator – POC")

st.markdown("""
En enkel simulator for å teste:
- Lønn i G (6G → 7.1G → 8G osv)
- Når du slutter å jobbe
- Sparing og avkastning
- Effekt på pensjonen ved 55 / 62 / 65 / 67 / 70

Modellen er forenklet (ikke NAV-nøyaktig),  
men *svært nyttig* for å se **hvordan ulike valg påvirker pensjonen**.
""")


# ==========================
#     INPUT-FELT (Sidebar)
# ==========================

with st.sidebar:
    st.header("📥 Input")

    current_age = st.number_input("Alder i dag", value=36)

    current_folketrygd_balance = st.number_input(
        "Folketrygd-beholdning (NAV)", value=1_697_820
    )

    current_otp_balance = st.number_input(
        "OTP-beholdning (valgfritt)", value=0
    )

    current_savings = st.number_input(
        "Dagens sparing (fond + bank)", value=660_000
    )

    annual_savings = st.number_input("Årlig sparing", value=120_000, step=10_000)

    annual_rental_savings = st.number_input("Leieinntekt som spares", value=0)

    g_amount = st.number_input("G-beløp", value=124_028)

    salary_in_g = st.slider("Lønn i G", 3.0, 12.0, 7.1, 0.1)

    work_until_age = st.slider("Jobber til alder", current_age, 70, 55)

    life_expectancy = st.slider("Forventet levealder", 80, 100, 90)

    st.subheader("Avanserte satser (kan stå urørt)")
    state_accrual_rate = st.number_input("Folketrygd-opptjening", value=0.18)
    otp_below_rate = st.number_input("OTP 0–7.1G", value=0.07)
    otp_above_rate = st.number_input("OTP over 7.1G", value=0.18)
    folketrygd_growth = st.number_input("Regulering folketrygd", value=0.02)
    otp_growth = st.number_input("OTP avkastning", value=0.04)
    savings_growth = st.number_input("Avkastning egen sparing", value=0.05)

    pension_ages = st.multiselect(
        "Vis pensjon for følgende aldre",
        options=[55, 62, 65, 67, 70],
        default=[55, 62, 67, 70],
    )


inputs = PensionInputs(
    current_age=current_age,
    current_folketrygd_balance=current_folketrygd_balance,
    current_otp_balance=current_otp_balance,
    current_savings=current_savings,
    annual_savings=annual_savings,
    annual_rental_savings=annual_rental_savings,
    g_amount=g_amount,
    salary_in_g=salary_in_g,
    state_accrual_rate=state_accrual_rate,
    otp_below_rate=otp_below_rate,
    otp_above_rate=otp_above_rate,
    folketrygd_growth=folketrygd_growth,
    otp_growth=otp_growth,
    savings_growth=savings_growth,
    life_expectancy=life_expectancy,
)


# ==========================
#     BEREGN RESULTATER
# ==========================

rows = []
for pa in pension_ages:
    result = simulate_until_pension_age(inputs, work_until_age, pa)
    annual_nav = annual_pension_from_balance(result["folketrygd"], pa, life_expectancy)
    annual_otp = annual_pension_from_balance(result["otp"], pa, life_expectancy)
    annual_sav = annual_pension_from_balance(result["savings"], pa, life_expectancy)

    rows.append({
        "Pensjonsalder": pa,
        "Jobber til": work_until_age,
        "Årlig NAV": round(annual_nav),
        "Årlig OTP": round(annual_otp),
        "Årlig sparing": round(annual_sav),
        "SUM årlig": round(annual_nav + annual_otp + annual_sav),
    })

main_df = pd.DataFrame(rows)


# ==========================
#     VIS RESULTATET
# ==========================

st.subheader("📈 Resultater – grunnscenario")
st.dataframe(main_df, use_container_width=True)



# ==========================
#     SAMMENLIGN 6G / 7.1G / 8G
# ==========================

st.subheader("🔍 Sammenligning: 6G vs 7.1G vs 8G – pensjon ved 67")

compare_rows = []
for g in [6.0, 7.1, 8.0]:

    temp_inputs = inputs
    temp_inputs.salary_in_g = g

    pa = 67
    result = simulate_until_pension_age(temp_inputs, work_until_age, pa)
    annual_nav = annual_pension_from_balance(result["folketrygd"], pa, life_expectancy)
    annual_otp = annual_pension_from_balance(result["otp"], pa, life_expectancy)
    annual_sav = annual_pension_from_balance(result["savings"], pa, life_expectancy)

    compare_rows.append({
        "Lønn i G": g,
        "Årlig NAV": round(annual_nav),
        "Årlig OTP": round(annual_otp),
        "Årlig sparing": round(annual_sav),
        "SUM årlig": round(annual_nav + annual_otp + annual_sav),
    })

compare_df = pd.DataFrame(compare_rows)
st.dataframe(compare_df, use_container_width=True)
