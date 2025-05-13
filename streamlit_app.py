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

# NEOS configuration
ios_email = 'parichay.nitwarangal@gmail.com'
os.environ['NEOS_EMAIL'] = ios_email

# Load and clean Pyomo script
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

# Solve model and return namespace
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

if st.sidebar.button("Run Optimization"):
    with st.spinner("Optimizing via NEOS... please wait"):
        model, ns = solve_model()
    st.success("Optimization Complete!")

    # Total operating cost
    total = pyo.value(model.Objf)
    st.markdown(
        f"<h1 style='text-align:center; font-weight:bold;'>"
        f"Total Operating Cost: ₹{total:,.2f}"
        f"</h1>", unsafe_allow_html=True
    )

    # Station identifiers
    stations = OrderedDict([
        ('Vadinar','1'), ('Jamnagar','2'), ('Rajkot','3'),
        ('Chotila','4'), ('Surendranagar','5'), ('Viramgam','6')
    ])
    # Parameters to include
    desired = OrderedDict([
        ('No. of Pumps','NOP'),
        ('Drag Reduction (%)','DR'),
        ('Pump Speed (RPM)','N'),
        ('Pump Efficiency (%)','EFFP'),
        ('Station Discharge Head (m)','SDHA'),
        ('Residual Head (m)','RH'),
        ('Power Cost (₹)','OF_POWER'),
        ('DRA Cost (₹)','OF_DRA')
    ])

    # Build results
    rows = []
    for label, base in desired.items():
        row = {'Parameter': label}
        for stn, idx in stations.items():
            # skip invalid drag
            if base=='DR' and stn not in ['Vadinar','Jamnagar','Rajkot','Surendranagar']:
                val = None
            else:
                # handle var naming
                if base in ['SDHA','OF_POWER','OF_DRA','RH']:
                    varname = f"{base}_{idx}"
                else:
                    varname = f"{base}{idx}"
                # override RH1
                if base=='RH' and stn=='Vadinar':
                    val = 50.0
                else:
                    obj = ns.get(varname) if varname in ns else getattr(model, varname, None)
                    try:
                        val = float(pyo.value(obj))
                    except:
                        val = None
            # format
            if label=='No. of Pumps' and val is not None:
                val = int(val)
            elif label=='Pump Efficiency (%)' and val is not None:
                val = f"{val*100:.2f}%"
            elif val is not None:
                val = round(val,2)
            row[stn] = val
        rows.append(row)

    df = pd.DataFrame(rows).set_index('Parameter')
    st.subheader("Station-wise Parameter Summary")
    st.table(df)
    footer()
else:
    st.markdown("Enter pipeline inputs and click **Run Optimization** to view results.")
    footer()
