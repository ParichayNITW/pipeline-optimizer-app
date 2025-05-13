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

# Load and clean the Pyomo script once
def _load_model_script():
    with open('opt.txt') as f:
        raw = f.read()
    lines = [l for l in raw.splitlines() if not l.strip().startswith('!pip')]
    code = "\n".join(lines)
    code = re.sub(r'.*input\(.*', '', code)
    code = re.sub(r'print\(.*', '', code)
    return code

SCRIPT = _load_model_script()

# Cached solver to speed up repeated runs
@st.cache_data(show_spinner=False)
def solve_pipeline_cached(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD):
    local = dict(
        os=os,
        pyo=pyo,
        SolverManagerFactory=SolverManagerFactory,
        FLOW=FLOW, KV=KV, rho=rho,
        SFC_J=SFC_J, SFC_R=SFC_R, SFC_S=SFC_S,
        RateDRA=RateDRA, Price_HSD=Price_HSD
    )
    exec(SCRIPT, local)
    model = local['model']
    solver = SolverManagerFactory('neos')
    solver.solve(model, opt='bonmin', tee=False)
    return model, local

# Sidebar: input parameters
st.sidebar.header("🌊 Pipeline Inputs")
FLOW      = st.sidebar.number_input("Flow rate (KL/Hr)",    min_value=0.0, value=1000.0)
KV        = st.sidebar.number_input("Kinematic Viscosity (cSt)", min_value=0.0, value=10.0)
rho       = st.sidebar.number_input("Density (kg/m3)",     min_value=0.0, value=850.0)
SFC_J     = st.sidebar.number_input("SFC at Jamnagar (gm/bhp/hr)", min_value=0.0, value=200.0)
SFC_R     = st.sidebar.number_input("SFC at Rajkot (gm/bhp/hr)",  min_value=0.0, value=200.0)
SFC_S     = st.sidebar.number_input("SFC at Surendranagar (gm/bhp/hr)", min_value=0.0, value=200.0)
RateDRA   = st.sidebar.number_input("DRA Rate (Rs/L)",      min_value=0.0, value=9.0)
Price_HSD = st.sidebar.number_input("HSD Price (Rs/L)",     min_value=0.0, value=80.0)

if st.sidebar.button("🚀 Run Optimization"):
    with st.spinner("Optimizing via NEOS... please wait 🤖"):
        model, local = solve_pipeline_cached(
            FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD
        )
    st.success("✅ Optimization Complete!")

    # Define station metadata
    stations = [
        {"name":"Vadinar","idx":"1","dr":"1","power":"1","dra":"1","effp":"1"},
        {"name":"Jamnagar","idx":"2","dr":"2","power":"2","dra":"2","effp":"2"},
        {"name":"Rajkot","idx":"3","dr":"3","power":"3","dra":"3","effp":"3"},
        {"name":"Chotila","idx":"4","dr":None,"power":None,"dra":None,"effp":None},
        {"name":"Surendranagar","idx":"5","dr":"4","power":"4","dra":"4","effp":"5"},
        {"name":"Viramgam","idx":"6","dr":None,"power":None,"dra":None,"effp":None},
    ]

    # Helper to extract values
    def val(key):
        v = local.get(key)
        if hasattr(v, 'is_expression') or hasattr(v, 'is_variable'):
            return pyo.value(v)
        elif isinstance(v, (int, float)):
            return v
        return None

    # Build results DataFrame
    rows = []
    for s in stations:
        row = {"Station": s["name"]}
        i = s["idx"]
        row["No. of Pumps"] = val(f"NOP{i}")
        row["Drag Reduction (%)"] = val(f"DR{s['dr']}" ) if s['dr'] else None
        row["Pump Speed (RPM)"] = val(f"N{i}")
        row["Residual Head (m)"] = val(f"RH{i}")
        row["Station Discharge Head (m)"] = val(f"SDHA_{i}")
        row["Pump Efficiency (%)"] = val(f"EFFP{s['effp']}" ) if s['effp'] else None
        row["Power Cost (₹)"] = val(f"OF_POWER_{s['power']}") if s['power'] else None
        row["DRA Cost (₹)"] = val(f"OF_DRA_{s['dra']}") if s['dra'] else None
        rows.append(row)
    df = pd.DataFrame(rows).set_index('Station')

    # Display metrics row
    total_cost = pyo.value(model.Objf)
    st.markdown("### Summary Metrics")
    cols = st.columns(4)
    cols[0].metric("💰 Total Operating Cost (₹)", f"{total_cost:,.2f}")
    cols[1].metric("⚙️ Total Pumps", int(df['No. of Pumps'].sum()))
    avg_eff = df['Pump Efficiency (%)'].dropna().mean()
    cols[2].metric("⚙️ Avg Pump Efficiency (%)", f"{avg_eff:.2f}")
    cols[3].metric("🔥 Avg DRA Dosage (%)", f"{df['Drag Reduction (%)'].dropna().mean():.2f}")

    # Display table with formatting
    st.markdown("---")
    st.subheader("Station-wise Results")
    fmt = {col:"{:.2f}" for col in df.columns if df[col].dtype != object}
    st.dataframe(df.style.format(fmt).highlight_max(axis=0), use_container_width=True)

    # Visualizations
    st.markdown("---")
    st.subheader("Performance Charts")
    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.markdown("#### Pumps per Station")
        st.bar_chart(df['No. of Pumps'])
    with chart_cols[1]:
        st.markdown("#### Pump Speed (RPM)")
        st.line_chart(df['Pump Speed (RPM)'])

    cost_cols = st.columns(2)
    with cost_cols[0]:
        st.markdown("#### Power Cost by Station")
        st.bar_chart(df['Power Cost (₹)'])
    with cost_cols[1]:
        st.markdown("#### DRA Cost by Station")
        st.bar_chart(df['DRA Cost (₹)'])

else:
    st.title("Pipeline Optimization App")
    st.markdown(
        "Use the sidebar to enter pipeline inputs, then click **Run Optimization**.\n"
        "See summary metrics, detailed table, and performance charts."
    )
