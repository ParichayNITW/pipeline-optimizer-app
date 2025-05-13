import os, re
import streamlit as st
import pyomo.environ as pyo
from pyomo.opt import SolverManagerFactory
import pandas as pd

# Page configuration and title
st.set_page_config(
    page_title="Mixed Integer Non-Linear Convex Optimisation of Pipeline Operations",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("Mixed Integer Non-Linear Convex Optimisation of Pipeline Operations")

# Sidebar inputs
st.sidebar.header("Pipeline Inputs")
FLOW      = st.sidebar.number_input("Flow rate (KL/Hr)", value=1000.0)
KV        = st.sidebar.number_input("Kinematic Viscosity (cSt)", value=10.0)
rho       = st.sidebar.number_input("Density (kg/m3)", value=850.0)
SFC_J     = st.sidebar.number_input("SFC at Jamnagar (gm/bhp/hr)", value=200.0)
SFC_R     = st.sidebar.number_input("SFC at Rajkot (gm/bhp/hr)", value=200.0)
SFC_S     = st.sidebar.number_input("SFC at Surendranagar (gm/bhp/hr)", value=200.0)
RateDRA   = st.sidebar.number_input("DRA Rate (Rs/L)", value=9.0)
Price_HSD = st.sidebar.number_input("HSD Price (Rs/L)", value=80.0)

# Footer function
def footer():
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:gray; font-size:12px;'>"
        "© 2025 Developed by Parichay Das. All rights reserved."  
        "</div>", unsafe_allow_html=True
    )

# Configure NEOS solver email
os.environ['NEOS_EMAIL'] = 'parichay.nitwarangal@gmail.com'

# Load and sanitize the Pyomo model script once
@st.cache_resource
def load_script():
    with open('opt.txt') as f:
        txt = f.read()
    lines = [l for l in txt.splitlines() if not l.strip().startswith('!pip')]
    code = '\n'.join(lines)
    code = re.sub(r'.*input\(.*', '', code)
    code = re.sub(r'print\(.*', '', code)
    return code

SCRIPT = load_script()

# Solve model and return raw values (no caching to avoid pickling issues)
def solve_model(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD):
    # Prepare namespace
    ns = dict(
        os=os, pyo=pyo, SolverManagerFactory=SolverManagerFactory,
        FLOW=FLOW, KV=KV, rho=rho,
        SFC_J=SFC_J, SFC_R=SFC_R, SFC_S=SFC_S,
        RateDRA=RateDRA, Price_HSD=Price_HSD
    )
    # Build and solve model
    exec(SCRIPT, ns)
    model = ns['model']
    solver = SolverManagerFactory('neos')
    solver.solve(model, opt='bonmin', tee=False)
    return model, ns

# Main app logic
if st.sidebar.button("Run Optimization"):
    with st.spinner("Optimizing via NEOS... please wait"):
        model, ns = solve_model(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD)
    st.success("Optimization Complete!")

    # Display total operating cost (bold, large)
    total_cost = pyo.value(model.Objf)
    st.markdown(
        f"<h1 style='text-align:center; font-weight:bold;'>"
        f"Total Operating Cost: ₹{total_cost:,.2f}"
        f"</h1>", unsafe_allow_html=True
    )

    # Define stations and parameters
    stations = {'Vadinar':1, 'Jamnagar':2, 'Rajkot':3, 'Surendranagar':5}
    params = {
        'No. of Pumps': 'NOP',
        'Drag Reduction (%)': 'DR',
        'Maximum Operating Allowable Pressure (bar)': 'MAOP',
        'Velocity (m/s)': 'v',
        'Reynolds Number': 'Re',
        'Friction Factor': 'f',
        'Dynamic Head Loss (m)': 'DH',
        'Pump Head Developed (m)': 'TDHA_PUMP',
        'Residual Head (m)': 'RH'
    }
    # Build transposed results
    result_data = {}
    for station, idx in stations.items():
        row = []
        for label, key in params.items():
            var_name = f"{key}{idx}"
            val_obj = ns.get(var_name) if var_name in ns else getattr(model, var_name, None)
            try:
                num = float(pyo.value(val_obj))
            except:
                num = float(val_obj) if isinstance(val_obj, (int, float)) else None
            # Format integers and decimals
            if label=='No. of Pumps' and num is not None:
                num = int(num)
            elif num is not None:
                num = round(num, 2)
            row.append(num)
        result_data[station] = row
    df = pd.DataFrame(result_data, index=list(params.keys()))

    # Display table
    st.subheader("Station-wise Parameter Summary")
    st.table(df)
    footer()
else:
    st.markdown("Enter your pipeline inputs in the sidebar and click **Run Optimization** to view results.")
    footer()
