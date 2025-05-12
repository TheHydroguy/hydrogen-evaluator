
import streamlit as st
from lcoh_calculator import calculate_lcoh

st.set_page_config(page_title="Hydrogen Project Evaluator", layout="centered")
st.title("🔬 Hydrogen Project Evaluator")
st.markdown("Estimate LCOH, incentive impact, and financials for hydrogen production.")

# Initialize session state variables
if "lcoh_results" not in st.session_state:
    st.session_state.lcoh_results = None

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

    st.markdown("### Optional: Include Storage and Transport Costs")
    add_storage = st.checkbox("Include Storage Cost?")
    add_transport = st.checkbox("Include Transport Cost?")
    storage_cost = st.number_input("Storage Cost [$ / kg H₂]", value=0.0) if add_storage else 0.0
    transport_cost = st.number_input("Transport Cost [$ / kg H₂]", value=0.0) if add_transport else 0.0

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

# If LCOH results exist, show next sections
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

    st.header("2️⃣ Incentives and Credits (Optional)")
    col1, col2 = st.columns(2)
    with col1:
        ira_credit = st.number_input("IRA 45V Credit [$ / kg H₂]", value=3.0, key="ira")
        rec_credit = st.number_input("REC Credit [$ / MWh]", value=20.0, key="rec")
    with col2:
        carbon_credit = st.number_input("Carbon Credit [$ / ton CO₂]", value=50.0, key="carbon")
        co2_avoided = st.number_input("CO₂ Avoided [kg / kg H₂]", value=10.0, key="co2")

    rec_component = rec_credit * efficiency / 1000
    carbon_component = (carbon_credit * co2_avoided) / 1000
    total_credit = ira_credit + rec_component + carbon_component
    st.metric("Total Incentive Value", f"${round(total_credit, 2)}/kg H₂")

    st.header("3️⃣ Financial Performance")
    h2_price = st.number_input("Hydrogen Selling Price [$ / kg H₂]", value=15.0, key="price")

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

    # SECTION 4 – GPT Summary
    st.header("4️⃣ AI Project Summary (ChatGPT)")
st.markdown("This summary is generated using OpenAI's GPT based on your project inputs.")

if st.button("🧠 Generate GPT Summary"):
    try:
        import openai
        openai.api_key = st.secrets["openai"]["api_key"]

        prompt = f"""
        Summarize this hydrogen project:
        - LCOH: ${results['LCOH']}/kg
        - Plant Size: {plant_size} MW
        - Electricity Cost: ${elec_cost}/MWh
        - Incentives: ${round(total_credit, 2)}/kg
        - NPV: {npv}
        - ROI: {roi}%
        - Payback Period: {payback} years

        Provide a 100-word summary explaining if this project is financially attractive and why.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )

        gpt_summary = response["choices"][0]["message"]["content"]
        st.markdown("### 🤖 GPT Summary")
        st.success(gpt_summary)

    except Exception as e:
        st.error(f"Error generating summary: {e}")
