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

# Display header with logos and title
col1, col2, col3 = st.columns([1,6,1])
with col1:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Indian_Oil_Corporation_Logo.svg/320px-Indian_Oil_Corporation_Logo.svg.png", width=80)
with col2:
    st.markdown("# Mixed Integer Non-Linear Convex Optimisation of Pipeline Operations")
with col3:
    st.image("https://images.unsplash.com/photo-1590487988183-7fd160517c9d?auto=format&fit=crop&w=200&q=60", width=80)

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
ios_email = 'parichay.nitwarangal@gmail.com'
os.environ['NEOS_EMAIL'] = ios_email

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

# Main app logic
if st.sidebar.button("Run Optimization"):
    with st.spinner("Optimizing via NEOS... please wait"):
        model, ns = solve_model(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD)
    st.success("Optimization Complete!")

    # Display Total Operating Cost (large, bold)
    total_cost = pyo.value(model.Objf)
    st.markdown(
        f"<h1 style='text-align:center; font-weight:bold;'>"
        f"Total Operating Cost: ₹{total_cost:,.2f}"
        f"</h1>", unsafe_allow_html=True
    )

    # Station definitions with drag indices
    stations_info = OrderedDict([
        ('Vadinar',       {'idx':'1','dr_idx':'1'}),
        ('Jamnagar',      {'idx':'2','dr_idx':'2'}),
        ('Rajkot',        {'idx':'3','dr_idx':'3'}),
        ('Chotila',       {'idx':'4','dr_idx':None}),
        ('Surendranagar', {'idx':'5','dr_idx':'4'}),
        ('Viramgam',      {'idx':'6','dr_idx':None}),
    ])

    # Parameters mapping: label -> (base var name, index key)
    params = OrderedDict([
        ('No. of Pumps',                 ('NOP',        'idx')),
        ('Drag Reduction (%)',           ('DR',         'dr_idx')),
        ('Maximum Allowable Operating Pressure (bar)', ('MAOP', 'idx')),
        ('Velocity (m/s)',               ('v',          'idx')),
        ('Reynolds Number',              ('Re',         'idx')),
        ('Friction Factor',              ('f',          'idx')),
        ('Dynamic Head Loss (m)',        ('DH',         'idx')),
        ('Head developed by each Pump (m)', ('TDHA_PUMP','idx')),
        ('Pump Speed (RPM)',             ('N',          'idx')),
        ('Pump Efficiency (%)',          ('EFFP',       'idx')),
        ('Station Discharge Head (m)',   ('SDHA',       'idx')),
        ('Residual Head (m)',            ('RH',         'idx')),
        ('Power Cost (₹)',               ('OF_POWER',   'idx')),
        ('DRA Cost (₹)',                 ('OF_DRA',     'idx')),
    ])

    # Identify parameter positions
    keys = list(params.keys())
    p_idx = keys.index('No. of Pumps')
    s_idx = keys.index('Pump Speed (RPM)')
    e_idx = keys.index('Pump Efficiency (%)')
    rh_idx = keys.index('Residual Head (m)')

    # Build transposed result data
    result_data = OrderedDict()
    for station, info in stations_info.items():
        row = []
        for label, (base, keyfld) in params.items():
            suffix = info.get(keyfld)
            if suffix is None:
                row.append(None)
                continue
            varname = f"{base}{suffix}"
            v_obj = ns.get(varname) if varname in ns else getattr(model, varname, None)
            try:
                num = float(pyo.value(v_obj))
            except:
                num = float(v_obj) if isinstance(v_obj, (int, float)) else None
            # Formatting
            if label == 'No. of Pumps' and num is not None:
                num = int(num)
            elif num is not None:
                num = round(num, 2)
            row.append(num)
        # Override RH for Vadinar
        if station == 'Vadinar':
            row[rh_idx] = 50.00
        # For Chotila and Viramgam only show RH
        if station in ['Chotila', 'Viramgam']:
            rh_val = row[rh_idx]
            row = [None]*len(keys)
            row[rh_idx] = rh_val
        # Override speed & efficiency when pumps == 0
        if station not in ['Chotila', 'Viramgam'] and row[p_idx] == 0:
            row[s_idx] = 0.00
            row[e_idx] = '0.00%'
        # Convert efficiency fraction to percent
        if station not in ['Chotila', 'Viramgam'] and row[p_idx] != 0:
            eff_frac = row[e_idx]
            row[e_idx] = f"{eff_frac*100:.2f}%" if eff_frac is not None else None
        result_data[station] = row

    # Build DataFrame and display
    df = pd.DataFrame(result_data, index=keys)
    st.subheader("Station-wise Parameter Summary")
    st.table(df)
    footer()
else:
    st.markdown("Enter your pipeline inputs in the sidebar and click **Run Optimization** to view results.")
    footer()
