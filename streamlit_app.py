import os, re
import streamlit as st
import pyomo.environ as pyo
from pyomo.opt import SolverManagerFactory
import pandas as pd

# Page configuration
st.set_page_config(page_title="Pipeline Optimization App", layout="wide")

# Configure NEOS email for remote solves
os.environ['NEOS_EMAIL'] = 'parichay.nitwarangal@gmail.com'

# Core function: load, solve, and return the model

def solve_pipeline(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD):
    # Read and sanitize the original Pyomo script
    with open('opt.txt') as f:
        code = f.read()
    code = '\n'.join([l for l in code.splitlines() if not l.strip().startswith('!pip')])
    code = re.sub(r'.*input\(.*', '', code)
    code = re.sub(r'print\(.*', '', code)

    # Prepare namespace with user inputs
    local = dict(
        os=os, pyo=pyo, SolverManagerFactory=SolverManagerFactory,
        FLOW=FLOW, KV=KV, rho=rho,
        SFC_J=SFC_J, SFC_R=SFC_R, SFC_S=SFC_S,
        RateDRA=RateDRA, Price_HSD=Price_HSD
    )

    # Execute the script (defines `model` with all Params, Vars, Expressions)
    exec(code, local)
    model = local['model']

    # Solve via NEOS Bonmin
    solver = SolverManagerFactory('neos')
    solver.solve(model, opt='bonmin', tee=False)
    return model

# Sidebar: user inputs
st.sidebar.header("Input Parameters")
FLOW      = st.sidebar.number_input("Flow rate (KL/Hr)",    value=1000.0)
KV        = st.sidebar.number_input("Kinematic Viscosity (cSt)", value=10.0)
rho       = st.sidebar.number_input("Density (kg/m3)",     value=850.0)
SFC_J     = st.sidebar.number_input("SFC at Jamnagar (gm/bhp/hr)", value=200.0)
SFC_R     = st.sidebar.number_input("SFC at Rajkot (gm/bhp/hr)", value=200.0)
SFC_S     = st.sidebar.number_input("SFC at Surendranagar (gm/bhp/hr)", value=200.0)
RateDRA   = st.sidebar.number_input("DRA Rate (Rs/L)",      value=9.0)
Price_HSD = st.sidebar.number_input("HSD Price (Rs/L)",     value=80.0)

# Run optimization
if st.sidebar.button("Run Optimization"):
    with st.spinner("Optimizing via NEOS..."):
        model = solve_pipeline(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD)
    st.success("Optimization Complete!")

    # Build results for each station
    stations = {
        'Vadinar':        {'idx':'1','dr':'1','power':'1','dra':'1','rh':'1','sdh':'1','effp':'1'},
        'Jamnagar':       {'idx':'2','dr':'2','power':'2','dra':'2','rh':'2','sdh':'2','effp':'2'},
        'Rajkot':         {'idx':'3','dr':'3','power':'3','dra':'3','rh':'3','sdh':'3','effp':'3'},
        'Surendranagar':  {'idx':'5','dr':'4','power':'4','dra':'4','rh':'5','sdh':'5','effp':'5'},
    }

    results = []
    for name, d in stations.items():
        i = d['idx']
        results.append({
            'Station': name,
            'Number of Pumps':    pyo.value(getattr(model, f"NOP{i}")),
            'Drag Reduction (%)':  pyo.value(getattr(model, f"DR{d['dr']}")),
            'Pump Speed (RPM)':    pyo.value(getattr(model, f"N{i}")),
            'Residual Head (m)':   pyo.value(getattr(model, f"RH{d['rh']}")),
            'Station Discharge Head (m)': pyo.value(getattr(model, f"SDHA_{d['sdh']}")),
            'Pump Efficiency (%)': pyo.value(getattr(model, f"EFFP{d['effp']}")),
            'Power Cost (₹)':      pyo.value(getattr(model, f"OF_POWER_{d['power']}")),
            'DRA Cost (₹)':        pyo.value(getattr(model, f"OF_DRA_{d['dra']}")),
        })

    df = pd.DataFrame(results)
    df = df.set_index('Station')

    # Display total operating cost
    total_cost = pyo.value(model.Objf)
    st.metric("Total Operating Cost (₹)", f"{total_cost:,.2f}")

    # Display station-wise results
    st.subheader("Station-wise Optimization Results")
    st.table(df)
else:
    st.title("Pipeline Optimization App")
    st.markdown(
        "Enter the inputs in the sidebar, then click **Run Optimization**.\n"
        "You will see the number of pumps, drag reduction, speed, residual head, station discharge head, pump efficiency, and power & DRA costs for each station, plus total operating cost."
    )
