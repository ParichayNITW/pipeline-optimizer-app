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
def load_script():
    with open('opt.txt') as f:
        raw = f.read()
    lines = [l for l in raw.splitlines() if not l.strip().startswith('!pip')]
    code = "\n".join(lines)
    code = re.sub(r'.*input\(.*', '', code)
    code = re.sub(r'print\(.*', '', code)
    return code

SCRIPT = st.cache_resource(load_script)()

# Cached data function: returns only serializable results
@st.cache_data(show_spinner=False)
def get_results(FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD, solver_choice):
    # Prepare namespace
    local = dict(
        os=os,
        pyo=pyo,
        SolverManagerFactory=SolverManagerFactory,
        FLOW=FLOW, KV=KV, rho=rho,
        SFC_J=SFC_J, SFC_R=SFC_R, SFC_S=SFC_S,
        RateDRA=RateDRA, Price_HSD=Price_HSD
    )
    # Execute model script
    exec(SCRIPT, local)
    model = local['model']
    # Solver choice
    if solver_choice.startswith("Local"):
        try:
            solver = pyo.SolverFactory('bonmin')
        except Exception:
            solver = SolverManagerFactory('neos')
    else:
        solver = SolverManagerFactory('neos')
    # Solve
    solver.solve(model, opt='bonmin', tee=False)
    # Stations definition
    stations = [
        {"name":"Vadinar","idx":"1","dr":"1","power":"1","dra":"1","effp":"1"},
        {"name":"Jamnagar","idx":"2","dr":"2","power":"2","dra":"2","effp":"2"},
        {"name":"Rajkot","idx":"3","dr":"3","power":"3","dra":"3","effp":"3"},
        {"name":"Chotila","idx":"4","dr":None,"power":None,"dra":None,"effp":None},
        {"name":"Surendranagar","idx":"5","dr":"4","power":"4","dra":"4","effp":"5"},
        {"name":"Viramgam","idx":"6","dr":None,"power":None,"dra":None,"effp":None},
    ]
    # Helper to extract
    def val(key):
        v = local.get(key)
        if hasattr(v, 'is_expression') or hasattr(v, 'is_variable'):
            return float(pyo.value(v))
        if isinstance(v, (int, float)):
            return float(v)
        return None
    # Build rows
    rows = []
    for s in stations:
        row = {"Station": s["name"]}
        i = s["idx"]
        row["No. of Pumps"] = val(f"NOP{i}")
        row["Drag Reduction (%)"] = val(f"DR{s['dr']}") if s['dr'] else None
        row["Pump Speed (RPM)"] = val(f"N{i}")
        row["Residual Head (m)"] = val(f"RH{i}")
        row["Station Discharge Head (m)"] = val(f"SDHA_{i}")
        row["Pump Efficiency (%)"] = val(f"EFFP{s['effp']}") if s['effp'] else None
        row["Power Cost (₹)"] = val(f"OF_POWER_{s['power']}") if s['power'] else None
        row["DRA Cost (₹)"] = val(f"OF_DRA_{s['dra']}") if s['dra'] else None
        rows.append(row)
    # Summary
    total_cost = float(pyo.value(model.Objf))
    total_pumps = sum((r.get("No. of Pumps") or 0) for r in rows)
    effs = [r["Pump Efficiency (%)"] for r in rows if r.get("Pump Efficiency (%)") is not None]
    avg_eff = float(sum(effs)/len(effs)) if effs else None
    drs = [r["Drag Reduction (%)"] for r in rows if r.get("Drag Reduction (%)") is not None]
    avg_dra = float(sum(drs)/len(drs)) if drs else None
    return rows, total_cost, total_pumps, avg_eff, avg_dra

# Sidebar inputs
st.sidebar.header("🌊 Pipeline Inputs")
FLOW      = st.sidebar.number_input("Flow rate (KL/Hr)",    min_value=0.0, value=1000.0)
KV        = st.sidebar.number_input("Kinematic Viscosity (cSt)", min_value=0.0, value=10.0)
rho       = st.sidebar.number_input("Density (kg/m3)",     min_value=0.0, value=850.0)
SFC_J     = st.sidebar.number_input("SFC at Jamnagar (gm/bhp/hr)", min_value=0.0, value=200.0)
SFC_R     = st.sidebar.number_input("SFC at Rajkot (gm/bhp/hr)",  min_value=0.0, value=200.0)
SFC_S     = st.sidebar.number_input("SFC at Surendranagar (gm/bhp/hr)", min_value=0.0, value=200.0)
RateDRA   = st.sidebar.number_input("DRA Rate (Rs/L)",      min_value=0.0, value=9.0)
Price_HSD = st.sidebar.number_input("HSD Price (Rs/L)",     min_value=0.0, value=80.0)
solver_choice = st.sidebar.selectbox(
    "Solver Option",
    ["NEOS Bonmin (slower, remote)", "Local Bonmin (faster, if available)"]
)
# Run button
if st.sidebar.button("🚀 Run Optimization"):
    with st.spinner("Optimizing via " + solver_choice + "... please wait 🤖"):
        rows, total_cost, total_pumps, avg_eff, avg_dra = get_results(
            FLOW, KV, rho, SFC_J, SFC_R, SFC_S, RateDRA, Price_HSD, solver_choice
        )
    st.success("✅ Optimization Complete!")
    # Summary metrics
    st.markdown("### Summary Metrics")
    cols = st.columns(4)
    cols[0].metric("💰 Total Operating Cost (₹)", f"{total_cost:,.2f}")
    cols[1].metric("⚙️ Total Pumps", f"{int(total_pumps)}")
    cols[2].metric("⚙️ Avg Pump Efficiency (%)", f"{avg_eff:.2f}" if avg_eff else "N/A")
    cols[3].metric("🔥 Avg DRA Dosage (%)", f"{avg_dra:.2f}" if avg_dra else "N/A")
    # Results table
    df = pd.DataFrame(rows).set_index('Station').round(2)
    st.markdown("---")
    st.subheader("Station-wise Results")
    st.dataframe(df, use_container_width=True)
    # Charts
    st.markdown("---")
    st.subheader("Performance Charts")
    c1, c2 = st.columns(2)
    c1.bar_chart(df['No. of Pumps'], use_container_width=True)
    c2.line_chart(df['Pump Speed (RPM)'], use_container_width=True)
    c3, c4 = st.columns(2)
    c3.bar_chart(df['Power Cost (₹)'], use_container_width=True)
    c4.bar_chart(df['DRA Cost (₹)'], use_container_width=True)
else:
    st.title("Pipeline Optimization App")
    st.markdown(
        "Use the sidebar to enter pipeline inputs, then click **Run Optimization**.\n"
        "Summary metrics and detailed station-wise results with charts will be displayed."
    )
