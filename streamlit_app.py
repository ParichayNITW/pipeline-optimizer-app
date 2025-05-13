import os, re
import streamlit as st
import pyomo.environ as pyo
from pyomo.opt import SolverManagerFactory
import pandas as pd

# Page configuration
st.set_page_config(page_title="Pipeline Optimization App", layout="wide")

# NEOS email configuration
os.environ['NEOS_EMAIL'] = 'parichay.nitwarangal@gmail.com'

# Mapping station indices to names
STATION_NAMES = {
    '1': 'Vadinar',
    '2': 'Jamnagar',
    '3': 'Rajkot',
    '4': 'Chotila',
    '5': 'Surendranagar',
    '6': 'Viramgam'
}

# Human-readable labels for parameter prefixes
PARAM_LABELS = {
    'NOP': 'Number of Pumps',
    'DR': 'Drag Reduction (%)',
    'N': 'Pump Speed (RPM)',
    'MAOP': 'Maximum Operating Allowable Pressure (bar)',
    'RH': 'Head (m)',
    'Re': 'Reynolds Number',
    'f': 'Friction Factor',
    'DH': 'Darcy-Weisbach Head Loss (m)',
    'SH': 'Static Head (m)',
    'SDHR': 'Segment Total Head Requirement (m)',
    'TDHA_PUMP': 'Pump Power (kW)',
    'SDHA': 'Available Pump Head (m)',
    'EFFP': 'Pump Efficiency (%)',
    'EFFM': 'Mechanical Efficiency (%)',
    'PPM': 'Pump Power Margin (%)',
    'v': 'Velocity (m/s)',
    'FLOW_EQUIV': 'Equivalent Flow Value',
    'OF_POWER': 'Power Cost (₹)',
    'OF_DRA': 'DRA Cost (₹)',
    'FLOW': 'Flow Rate (KL/Hr)'
}

# Core solve function

def solve_pipeline(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD):
    # Load and sanitize the original script
    with open('opt.txt') as f:
        code = f.read()
    lines = code.splitlines()
    lines = [l for l in lines if not l.strip().startswith('!pip')]
    code = '\n'.join(lines)
    code = re.sub(r'.*input\(.*', '', code)
    code = re.sub(r'print\(.*', '', code)

    # Prepare namespace
    local = {
        'os': os,
        'pyo': pyo,
        'SolverManagerFactory': SolverManagerFactory,
        'FLOW': FLOW,
        'KV': KV,
        'rho': rho,
        'SFC_J': SFC_J,
        'SFC_R': SFC_R,
        'SFC_S': SFC_S,
        'RateDRA': RateDRA,
        'Price_HSD': Price_HSD
    }
    # Execute
    exec(code, local)
    model = local['model']

    # Solve remotely
    solver = SolverManagerFactory('neos')
    solver.solve(model, opt='bonmin', tee=False)

    outputs = {}
    # Capture model objectives, vars, expressions
    for comp in model.component_objects(pyo.Component, active=True):
        for obj in getattr(model, comp.name).components() if hasattr(model, comp.name) else []:
            pass
    # Objectives
    for obj in model.component_objects(pyo.Objective, active=True):
        outputs[obj.name] = pyo.value(obj)
    # Variables
    for var in model.component_data_objects(pyo.Var, active=True, descend_into=True):
        outputs[var.name] = pyo.value(var)
    # Expressions
    for expr in model.component_data_objects(pyo.Expression, active=True, descend_into=True):
        outputs[expr.name] = pyo.value(expr)
    
    # Capture any local Python variables (v1, Re1, etc.)
    exclude = set(local.keys()) & set(['os','pyo','SolverManagerFactory','model'])
    input_keys = {'FLOW','KV','rho','SFC_J','SFC_R','SFC_S','RateDRA','Price_HSD'}
    for k, v in local.items():
        if k in exclude or k in input_keys or k.startswith('__'):
            continue
        # Skip components already captured
        if k in outputs:
            continue
        # Attempt to fetch numeric value
        try:
            val = pyo.value(v)
        except:
            # fallback for pure Python numbers
            if isinstance(v, (int, float)):
                val = v
            else:
                continue
        outputs[k] = val
    return outputs

# Sidebar inputs
st.sidebar.header("Input Parameters")
FLOW      = st.sidebar.number_input("Flow rate (KL/Hr)", min_value=0.0, value=1000.0)
KV        = st.sidebar.number_input("Kinematic Viscosity (cSt)", min_value=0.0, value=10.0)
rho       = st.sidebar.number_input("Density (kg/m3)", min_value=0.0, value=850.0)
SFC_J     = st.sidebar.number_input("SFC at Jamnagar (gm/bhp/hr)", min_value=0.0, value=200.0)
SFC_R     = st.sidebar.number_input("SFC at Rajkot (gm/bhp/hr)", min_value=0.0, value=200.0)
SFC_S     = st.sidebar.number_input("SFC at Surendranagar (gm/bhp/hr)", min_value=0.0, value=200.0)
RateDRA   = st.sidebar.number_input("DRA Rate (Rs/L)", min_value=0.0, value=9.0)
Price_HSD = st.sidebar.number_input("HSD Price (Rs/L)", min_value=0.0, value=80.0)

# Run optimization
if st.sidebar.button("Run Optimization"):
    with st.spinner("Optimizing via NEOS..."):
        outputs = solve_pipeline(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD)
    st.success("Optimization Complete!")

    # Build table rows
    rows = []
    for key, val in outputs.items():
        # try station-specific
        m = re.match(r"^([A-Za-z_]+?)(\d+)", key)
        if m:
            prefix = m.group(1).rstrip('_')
            idx = m.group(2)
            station = STATION_NAMES.get(idx, f"Station {idx}")
            label = PARAM_LABELS.get(prefix, prefix.replace('_',' '))
        else:
            station = 'Overall'
            label = PARAM_LABELS.get(key, key.replace('_',' '))
        rows.append({"Station": station, "Parameter": label, "Value": val})

    df = pd.DataFrame(rows)
    df = df.sort_values(by=["Station","Parameter"]).reset_index(drop=True)

    st.subheader("Detailed Results by Station and Parameter")
    st.dataframe(df, use_container_width=True)

else:
    st.title("Pipeline Optimization App")
    st.markdown(
        "Enter the required inputs in the sidebar, then click **Run Optimization**.\n"
        "All intermediate and final parameters (velocity, Reynolds number, friction factor, static and dynamic heads, pump power, costs, efficiencies, etc.) will be shown for each station."
    )
