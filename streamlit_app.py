import os, re
import streamlit as st
import pyomo.environ as pyo
from pyomo.opt import SolverManagerFactory
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Pipeline Optimization App",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure NEOS email
os.environ['NEOS_EMAIL'] = 'parichay.nitwarangal@gmail.com'

# Load and clean the Pyomo model script once
def load_script():
    with open('opt.txt') as f:
        raw = f.read()
    lines = [l for l in raw.splitlines() if not l.strip().startswith('!pip')]
    code = "\n".join(lines)
    code = re.sub(r'.*input\(.*', '', code)
    code = re.sub(r'print\(.*', '', code)
    return code

SCRIPT = load_script()

# Run optimization and extract variables
def run_optimization(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD):
    # Prepare namespace and define model
    local = dict(
        os=os, pyo=pyo, SolverManagerFactory=SolverManagerFactory,
        FLOW=FLOW, KV=KV, rho=rho,
        SFC_J=SFC_J, SFC_R=SFC_R, SFC_S=SFC_S,
        RateDRA=RateDRA, Price_HSD=Price_HSD
    )
    exec(SCRIPT, local)
    model = local['model']
    # Solve on NEOS
    solver = SolverManagerFactory('neos')
    solver.solve(model, opt='bonmin', tee=False)

    # Helper to get numeric values
    def val(key):
        v = local.get(key) if key in local else getattr(model, key, None)
        try:
            return float(pyo.value(v))
        except:
            return float(v) if isinstance(v, (int, float)) else None

    # Define mapping for each station
    mapping = [
        {'Station': 'Vadinar',       'NOP': 'NOP1', 'DR': 'DR1', 'Speed': 'N1', 'Residual Head': 'RH2', 'Discharge Head': 'SDHA_1', 'Efficiency': 'EFFP1', 'Power Cost': 'OF_POWER_1', 'DRA Cost': 'OF_DRA_1'},
        {'Station': 'Jamnagar',      'NOP': 'NOP2', 'DR': 'DR2', 'Speed': 'N2', 'Residual Head': 'RH3', 'Discharge Head': 'SDHA_2', 'Efficiency': 'EFFP2', 'Power Cost': 'OF_POWER_2', 'DRA Cost': 'OF_DRA_2'},
        {'Station': 'Rajkot',        'NOP': 'NOP3', 'DR': 'DR3', 'Speed': 'N3', 'Residual Head': 'RH4', 'Discharge Head': 'SDHA_3', 'Efficiency': 'EFFP3', 'Power Cost': 'OF_POWER_3', 'DRA Cost': 'OF_DRA_3'},
        {'Station': 'Surendranagar', 'NOP': 'NOP5', 'DR': 'DR5', 'Speed': 'N5', 'Residual Head': 'RH6', 'Discharge Head': 'SDHA_4', 'Efficiency': 'EFFP5', 'Power Cost': 'OF_POWER_4', 'DRA Cost': 'OF_DRA_4'}
    ]

    # Build results rows with zero overrides
    rows = []
    for m in mapping:
        nop_val = val(m['NOP']) or 0
        row = {
            'Station': m['Station'],
            'No. of Pumps': nop_val,
            'Drag Reduction (%)': val(m['DR']),
            'Residual Head (m)': val(m['Residual Head']),
            'Station Discharge Head (m)': val(m['Discharge Head']),
            'Power Cost (₹)': val(m['Power Cost']),
            'DRA Cost (₹)': val(m['DRA Cost'])
        }
        # Speed and efficiency
        if nop_val == 0:
            speed_val = 0.0
            eff_val = 0.0
        else:
            speed_val = val(m['Speed'])
            eff_val = val(m['Efficiency'])
        row['Pump Speed (RPM)'] = speed_val
        row['Pump Efficiency Fraction'] = eff_val
        rows.append(row)

    # Total operating cost
    total_cost = float(pyo.value(model.Objf))
    return rows, total_cost

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

# Main app
def main():
    if st.sidebar.button("Run Optimization"):
        with st.spinner("Running optimization on NEOS..."):
            rows, total_cost = run_optimization(
                FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD
            )
        st.success("Optimization Complete!")

        # Bold total cost heading
        st.markdown(f"**Total Operating Cost: ₹{total_cost:,.2f}**")

        # Prepare DataFrame
        df = pd.DataFrame(rows).set_index('Station')
        # Format numeric columns
        df['No. of Pumps'] = df['No. of Pumps'].astype(int)
        df[['Pump Speed (RPM)', 'Residual Head (m)', 'Station Discharge Head (m)', 'Power Cost (₹)', 'DRA Cost (₹)']] = \
            df[['Pump Speed (RPM)', 'Residual Head (m)', 'Station Discharge Head (m)', 'Power Cost (₹)', 'DRA Cost (₹)']].round(2)
        # Convert efficiency fraction to percentage and drop fraction
        df['Pump Efficiency (%)'] = df['Pump Efficiency Fraction'].apply(lambda x: f"{x*100:.2f}%")
        df.drop(columns=['Pump Efficiency Fraction'], inplace=True)

        # Display station-wise table
        st.subheader("**Station-wise Results**")
        st.table(df)
    else:
        st.title("Pipeline Optimization App")
        st.markdown(
            "Enter inputs in the sidebar and click **Run Optimization** to see station-wise pump counts, speeds, heads, efficiencies, and costs."
        )

if __name__ == '__main__':
    main()
