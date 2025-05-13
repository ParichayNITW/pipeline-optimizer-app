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
# Header with logos and title
col1, col2, col3 = st.columns([1,6,1])
with col1:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Indian_Oil_Corporation_Logo.svg/120px-Indian_Oil_Corporation_Logo.svg.png", width=60)
with col2:
    st.markdown("# Mixed Integer Non-Linear Convex Optimisation of Pipeline Operations")
with col3:
    st.image("https://images.unsplash.com/photo-1590487988183-7fd160517c9d?auto=format&fit=crop&w=120&q=60", width=60)

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

# Load and sanitize Pyomo model script (cached)
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

# Solve model and return model + namespace
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

# Main logic
if st.sidebar.button("Run Optimization"):
    with st.spinner("Optimizing via NEOS... please wait"):
        model, ns = solve_model(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD)
    st.success("Optimization Complete!")

    # Display total cost
    total_cost = pyo.value(model.Objf)
    st.markdown(
        f"<h1 style='text-align:center; font-weight:bold;'>Total Operating Cost: ₹{total_cost:,.2f}</h1>",
        unsafe_allow_html=True
    )

    # Stations and parameters
    stations_info = OrderedDict([
        ('Vadinar',       {'idx':'1','dr_idx':'1'}),
        ('Jamnagar',      {'idx':'2','dr_idx':'2'}),
        ('Rajkot',        {'idx':'3','dr_idx':'3'}),
        ('Chotila',       {'idx':'4','dr_idx':None}),
        ('Surendranagar', {'idx':'5','dr_idx':'4'}),
        ('Viramgam',      {'idx':'6','dr_idx':None}),
    ])
    params = OrderedDict([
        ('No. of Pumps', ('NOP','idx')),
        ('Drag Reduction (%)', ('DR','dr_idx')),
        ('Maximum Allowable Operating Pressure (bar)', ('MAOP','idx')),
        ('Velocity (m/s)', ('v','idx')),
        ('Reynolds Number', ('Re','idx')),
        ('Friction Factor', ('f','idx')),
        ('Dynamic Head Loss (m)', ('DH','idx')),
        ('Head developed by each Pump (m)', ('TDHA_PUMP','idx')),
        ('Pump Speed (RPM)', ('N','idx')),
        ('Pump Efficiency (%)', ('EFFP','idx')),
        ('Station Discharge Head (m)', ('SDHA','idx')),
        ('Residual Head (m)', ('RH','idx')),
        ('Power Cost (₹)', ('OF_POWER','idx')),
        ('DRA Cost (₹)', ('OF_DRA','idx')),
    ])
    keys = list(params.keys())
    p_idx = keys.index('No. of Pumps')
    s_idx = keys.index('Pump Speed (RPM)')
    e_idx = keys.index('Pump Efficiency (%)')
    rh_idx = keys.index('Residual Head (m)')

    # Build table data
    result_data = OrderedDict()
    for station, info in stations_info.items():
        row = []
        for label, (base, fld) in params.items():
            idx = info.get(fld)
            if idx is None:
                row.append(None)
                continue
            # choose delimiter
            delim = '_' if base in ['MAOP','DH','TDHA_PUMP','SDHA','OF_POWER','OF_DRA','RH'] else ''
            varname = f"{base}{delim}{idx}" if delim=='' else f"{base}{delim}{idx}"
            v = ns.get(varname) if varname in ns else getattr(model, varname, None)
            try:
                val = float(pyo.value(v))
            except:
                val = float(v) if isinstance(v,(int,float)) else None
            if label=='No. of Pumps' and val is not None:
                val = int(val)
            elif val is not None:
                val = round(val,2)
            row.append(val)
        # override RH1
        if station=='Vadinar': row[rh_idx]=50.00
        # Chotila & Viramgam only RH
        if station in ['Chotila','Viramgam']:
            rh = row[rh_idx]
            row = [None]*len(keys)
            row[rh_idx]=rh
        # speed/eff zero when no pumps
        if station not in ['Chotila','Viramgam'] and row[p_idx]==0:
            row[s_idx]=0.00; row[e_idx]='0.00%'
        # efficiency percent
        if station not in ['Chotila','Viramgam'] and row[p_idx]>0:
            frac=row[e_idx]; row[e_idx]=f"{frac*100:.2f}%" if frac is not None else None
        result_data[station]=row

        # Display attractive styled table
    st.subheader("Station-wise Parameter Summary")
    # Style DataFrame: conditional formatting and gradient
    styled = df.style \
        .format(precision=2) \
        .applymap(lambda v: "font-weight: bold;" if isinstance(v, int) else "", subset=["No. of Pumps"]) \
        .background_gradient(subset=df.columns.drop("No. of Pumps"), cmap="Blues", axis=0) \
        .highlight_max(color="lightgreen", axis=1)
    st.dataframe(styled, use_container_width=True)
    footer()
else:
    st.markdown("Enter your pipeline inputs in the sidebar and click **Run Optimization** to view results.")
    footer()
