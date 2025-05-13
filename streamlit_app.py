import os, re
import streamlit as st
import pyomo.environ as pyo
from pyomo.opt import SolverManagerFactory
import pandas as pd
from collections import OrderedDict

# Page configuration
st.set_page_config(
    page_title="Mixed Integer Non-Linear Convex Optimisation of Pipeline Operations",
    layout="wide"
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

# NEOS configuration
ios_email = 'parichay.nitwarangal@gmail.com'
os.environ['NEOS_EMAIL'] = ios_email

# Load model script
@st.cache_resource
def load_script():
    code = []
    with open('opt.txt') as f:
        for ln in f:
            if ln.strip().startswith(('!pip','print','input')):
                continue
            code.append(ln)
    return ''.join(code)
SCRIPT = load_script()

# Solve model
def solve_model():
    ns = dict(os=os, pyo=pyo, SolverManagerFactory=SolverManagerFactory,
              FLOW=FLOW, KV=KV, rho=rho,
              SFC_J=SFC_J, SFC_R=SFC_R, SFC_S=SFC_S,
              RateDRA=RateDRA, Price_HSD=Price_HSD)
    exec(SCRIPT, ns)
    model = ns['model']
    SolverManagerFactory('neos').solve(model, opt='bonmin', tee=False)
    return model, ns

if st.sidebar.button("Run Optimization"):
    model, ns = solve_model()
    # Total cost
    total = pyo.value(model.Objf)
    st.markdown(f"<h1 style='text-align:center; font-weight:bold;'>Total Operating Cost: ₹{total:,.2f}</h1>", unsafe_allow_html=True)

    # Stations and elements
    stations = OrderedDict([('Vadinar','1'),('Jamnagar','2'),('Rajkot','3'),('Chotila','4'),('Surendranagar','5'),('Viramgam','6')])
    desired = OrderedDict([
        ('No. of Pumps','NOP'),('Drag Reduction (%)','DR'),('Pump Speed (RPM)','N'),
        ('Pump Efficiency (%)','EFFP'),('Station Discharge Head (m)','SDHA'),
        ('Residual Head (m)','RH'),('Power Cost (₹)','OF_POWER'),('DRA Cost (₹)','OF_DRA')
    ])
    data = {k:[] for k in desired}
    for param, base in desired.items():
        for stn, idx in stations.items():
            # Chotila & Viramgam: zero except RH
            if stn in ['Chotila','Viramgam'] and base!='RH':
                val = 0.0
            else:
                varname = f"{base}_{idx}" if base in ['SDHA','OF_POWER','OF_DRA','RH'] else f"{base}{idx}"
                # RH override
                if base=='RH' and stn=='Vadinar':
                    val = 50.0
                else:
                    comp = getattr(model, varname, None)
                    val = float(pyo.value(comp)) if comp is not None else None
            # format
            if base=='NOP' and val is not None:
                data[param].append(int(val))
            elif base=='EFFP' and val is not None:
                data[param].append(f"{val*100:.2f}%")
            elif val is not None:
                data[param].append(round(val,2))
            else:
                data[param].append(None)
    df = pd.DataFrame(data, index=list(stations.keys())).T
    st.subheader("Station-wise Parameter Summary")
    st.table(df)
    footer()
else:
    st.markdown("Enter inputs and click **Run Optimization** to view results.")
    footer()
