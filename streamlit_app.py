import os, re
import streamlit as st
import pyomo.environ as pyo
from pyomo.opt import SolverManagerFactory
import pandas as pd

# Title and page config
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

# Configure NEOS
os.environ['NEOS_EMAIL'] = 'parichay.nitwarangal@gmail.com'

# Load Pyomo model script
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

# Solver function
@st.cache_data
def solve_model(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD):
    ns = dict(os=os, pyo=pyo, SolverManagerFactory=SolverManagerFactory,
              FLOW=FLOW, KV=KV, rho=rho,
              SFC_J=SFC_J, SFC_R=SFC_R, SFC_S=SFC_S,
              RateDRA=RateDRA, Price_HSD=Price_HSD)
    exec(SCRIPT, ns)
    model = ns['model']
    solver = SolverManagerFactory('neos')
    solver.solve(model, opt='bonmin', tee=False)
    return model, ns

# On button
if st.sidebar.button("Run Optimization"):
    with st.spinner("Running optimization via NEOS..."):
        model, ns = solve_model(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD)
    st.markdown(f"<h1 style='text-align:center'>Total Operating Cost: ₹{pyo.value(model.Objf):,.2f}</h1>", unsafe_allow_html=True)

    # Station parameter mapping
    stations = {
        'Vadinar': 1,
        'Jamnagar': 2,
        'Rajkot': 3,
        'Chotila': 4,
        'Surendranagar': 5,
        'Viramgam': 6
    }
    # Parameters to extract
    params = {
        'No. of Pumps': 'NOP',
        'Drag Reduction (%)': 'DR',
        'Maximum Operating Allowable Pressure (bar)': 'MAOP',
        'Velocity (m/s)': 'v',
        'Reynolds Number': 'Re',
        'Friction Factor': 'f',
        'Dynamic Head Loss (m)': 'DH',
        'Pump Head Developed (m)': 'TDHA_PUMP'
    }
    # Build DataFrame
    data = {}
    for stat, idx in stations.items():
        col = []
        for label, key in params.items():
            var = f"{key}{idx}"
            if var in ns:
                val = ns[var]
            elif hasattr(model, var):
                val = getattr(model, var)
            else:
                val = None
            try:
                num = float(pyo.value(val))
            except:
                num = float(val) if isinstance(val, (int, float)) else None
            if label == 'No. of Pumps' and num is not None:
                num = int(num)
            col.append(num)
        data[stat] = col
    df = pd.DataFrame(data, index=list(params.keys()))
    df = df.round(2)

    # Transposed table display
    st.subheader("Station-wise Parameter Summary")
    st.table(df)

    # Footer
    st.markdown("---")
    st.markdown("<div style='text-align:center; color:gray; font-size:12px;'>© 2025 Developed by Parichay Das. All rights reserved.</div>", unsafe_allow_html=True)
else:
    st.markdown("Enter your pipeline inputs in the sidebar and click **Run Optimization**.")
