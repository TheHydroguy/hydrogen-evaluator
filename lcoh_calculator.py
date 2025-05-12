
def calculate_lcoh(
    capex_per_mw,
    opex_per_mw,
    plant_size_mw,
    plant_lifetime_years,
    discount_rate,
    elec_cost_per_mwh,
    capacity_factor,
    efficiency_kwh_per_kg,
    storage_cost_per_kg=0.0,
    transport_cost_per_kg=0.0
):
    # Convert percentages to decimals
    capacity_factor /= 100
    discount_rate /= 100

    # Hours per year
    hours_per_year = 8760

    # Calculate CRF
    crf = (discount_rate * (1 + discount_rate) ** plant_lifetime_years) / ((1 + discount_rate) ** plant_lifetime_years - 1)

    # Annual hydrogen production (kg/year)
    annual_h2_kg = (capacity_factor * hours_per_year * plant_size_mw * 1000) / efficiency_kwh_per_kg

    # Annualized CAPEX ($/year)
    annual_capex = capex_per_mw * plant_size_mw * crf

    # Annual OPEX ($/year)
    annual_opex = opex_per_mw * plant_size_mw

    # Electricity cost ($/year)
    elec_cost = (elec_cost_per_mwh / 1000) * efficiency_kwh_per_kg * annual_h2_kg

    # Total cost per year
    total_cost_per_year = annual_capex + annual_opex + elec_cost + (storage_cost_per_kg * annual_h2_kg) + (transport_cost_per_kg * annual_h2_kg)

    # LCOH ($/kg H2)
    lcoh = total_cost_per_year / annual_h2_kg

    # Breakdown
    capex_per_kg = annual_capex / annual_h2_kg
    opex_per_kg = annual_opex / annual_h2_kg
    elec_per_kg = elec_cost / annual_h2_kg

    return {
        "LCOH": round(lcoh, 2),
        "CAPEX_per_kg": round(capex_per_kg, 2),
        "OPEX_per_kg": round(opex_per_kg, 2),
        "Elec_per_kg": round(elec_per_kg, 2),
        "Storage_per_kg": round(storage_cost_per_kg, 2),
        "Transport_per_kg": round(transport_cost_per_kg, 2),
        "Annual_H2_kg": int(annual_h2_kg),
        "CRF": round(crf, 6)
    }
