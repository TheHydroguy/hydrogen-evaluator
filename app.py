import streamlit as st
import matplotlib.pyplot as plt
from lcoh_calculator import calculate_lcoh

st.set_page_config(page_title="Hydrogen Project Evaluator", layout="centered")
st.title("🔬 Hydrogen Project Evaluator")

# Initialize session state
if "lcoh_results" not in st.session_state:
    st.session_state.lcoh_results = None

# SECTION 1 – Inputs
st.header("1️⃣ Core Project Inputs")
with st.form("core_inputs"):
    col1, col2 = st.columns(2)
    with col1:
        capex = st.number_input("CAPEX [$ / MW / year]", value=2_000_000)
        opex = st.number_input("OPEX [$ / MW / year]", value=90_000)
        plant_size = st.number_input("Electrolyzer Size [MW]", value=10)
        lifetime = st.number_input("Plant Lifetime [years]", value=20)
    with col2:
        discount_rate = st.number_input("Discount Rate [%]", value=7.0)
        elec_cost = st.number_input("Electricity Cost [$ / MWh]", value=50.0)
        cap_factor = st.number_input("Capacity Factor [%]", value=50.0)
        efficiency = st.number_input("H2 Efficiency [kWh / kg]", value=50.0)

    st.markdown("### Optional Costs")
    add_storage = st.checkbox("Include Storage Cost?")
    add_transport = st.checkbox("Include Transport Cost?")
    storage_cost = st.number_input("Storage Cost [$ / kg]", value=0.0) if add_storage else 0.0
    transport_cost = st.number_input("Transport Cost [$ / kg]", value=0.0) if add_transport else 0.0

    submitted = st.form_submit_button("🧮 Calculate")

if submitted:
    st.session_state.lcoh_results = calculate_lcoh(
        capex_per_mw=capex,
        opex_per_mw=opex,
        plant_size_mw=plant_size,
        plant_lifetime_years=lifetime,
        discount_rate=discount_rate,
        elec_cost_per_mwh=elec_cost,
        capacity_factor=cap_factor,
        efficiency_kwh_per_kg=efficiency,
        storage_cost_per_kg=storage_cost,
        transport_cost_per_kg=transport_cost
    )

# Show results if LCOH was calculated
if st.session_state.lcoh_results:
    results = st.session_state.lcoh_results
    st.success("✅ LCOH Calculated:")
    st.metric("Levelized Cost of Hydrogen (LCOH)", f"${results['LCOH']}/kg")
    st.markdown(f"""
    **Breakdown:**  
    • CAPEX: ${results['CAPEX_per_kg']}/kg  
    • OPEX: ${results['OPEX_per_kg']}/kg  
    • Electricity: ${results['Elec_per_kg']}/kg  
    • Storage: ${results['Storage_per_kg']}/kg  
    • Transport: ${results['Transport_per_kg']}/kg  
    """)
    st.caption(f"Annual H₂ Production: {results['Annual_H2_kg']:,} kg | CRF: {results['CRF']}")

    # SECTION 2 – Incentives
    st.header("2️⃣ Incentives and Credits")
    col1, col2 = st.columns(2)
    with col1:
        ira_credit = st.number_input("IRA 45V Credit [$ / kg H₂]", value=3.0)
        rec_credit = st.number_input("REC Credit [$ / MWh]", value=20.0)
    with col2:
        carbon_credit = st.number_input("Carbon Credit [$ / ton CO₂]", value=50.0)
        co2_avoided = st.number_input("CO₂ Avoided [kg / kg H₂]", value=10.0)

    rec_component = rec_credit * efficiency / 1000
    carbon_component = (carbon_credit * co2_avoided) / 1000
    total_credit = ira_credit + rec_component + carbon_component
    st.metric("Total Incentive Value", f"${round(total_credit, 2)}/kg")

    # SECTION 3 – Financials
    st.header("3️⃣ Financial Performance")
    h2_price = st.number_input("Hydrogen Selling Price [$ / kg]", value=15.0)

    annual_revenue = (h2_price + total_credit) * results['Annual_H2_kg']
    annual_cost = results['LCOH'] * results['Annual_H2_kg']
    annual_profit = annual_revenue - annual_cost
    initial_investment = capex * plant_size

    if discount_rate > 0:
        npv = round((annual_profit * ((1 - (1 + discount_rate / 100) ** -lifetime) / (discount_rate / 100))) - initial_investment, 2)
    else:
        npv = "N/A"

    payback = round(initial_investment / annual_profit, 2) if annual_profit > 0 else "N/A"
    roi = round((annual_profit / initial_investment) * 100, 2) if annual_profit > 0 else "N/A"

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Annual Profit", f"${round(annual_profit/1e6,2)}M")
        st.metric("NPV (20 yrs)", f"${npv/1e6}M" if isinstance(npv, (int, float)) else "N/A")
    with col2:
        st.metric("Payback Period", f"{payback} years")
        st.metric("ROI", f"{roi}%")

    # SECTION 4 – Charts
    st.header("4 Visualize Project Analysis")

    # Chart 1 – LCOH vs Electricity Price
if st.button("📊 LCOH vs. Electricity Price"):
    elec_range = np.linspace(20, 100, 20)
    lcoh_values = []
    for e in elec_range:
        temp_result = calculate_lcoh(
            capex_per_mw=capex,
            opex_per_mw=opex,
            plant_size_mw=plant_size,
            plant_lifetime_years=lifetime,
            discount_rate=discount_rate,
            elec_cost_per_mwh=e,
            capacity_factor=cap_factor,
            efficiency_kwh_per_kg=efficiency,
            storage_cost_per_kg=storage_cost,
            transport_cost_per_kg=transport_cost
        )
        lcoh_values.append(temp_result["LCOH"])

    fig1, ax1 = plt.subplots()
    ax1.plot(elec_range, lcoh_values, marker='o')
    ax1.set_title("LCOH vs Electricity Price")
    ax1.set_xlabel("Electricity Price ($/MWh)")
    ax1.set_ylabel("LCOH ($/kg H₂)")
    st.pyplot(fig1)

# Chart 2 – NPV vs LCOH
if st.button("📈 NPV vs. LCOH"):
    lcoh_test_vals = np.linspace(2, 10, 20)
    npvs = []
    for test_lcoh in lcoh_test_vals:
        total_cost = test_lcoh * results["Annual_H2_kg"]
        test_profit = (h2_price + total_credit) * results["Annual_H2_kg"] - total_cost
        test_npv = (test_profit * ((1 - (1 + discount_rate / 100) ** -lifetime) / (discount_rate / 100))) - (capex * plant_size)
        npvs.append(test_npv / 1e6)

    fig2, ax2 = plt.subplots()
    ax2.plot(lcoh_test_vals, npvs, color='purple', marker='x')
    ax2.set_title("NPV vs LCOH")
    ax2.set_xlabel("LCOH ($/kg H₂)")
    ax2.set_ylabel("NPV (Million USD)")
    st.pyplot(fig2)
'''

# Append smart visualization block to the app
with open(app_path, "a") as f:
    f.write(updated_charts_code)

app_path
