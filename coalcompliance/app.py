"""
app.py — Streamlit entry point for Coal Mine Compliance Tracker (Module 1)

Run with:
    streamlit run app.py
"""

import streamlit as st
import sqlite3
from datetime import date
from db import init_db, get_projects, create_project, delete_project, get_milestones
from components import dashboard, update_form, add_milestone


# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CoalTrack — Compliance Module",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────
# GLOBAL STYLES (mobile-responsive)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"]  { font-family: 'IBM Plex Sans', sans-serif; }
h1, h2, h3                  { font-family: 'IBM Plex Mono', monospace; }

[data-testid="stSidebar"] {
    background: #0d1117;
    border-right: 2px solid #f0a500;
}
[data-testid="stSidebar"] * { color: #e6edf3 !important; }

[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px;
}

/* Status badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.05em;
}
.badge-pending     { background:#2d2d00; color:#f0e68c; border:1px solid #a89020; }
.badge-in_progress { background:#002d4a; color:#7dd3fc; border:1px solid #0284c7; }
.badge-complete    { background:#003d1f; color:#86efac; border:1px solid #16a34a; }
.badge-delayed     { background:#3d0000; color:#fca5a5; border:1px solid #dc2626; }

/* Timeline bar */
.timeline-bar  { height:8px; border-radius:4px; background:#30363d; margin:4px 0; overflow:hidden; }
.timeline-fill { height:100%; border-radius:4px; }

/* Overdue chip */
.overdue-chip {
    background:#3d0000; color:#fca5a5;
    border:1px solid #dc2626; border-radius:4px;
    padding:2px 8px; font-size:0.7rem;
    font-family:'IBM Plex Mono',monospace;
}

/* Section title */
.section-title {
    color:#f0a500;
    font-family:'IBM Plex Mono',monospace;
    font-size:0.8rem;
    letter-spacing:0.15em;
    text-transform:uppercase;
    border-bottom:1px solid #30363d;
    padding-bottom:4px;
    margin:1.5rem 0 0.75rem;
}

/* App header */
.app-header {
    background: linear-gradient(135deg,#0d1117 0%,#1c2836 50%,#0d1117 100%);
    border-bottom: 3px solid #f0a500;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    border-radius: 8px;
}
.app-header h1 { color:#f0a500; margin:0; font-size:clamp(1.2rem,4vw,1.8rem); }
.app-header p  { color:#8b949e; margin:4px 0 0; font-size:0.85rem; }

/* Mobile: stack columns */
@media (max-width: 640px) {
    [data-testid="column"] { min-width:100% !important; flex:1 1 100% !important; }
    .stDataFrame            { font-size:12px; }
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────
init_db()

st.markdown("""
<div class="app-header">
  <h1>⛏️ CoalTrack — Compliance Module 1</h1>
  <p>Regulatory Milestone Tracker · SQLite · Module 1 of N</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SIDEBAR — Project management
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📁 Projects")
    st.markdown("---")

    projects_df = get_projects()

    if projects_df.empty:
        st.info("No projects yet. Create one below.")
        selected_project_id   = None
        selected_project_name = None
    else:
        project_options       = dict(zip(projects_df["name"], projects_df["id"]))
        selected_project_name = st.selectbox("Active Project", list(project_options.keys()))
        selected_project_id   = project_options[selected_project_name]

    st.markdown('<div class="section-title">New Project</div>', unsafe_allow_html=True)

    with st.form("new_project_form", clear_on_submit=True):
        proj_name     = st.text_input("Project Name *", placeholder="e.g. Jharia Block-4")
        proj_location = st.text_input("Location",       placeholder="e.g. Dhanbad, Jharkhand")
        proj_start    = st.date_input("Start Date *",   value=date.today())

        if st.form_submit_button("➕ Create Project", use_container_width=True):
            if not proj_name.strip():
                st.error("Project name is required.")
            else:
                try:
                    create_project(proj_name.strip(), proj_start, proj_location.strip())
                    st.success(f"✅ '{proj_name}' created with 5 default milestones.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("A project with this name already exists.")

    if selected_project_id:
        st.markdown("---")
        if st.button("🗑️ Delete Active Project", use_container_width=True, type="secondary"):
            delete_project(selected_project_id)
            st.warning(f"'{selected_project_name}' deleted.")
            st.rerun()


# ─────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────
if not selected_project_id:
    st.markdown("""
    <div style="text-align:center;padding:3rem;color:#8b949e;">
      <h2 style="color:#f0a500">👈 Create a project to begin</h2>
      <p>Use the sidebar to set up your first compliance project.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

milestones_df = get_milestones(selected_project_id)

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "✏️ Update Milestones", "➕ Add Milestone"])

with tab1:
    dashboard.render(selected_project_id, selected_project_name, milestones_df)

with tab2:
    update_form.render(milestones_df)

with tab3:
    add_milestone.render(selected_project_id)