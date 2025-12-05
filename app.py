"""
Pension Simulator - Streamlit Application

A proof-of-concept pension calculator for Norwegian pensions. This application
simulates pension income based on three components:
- Folketrygd (Norwegian state pension from NAV)
- OTP (Occupational pension/Tjenestepensjon)
- Personal savings

The simulator allows users to model different scenarios by adjusting salary levels
(in G-units), retirement ages, savings rates, and growth assumptions to plan for
early retirement or international retirement scenarios.

Note: This is a simplified model for comparative analysis, not an official NAV
calculation tool.
"""

import datetime

import pandas as pd
import streamlit as st

from models import PensionInputs
from pension_calculator import (
    simulate_until_pension_age,
    annual_pension_from_balance,
)

st.set_page_config(page_title="Pensjonssimulator – POC", layout="wide")

st.title("🧮 Pensjonssimulator – POC")

st.markdown("""
En **forenklet** modell for å se hvordan:
- lønn i G  
- hvor lenge du jobber  
- årlig sparing og avkastning  

…påvirker pensjon ved ulike aldre.

🔎 Modellen bruker:
- NAV-lignende opptjening i folketrygden (18 % opp til 7,1 G)
- NAV-lignende **levealdersjustering** med delingsfaktor ved 62–67 år
- Forenklet modell for 68–75 år
- Forenklet modell for OTP og egen sparing

⚠️ Dette er **ikke en offisiell NAV-beregning**, men gir god indikasjon på **retning og størrelsesorden** mellom ulike valg.
""")

# -------- Input (sidebar) --------

with st.sidebar:
    st.header("📥 Input")

    current_age = st.number_input("Alder i dag", value=36, min_value=18, max_value=70)

    # Fødselsår (beregnet grovt: inneværende år - alder)
    current_year = datetime.date.today().year
    birth_year_default = current_year - current_age
    birth_year = st.number_input(
        "Fødselsår", value=birth_year_default, min_value=1900, max_value=current_year
    )

    current_folketrygd_balance = st.number_input(
        "Folketrygd-beholdning (NAV)", value=1_697_820, step=50_000, min_value=0
    )
    current_otp_balance = st.number_input(
        "OTP-beholdning (valgfritt)", value=0, step=10_000, min_value=0
    )
    current_savings = st.number_input(
        "Dagens sparing (fond + bank)", value=660_000, step=10_000, min_value=0
    )

    annual_savings = st.number_input(
        "Årlig egen sparing", value=120_000, step=10_000, min_value=0
    )
    annual_rental_savings = st.number_input(
        "Leieinntekt som spares per år", value=0, step=10_000, min_value=0
    )

    g_amount = st.number_input(
        "G-beløp", value=124_028, step=1_000, min_value=1
    )
    salary_in_g = st.slider("Lønn i G", 3.0, 12.0, 7.1, 0.1)

    work_until_age_default = max(55, int(current_age))
    work_until_age = st.slider("Jobber til alder", current_age, 75, work_until_age_default)
    life_expectancy = st.slider("Forventet levealder", 80, 100, 90)

    st.subheader("Avanserte parametere")
    state_accrual_rate = st.number_input(
        "Folketrygd-opptjening (andel av lønn opp til 7,1 G)",
        value=0.18,
        step=0.01,
    )
    otp_below_rate = st.number_input("OTP-sats 0–7,1 G", value=0.07, step=0.01)
    otp_above_rate = st.number_input("OTP-sats over 7,1 G", value=0.18, step=0.01)
    folketrygd_growth = st.number_input(
        "Årlig vekst folketrygd (regulering)",
        value=0.02,
        step=0.005,
        format="%.3f",
    )
    otp_growth = st.number_input(
        "Årlig vekst tjenestepensjon (OTP)",
        value=0.04,
        step=0.005,
        format="%.3f",
    )
    savings_growth = st.number_input(
        "Årlig avkastning egen sparing",
        value=0.05,
        step=0.005,
        format="%.3f",
    )

    pension_ages = st.multiselect(
        "Vis pensjon for følgende aldre",
        options=[55, 62, 65, 67, 70],
        default=[62, 67, 70],
        help="NAV gir alderspensjon fra 62 år. For aldre under 62 år i tabellen vil folketrygd-delen være forenklet/teoretisk.",
    )

# Validate pension_ages
if not pension_ages:
    st.warning("⚠️ Velg minst én pensjonsalder fra listen over.")
    st.stop()

try:
    inputs = PensionInputs(
        current_age=int(current_age),
        birth_year=int(birth_year),
        current_folketrygd_balance=float(current_folketrygd_balance),
        current_otp_balance=float(current_otp_balance),
        current_savings=float(current_savings),
        annual_savings=float(annual_savings),
        annual_rental_savings=float(annual_rental_savings),
        g_amount=float(g_amount),
        salary_in_g=float(salary_in_g),
        state_accrual_rate=float(state_accrual_rate),
        otp_below_rate=float(otp_below_rate),
        otp_above_rate=float(otp_above_rate),
        folketrygd_growth=float(folketrygd_growth),
        otp_growth=float(otp_growth),
        savings_growth=float(savings_growth),
        life_expectancy=int(life_expectancy),
    )
except (ValueError, TypeError) as e:
    st.error(f"❌ Ugyldig input: {e}")
    st.stop()

# -------- Beregning --------

rows = []

for pa in pension_ages:
    try:
        folketrygd, otp, savings = simulate_until_pension_age(
            inputs=inputs,
            work_until_age=int(work_until_age),
            pension_age=int(pa),
        )

        annual_nav = annual_pension_from_balance(
            balance=folketrygd,
            pension_age=int(pa),
            birth_year=int(birth_year),
            life_expectancy=int(life_expectancy),
            use_nav_style=True,
        )
        annual_otp = annual_pension_from_balance(
            balance=otp,
            pension_age=int(pa),
            birth_year=int(birth_year),
            life_expectancy=int(life_expectancy),
            use_nav_style=False,  # OTP er ikke NAV, så vi bruker enkel modell
        )
        annual_sav = annual_pension_from_balance(
            balance=savings,
            pension_age=int(pa),
            birth_year=int(birth_year),
            life_expectancy=int(life_expectancy),
            use_nav_style=False,
        )

        rows.append({
            "Pensjonsalder": pa,
            "Jobber til": work_until_age,
            "Lønn i G": salary_in_g,
            "Årlig NAV (modell m/levealdersjustering)": round(annual_nav),
            "Årlig OTP (modell)": round(annual_otp),
            "Årlig fra sparing": round(annual_sav),
            "SUM årlig (modell)": round(annual_nav + annual_otp + annual_sav),
        })
    except Exception as e:
        st.error(f"❌ Beregningsfeil for pensjonsalder {pa}: {e}")
        continue

df = pd.DataFrame(rows)

st.subheader("📈 Resultater – grunnscenario")
st.dataframe(df, use_container_width=True)

st.markdown("""
💡 **Tolkning:**

- NAV-delen (folketrygd) bruker delingsfaktor (levealdersjustering) fra 62 år og opp.
- OTP og egen sparing bruker en enklere "levetid / antall år som pensjonist"-modell.
- For tidlige aldre (f.eks. 55) er folketrygd-delen mer teoretisk i denne POC-en – du kan uansett ikke ta ut NAV-pensjon før 62.
- Modellen er best egnet til å sammenligne **scenarier**: 6 G vs 7,1 G, jobbe til 55 vs 67, med/uten ekstra sparing osv.
""")
