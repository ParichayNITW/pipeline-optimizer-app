import os, re
import streamlit as st
import pyomo.environ as pyo
from pyomo.opt import SolverManagerFactory
import pandas as pd

# Page configuration
st.set_page_config(page_title="Pipeline Optimization App", layout="wide")

# Configure NEOS email for remote solves
os.environ['NEOS_EMAIL'] = 'parichay.nitwarangal@gmail.com'

# Function to execute the original opt.txt model and return all model outputs
def solve_pipeline(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD):
    # Load and clean the Pyomo script
    with open('opt.txt') as f:
        code = f.read()
    # Remove pip installs, input() calls, prints
    code = '\n'.join([l for l in code.splitlines() if not l.strip().startswith('!pip')])
    code = re.sub(r'.*input\(.*', '', code)
    code = re.sub(r'print\(.*', '', code)

    # Prepare namespace with user parameters
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

    # Execute the model script (defines `model`)
    exec(code, local)
    model = local['model']

    # Solve via NEOS Bonmin
    solver = SolverManagerFactory('neos')
    solver.solve(model, opt='bonmin', tee=False)

    # Collect all outputs: objectives, variables, expressions
    outputs = {}
    # Objective(s)
    for obj in model.component_objects(pyo.Objective, active=True):
        outputs[obj.name] = pyo.value(obj)
    # Variables
    for var in model.component_data_objects(pyo.Var, active=True, descend_into=True):
        outputs[var.name] = pyo.value(var)
    # Expressions
    for expr in model.component_data_objects(pyo.Expression, active=True, descend_into=True):
        outputs[expr.name] = pyo.value(expr)
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

    # Display Total Cost prominently
    if 'Objf' in outputs:
        st.metric("Objective (Total Cost, ₹)", f"{outputs['Objf']:,.2f}")
    else:
        # If custom name used
        total = outputs.get('model.Objf', None)
        if total is not None:
            st.metric("Total Cost (₹)", f"{total:,.2f}")

    # Create a DataFrame of all outputs
    df = pd.DataFrame(
        list(outputs.items()),
        columns=["Variable/Output", "Value"]
    )
    # Sort by variable name
    df = df.sort_values(by="Variable/Output").reset_index(drop=True)

    st.subheader("All Calculated Outputs")
    st.dataframe(df, use_container_width=True)

else:
    st.title("Pipeline Optimization App")
    st.markdown(
        "Use the sidebar to enter inputs, then click **Run Optimization**.\n"
        "All computed variables (pump counts, speeds, heads, losses, power, DRA dosages, etc.) will be displayed in a table."
    )
