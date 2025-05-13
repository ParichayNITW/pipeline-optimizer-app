import os, re
import streamlit as st
import pyomo.environ as pyo
from pyomo.opt import SolverManagerFactory
import pandas as pd
from collections import OrderedDict

# Page configuration and title
st.set_page_config(
    page_title="Mixed Integer Non-Linear Convex Optimisation of Pipeline Operations",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Title only
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

# Footer
def footer():
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:gray; font-size:12px;'>"
        "© 2025 Developed by Parichay Das. All rights reserved."
        "</div>", unsafe_allow_html=True
    )

# Configure NEOS email
os.environ['NEOS_EMAIL'] = 'parichay.nitwarangal@gmail.com'

# Load and clean model script
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

# Solve model
def solve_model():
    ns = dict(os=os, pyo=pyo, SolverManagerFactory=SolverManagerFactory,
              FLOW=FLOW, KV=KV, rho=rho,
              SFC_J=SFC_J, SFC_R=SFC_R, SFC_S=SFC_S,
              RateDRA=RateDRA, Price_HSD=Price_HSD)
    exec(SCRIPT, ns)
    model = ns['model']
    solver = SolverManagerFactory('neos')
    solver.solve(model, opt='bonmin', tee=False)
    return model, ns

# Main UI
if st.sidebar.button("Run Optimization"):
    with st.spinner("Solving optimization via NEOS, please wait..."):
        model, ns = solve_model()
    st.success("Optimization Complete!")

    # Total cost
    total = pyo.value(model.Objf)
    st.markdown(f"<h1 style='text-align:center; font-weight:bold;'>Total Operating Cost: ₹{total:,.2f}</h1>", unsafe_allow_html=True)

    # Define stations and params
    stations = OrderedDict([
        ('Vadinar',       '1'),
        ('Jamnagar',      '2'),
        ('Rajkot',        '3'),
        ('Chotila',       '4'),
        ('Surendranagar', '5'),
        ('Viramgam',      '6'),
    ])
    # Map parameter label to var base and drag index special
    param_map = OrderedDict([
        ('No. of Pumps', 'NOP'),
        ('Drag Reduction (%)', 'DR'),
        ('Maximum Allowable Operating Pressure (bar)', 'MAOP'),
        ('Velocity (m/s)', 'v'),
        ('Reynolds Number', 'Re'),
        ('Friction Factor', 'f'),
        ('Dynamic Head Loss (m)', 'DH'),
        ('Head developed by each Pump (m)', 'TDHA_PUMP'),
        ('Pump Speed (RPM)', 'N'),
        ('Pump Efficiency (%)', 'EFFP'),
        ('Station Discharge Head (m)', 'SDHA'),
        ('Residual Head (m)', 'RH'),
        ('Power Cost (₹)', 'OF_POWER'),
        ('DRA Cost (₹)', 'OF_DRA'),
    ])
    rows = []
    for label, base in param_map.items():
        row = {'Parameter': label}
        for stn, idx in stations.items():
            # skip drag for chotila/viramgam
            if base == 'DR' and stn not in ['Vadinar','Jamnagar','Rajkot','Surendranagar']:
                row[stn] = None
                continue
            # build var name
            var = f"{base}_{idx}"
            # handle RH1 override
            if base=='RH' and stn=='Vadinar':
                val = 50.0
            else:
                val_obj = ns.get(var) if var in ns else getattr(model, var, None)
                try:
                    val = float(pyo.value(val_obj))
                except:
                    val = float(val_obj) if isinstance(val_obj,(int,float)) else None
            # format
            if label=='No. of Pumps' and val is not None:
                row[stn] = int(val)
            elif label=='Pump Efficiency (%)' and val is not None:
                row[stn] = f"{val*100:.2f}%"
            elif val is not None:
                row[stn] = round(val,2)
            else:
                row[stn] = None
        rows.append(row)
    df = pd.DataFrame(rows).set_index('Parameter')

    # Display styled table
    st.subheader("Station-wise Parameter Summary")
    st.table(df)
    footer()
else:
    st.markdown("Enter inputs and click **Run Optimization** to view results.")
    footer()
