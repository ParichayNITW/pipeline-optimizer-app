import os
import streamlit as st
import pyomo.environ as pyo
from pyomo.opt import SolverFactory

# Page setup
st.set_page_config(page_title="Pipeline Optimizer", layout="wide")
st.title("Pipeline Optimizer")

# Sidebar inputs with full labels
flow_rate = st.sidebar.number_input("Flow rate (kiloliters per hour)", value=1000.0)
kinematic_viscosity = st.sidebar.number_input("Kinematic viscosity (centistokes)", value=10.0)
density = st.sidebar.number_input("Density (kilograms per cubic meter)", value=850.0)
specific_fuel_consumption = st.sidebar.number_input("Specific fuel consumption (grams per brake horsepower-hour)", value=200.0)
dra_cost_rate = st.sidebar.number_input("Drag reducing agent cost rate (rupees per liter)", value=9.0)
hsd_price = st.sidebar.number_input("High-speed diesel price (rupees per liter)", value=80.0)

# Load the Pyomo model from opt.txt
with open('opt.txt') as f:
    model_script = f.read()

# Solve function
@st.cache_resource
def solve_pipeline_model(flow, viscosity, rho, sfc, dra_rate, diesel_price):
    ns = dict(
        FLOW=flow,
        KV=viscosity,
        rho=rho,
        SFC=sfc,
        RateDRA=dra_rate,
        PriceHSD=diesel_price,
        pyo=pyo
    )
    exec(model_script, ns)
    model = ns['model']
    solver = SolverFactory('bonmin')
    solver.solve(model)
    return model

# Map station indices to names
station_names = {
    '1': 'Vadinar',
    '2': 'Jamnagar',
    '3': 'Rajkot',
    '4': 'Chotila',
    '5': 'Surendranagar',
    '6': 'Viramgam'
}

if st.sidebar.button("Run Optimization"):
    model = solve_pipeline_model(
        flow_rate,
        kinematic_viscosity,
        density,
        specific_fuel_consumption,
        dra_cost_rate,
        hsd_price
    )
    st.header("Optimization Results")
    # Display the objective
    total_cost = pyo.value(model.Objf)
    st.write(f"**Total Operating Cost (₹):** {total_cost:,.2f}")

        # Loop over stations for detailed outputs
    for idx, name in station_names.items():
        st.subheader(f"Station: {name}")
        # Number of pumps
        var_nop = f"NOP{idx}"
        num_pumps = int(pyo.value(getattr(model, var_nop))) if hasattr(model, var_nop) else None
        st.write(f"- Number of Pumps: {num_pumps}")
        # Drag Reduction
        var_dr = f"DR{idx}"
        if hasattr(model, var_dr):
            dr = pyo.value(getattr(model, var_dr))
            st.write(f"- Drag Reduction (%): {dr:.2f}")
        # Pump Speed
        var_n = f"N{idx}"
        if hasattr(model, var_n):
            speed = pyo.value(getattr(model, var_n))
            st.write(f"- Pump Speed (RPM): {speed:.2f}")
        # Pump Efficiency
        var_eff = f"EFFP{idx}"
        if hasattr(model, var_eff):
            eff = pyo.value(getattr(model, var_eff))*100
            st.write(f"- Pump Efficiency (%): {eff:.2f}")
        # Station Discharge Head
        var_sdha = f"SDHA{idx}"
        if hasattr(model, var_sdha):
            sdha = pyo.value(getattr(model, var_sdha))
            st.write(f"- Station Discharge Head (m): {sdha:.2f}")
        # Residual Head
        var_rh = f"RH{idx}"
        if hasattr(model, var_rh):
            rh = pyo.value(getattr(model, var_rh))
            st.write(f"- Residual Head (m): {rh:.2f}")
        # Power Cost
        var_pow = f"OF_POWER{idx}"
        if hasattr(model, var_pow):
            powc = pyo.value(getattr(model, var_pow))
            st.write(f"- Power Cost (₹): {powc:.2f}")
        # DRA Cost
        var_dra = f"OF_DRA{idx}"
        if hasattr(model, var_dra):
            drac = pyo.value(getattr(model, var_dra))
            st.write(f"- DRA Cost (₹): {drac:.2f}")
else:
    st.write("Enter all inputs in the sidebar and click **Run Optimization** to view results.")
    st.write("Enter all inputs in the sidebar and click **Run Optimization** to view results.")
