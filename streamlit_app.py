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

# Set NEOS email for remote solves
os.environ['NEOS_EMAIL'] = 'parichay.nitwarangal@gmail.com'

# Load and clean Pyomo script (no caching to avoid micropip issues)
def load_script():
    with open('opt.txt') as f:
        lines = [l for l in f if not l.strip().startswith(('!pip','print','input'))]
    return ''.join(lines)

SCRIPT = load_script()

# Solve model and return Pyomo model
def solve_model():
    # Prepare namespace for exec
    ns = dict(
        os=os, pyo=pyo, SolverManagerFactory=SolverManagerFactory,
        FLOW=FLOW, KV=KV, rho=rho,
        SFC_J=SFC_J, SFC_R=SFC_R, SFC_S=SFC_S,
        RateDRA=RateDRA, Price_HSD=Price_HSD
    )
    exec(SCRIPT, ns)
    model = ns['model']
    # Solve remotely via NEOS
    SolverManagerFactory('neos').solve(model, opt='bonmin', tee=False)
    return model

# Run optimization and display results
def main():
    if st.sidebar.button("Run Optimization"):
        model = solve_model()
        # Total Operating Cost
        total = pyo.value(model.Objf)
        st.markdown(
            f"<h1 style='text-align:center; font-weight:bold;'>"
            f"Total Operating Cost: ₹{total:,.2f}"
            f"</h1>", unsafe_allow_html=True
        )

        # Station codes
        stations = OrderedDict([
            ('Vadinar','1'), ('Jamnagar','2'), ('Rajkot','3'),
            ('Chotila','4'), ('Surendranagar','5'), ('Viramgam','6')
        ])
        # Desired outputs
        params = OrderedDict([
            ('No. of Pumps','NOP'),
            ('Drag Reduction (%)','DR'),
            ('Pump Speed (RPM)','N'),
            ('Pump Efficiency (%)','EFFP'),
            ('Station Discharge Head (m)','SDHA'),
            ('Residual Head (m)','RH'),
            ('Power Cost (₹)','OF_POWER'),
            ('DRA Cost (₹)','OF_DRA')
        ])
        # Build results table
        data = {}
        for label, base in params.items():
            row = []
            for stn, idx in stations.items():
                # Chotila & Viramgam: only RH
                if stn in ['Chotila','Viramgam'] and base != 'RH':
                    val = 0.0
                else:
                    # Construct var name
                    varname = f"{base}_{idx}" if base in ['SDHA','OF_POWER','OF_DRA','RH'] else f"{base}{idx}"
                    # Override RH1
                    if base == 'RH' and stn == 'Vadinar':
                        val = 50.0
                    else:
                        comp = getattr(model, varname, None)
                        val = pyo.value(comp) if comp is not None else None
                # Formatting
                if base == 'NOP':
                    row.append(int(val) if val is not None else None)
                elif base == 'EFFP':
                    row.append(f"{val*100:.2f}%" if val is not None else None)
                else:
                    row.append(round(val,2) if val is not None else None)
            data[label] = row
        df = pd.DataFrame(data, index=list(stations.keys())).T
        st.subheader("Station-wise Parameter Summary")
        st.table(df)
        footer()
    else:
        st.markdown("Enter inputs and click **Run Optimization** to view results.")
        footer()

if __name__ == '__main__':
    main()
