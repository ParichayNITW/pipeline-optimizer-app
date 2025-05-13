import os
import re
import streamlit as st
import pyomo.environ as pyo
from pyomo.opt import SolverManagerFactory
import pandas as pd

# Page configuration
st.set_page_config(page_title="Pipeline Optimization App", layout="wide")

# Configure NEOS email
os.environ['NEOS_EMAIL'] = 'parichay.nitwarangal@gmail.com'

# Core solver: load the Pyomo script, solve, and return model + namespace
def solve_pipeline(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD):
    # Load and sanitize original script
    with open('opt.txt') as f:
        code = f.read()
    lines = [l for l in code.splitlines() if not l.strip().startswith('!pip')]
    code = "\n".join(lines)
    code = re.sub(r'.*input\(.*', '', code)
    code = re.sub(r'print\(.*', '', code)

    # Prepare namespace
    local = dict(
        os=os,
        pyo=pyo,
        SolverManagerFactory=SolverManagerFactory,
        FLOW=FLOW,
        KV=KV,
        rho=rho,
        SFC_J=SFC_J,
        SFC_R=SFC_R,
        SFC_S=SFC_S,
        RateDRA=RateDRA,
        Price_HSD=Price_HSD
    )
    exec(code, local)
    model = local['model']

    # Solve remotely
    solver = SolverManagerFactory('neos')
    solver.solve(model, opt='bonmin', tee=False)
    return model, local

# Sidebar inputs
st.sidebar.header("Input Parameters")
FLOW      = st.sidebar.number_input("Flow rate (KL/Hr)",    value=1000.0)
KV        = st.sidebar.number_input("Kinematic Viscosity (cSt)", value=10.0)
rho       = st.sidebar.number_input("Density (kg/m3)",     value=850.0)
SFC_J     = st.sidebar.number_input("SFC at Jamnagar (gm/bhp/hr)", value=200.0)
SFC_R     = st.sidebar.number_input("SFC at Rajkot (gm/bhp/hr)",  value=200.0)
SFC_S     = st.sidebar.number_input("SFC at Surendranagar (gm/bhp/hr)", value=200.0)
RateDRA   = st.sidebar.number_input("DRA Rate (Rs/L)",      value=9.0)
Price_HSD = st.sidebar.number_input("HSD Price (Rs/L)",     value=80.0)

# Run optimization
if st.sidebar.button("Run Optimization"):
    with st.spinner("Optimizing via NEOS..."):
        model, local = solve_pipeline(
            FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD
        )
    st.success("Optimization Complete!")

    # Define stations and their index mappings
    stations = [
        {"name": "Vadinar",       "idx": "1", "dr_idx": "1", "power_idx": "1", "dra_idx": "1", "effp_idx": "1"},
        {"name": "Jamnagar",      "idx": "2", "dr_idx": "2", "power_idx": "2", "dra_idx": "2", "effp_idx": "2"},
        {"name": "Rajkot",        "idx": "3", "dr_idx": "3", "power_idx": "3", "dra_idx": "3", "effp_idx": "3"},
        {"name": "Chotila",       "idx": "4", "dr_idx": None,   "power_idx": None,   "dra_idx": None,   "effp_idx": None},
        {"name": "Surendranagar", "idx": "5", "dr_idx": "4", "power_idx": "4", "dra_idx": "4", "effp_idx": "5"},
        {"name": "Viramgam",      "idx": "6", "dr_idx": None,   "power_idx": None,   "dra_idx": None,   "effp_idx": None},
    ]

    # Build results rows
    rows = []
    for s in stations:
        row = {"Station": s["name"]}
        idx = s["idx"]
        # Number of Pumps
        try:
            row["Number of Pumps"] = pyo.value(getattr(model, f"NOP{idx}"))
        except:
            row["Number of Pumps"] = None
        # Drag Reduction (%)
        if s["dr_idx"]:
            row["Drag Reduction (%)"] = pyo.value(getattr(model, f"DR{s['dr_idx']}"))
        else:
            row["Drag Reduction (%)"] = None
        # Pump Speed (RPM)
        try:
            row["Pump Speed (RPM)"] = pyo.value(getattr(model, f"N{idx}"))
        except:
            row["Pump Speed (RPM)"] = None
        # Residual Head (m)
        try:
            row["Residual Head (m)"] = pyo.value(getattr(model, f"RH{idx}"))
        except:
            row["Residual Head (m)"] = None
        # Station Discharge Head (m)
        key_sdh = f"SDHA_{idx}"
        sdh_val = local.get(key_sdh)
        row["Station Discharge Head (m)"] = pyo.value(sdh_val) if sdh_val is not None else None
        # Pump Efficiency (%)
        if s["effp_idx"]:
            effp_val = local.get(f"EFFP{s['effp_idx']}")
            row["Pump Efficiency (%)"] = pyo.value(effp_val)
        else:
            row["Pump Efficiency (%)"] = None
        # Power Cost (₹)
        if s["power_idx"]:
            pc_val = local.get(f"OF_POWER_{s['power_idx']}")
            row["Power Cost (₹)"] = pyo.value(pc_val)
        else:
            row["Power Cost (₹)"] = None
        # DRA Cost (₹)
        if s["dra_idx"]:
            dc_val = local.get(f"OF_DRA_{s['dra_idx']}")
            row["DRA Cost (₹)"] = pyo.value(dc_val)
        else:
            row["DRA Cost (₹)"] = None
        rows.append(row)

    # Create DataFrame and display
    df = pd.DataFrame(rows).set_index('Station')

    # Total Operating Cost
    total_cost = pyo.value(model.Objf)
    st.metric("Total Operating Cost (₹)", f"{total_cost:,.2f}")

    st.subheader("Station-wise Optimization Results")
    st.table(df)
else:
    st.title("Pipeline Optimization App")
    st.markdown(
        "Enter inputs in the sidebar, click **Run Optimization**, and view pumps, drag reduction, speed, heads, efficiency, and costs per station, plus total operating cost."
    )
