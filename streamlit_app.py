import os
import re
import streamlit as st
import pyomo.environ as pyo
from pyomo.opt import SolverManagerFactory

# Set NEOS email for remote solves
os.environ['NEOS_EMAIL'] = 'parichay.nitwarangal@gmail.com'

# Core function: dynamically load and run the opt.txt model

def solve_pipeline(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD):
    # Read the original Pyomo script
    with open('opt.txt') as f:
        code = f.read()
    # Remove any pip install directives
    code = '\n'.join([l for l in code.splitlines() if not l.strip().startswith('!pip')])
    # Strip out input() calls (we'll supply those via function args)
    code = re.sub(r'.*input\(.*', '', code)
    # Remove print statements (we'll capture results programmatically)
    code = re.sub(r'print\(.*', '', code)

    # Prepare namespace for exec
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

    # Execute the script: defines `model`, all Params, Vars, Constraints, and Objective
    exec(code, local)
    model = local['model']

    # Solve via NEOS Bonmin
    solver = SolverManagerFactory('neos')
    results = solver.solve(model, opt='bonmin', tee=False)

    # Collect outputs
    outputs = {}
    outputs['Total Cost'] = pyo.value(model.Objf)
    # Pumps and heads for each segment
    keys = ['NOP1','DR1','N1','RH2', 'NOP2','DR2','N2','RH3',
            'NOP3','DR3','N3','RH4', 'RH5','NOP5','DR4','N5','RH6']
    for k in keys:
        if hasattr(model, k):
            outputs[k] = pyo.value(getattr(model, k))
    return outputs

# Streamlit UI
st.title("Pipeline Optimization via Pyomo + NEOS")
st.markdown("Provide the eight key inputs below and click Optimize.")

FLOW = st.number_input("Flow rate (KL/Hr)", value=1000.0)
KV = st.number_input("Kinematic Viscosity (cSt)", value=10.0)
rho = st.number_input("Density (kg/m3)", value=850.0)
SFC_J = st.number_input("SFC at Jamnagar (gm/bhp/hr)", value=200.0)
SFC_R = st.number_input("SFC at Rajkot (gm/bhp/hr)", value=200.0)
SFC_S = st.number_input("SFC at Surendranagar (gm/bhp/hr)", value=200.0)
RateDRA = st.number_input("DRA Rate (Rs/L)", value=9.0)
Price_HSD = st.number_input("HSD Price (Rs/L)", value=80.0)

if st.button("Optimize"):
    with st.spinner("Running optimization on NEOS..."):
        results = solve_pipeline(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD)
    st.success("Optimization complete!")
    st.json(results)
