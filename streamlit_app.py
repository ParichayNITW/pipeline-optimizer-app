import os, re
import streamlit as st
import pyomo.environ as pyo
from pyomo.opt import SolverManagerFactory
import pandas as pd
from collections import OrderedDict

# Page config and title
st.set_page_config(page_title="Mixed Integer Non-Linear Convex Optimisation of Pipeline Operations", layout="wide")
st.title("Mixed Integer Non-Linear Convex Optimisation of Pipeline Operations")

# Sidebar inputs
st.sidebar.header("Pipeline Inputs")
FLOW = st.sidebar.number_input("Flow rate (KL/Hr)", 1000.0)
KV = st.sidebar.number_input("Kinematic Viscosity (cSt)", 10.0)
rho = st.sidebar.number_input("Density (kg/m3)", 850.0)
SFC_J = st.sidebar.number_input("SFC at Jamnagar (gm/bhp/hr)", 200.0)
SFC_R = st.sidebar.number_input("SFC at Rajkot (gm/bhp/hr)", 200.0)
SFC_S = st.sidebar.number_input("SFC at Surendranagar (gm/bhp/hr)", 200.0)
RateDRA = st.sidebar.number_input("DRA Rate (Rs/L)", 9.0)
Price_HSD = st.sidebar.number_input("HSD Price (Rs/L)", 80.0)

# Footer
def footer():
    st.markdown("---")
    st.markdown("<div style='text-align:center; color:gray; font-size:12px;'>© 2025 Developed by Parichay Das. All rights reserved.</div>", unsafe_allow_html=True)

# Configure NEOS email
ios_email = 'parichay.nitwarangal@gmail.com'
os.environ['NEOS_EMAIL'] = ios_email

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
    with st.spinner("Optimizing via NEOS... please wait"):
        model, ns = solve_model()
    st.success("Optimization Complete!")

    # Display total cost
    total = pyo.value(model.Objf)
    st.markdown(f"<h1 style='text-align:center; font-weight:bold;'>Total Operating Cost: ₹{total:,.2f}</h1>", unsafe_allow_html=True)

    # Setup stations and parameters
    stations = OrderedDict([('Vadinar','1'),('Jamnagar','2'),('Rajkot','3'),('Chotila','4'),('Surendranagar','5'),('Viramgam','6')])
    desired = OrderedDict([
        ('No. of Pumps','NOP'),('Drag Reduction (%)','DR'),('Pump Speed (RPM)','N'),
        ('Pump Efficiency (%)','EFFP'),('Station Discharge Head (m)','SDHA'),
        ('Residual Head (m)','RH'),('Power Cost (₹)','OF_POWER'),('DRA Cost (₹)','OF_DRA')
    ])

    # Build result DataFrame
    data = {param:[] for param in desired.keys()}
        # Build result DataFrame
    data = {param: [] for param in desired.keys()}
    for param, base in desired.items():
        for stn, idx in stations.items():
            # Only RH for Chotila/Viramgam, others zero
            if stn in ['Chotila','Viramgam']:
                if base == 'RH':
                    rh_var = f"RH_{idx}"
                    try:
                        val = float(pyo.value(ns.get(rh_var, getattr(model, rh_var))))
                    except:
                        val = None
                else:
                    val = 0.0
            else:
                # Determine variable name
                if base in ['SDHA','OF_POWER','OF_DRA','RH']:
                    varname = f"{base}_{idx}"
                else:
                    varname = f"{base}{idx}"
                # Override RH1
                if base == 'RH' and stn == 'Vadinar':
                    val = 50.0
                else:
                    vobj = ns.get(varname, None)
                    if vobj is None:
                        vobj = getattr(model, varname, None)
                    try:
                        val = float(pyo.value(vobj))
                    except:
                        val = None
            # Formatting
            if base == 'NOP' and val is not None:
                data[param].append(int(val))
            elif base == 'EFFP' and val is not None:
                data[param].append(f"{val*100:.2f}%")
            elif val is not None:
                data[param].append(round(val, 2))
            else:
                data[param].append(None)

    df = pd.DataFrame(data, index=list(stations.keys())).T
    st.subheader("Station-wise Parameter Summary")
    st.table(df)
    footer()
else:(data, index=list(stations.keys())).T
    st.subheader("Station-wise Parameter Summary")
    st.table(df)
    footer()
else:
    st.markdown("Enter pipeline inputs and click **Run Optimization** to view results.")
    footer()
