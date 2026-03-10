"""
components/dashboard.py — Tab 1: KPI metrics + visual milestone timeline
"""

import streamlit as st
import pandas as pd
from datetime import date
from db import get_projects

STATUS_COLORS = {
    "pending":     "🟡",
    "in_progress": "🔵",
    "complete":    "🟢",
    "delayed":     "🔴",
}


def milestone_health(df: pd.DataFrame) -> dict:
    today   = date.today()
    total   = len(df)
    done    = int((df["status"] == "complete").sum())
    delayed = int((df["status"] == "delayed").sum())
    overdue = sum(
        1 for _, r in df.iterrows()
        if r["status"] != "complete" and date.fromisoformat(r["target_date"]) < today
    )
    return {"total": total, "done": done, "delayed": delayed, "overdue": overdue}


def render(project_id: int, project_name: str, milestones_df: pd.DataFrame):
    health = milestone_health(milestones_df)
    today  = date.today()

    # ── Project title + KPIs ──
    st.markdown(f"## {project_name}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 Total",     health["total"])
    c2.metric("✅ Completed", health["done"],
              delta=f"{int(health['done'] / max(health['total'], 1) * 100)}%")
    c3.metric("⚠️ Delayed",   health["delayed"])
    c4.metric("🔥 Overdue",   health["overdue"])

    # ── Overall progress bar ──
    pct       = int(health["done"] / max(health["total"], 1) * 100)
    bar_color = "#16a34a" if pct == 100 else ("#f0a500" if pct >= 50 else "#dc2626")
    st.markdown(f"""
    <div style="margin: 0.5rem 0 1.5rem;">
      <div style="font-size:0.75rem; color:#8b949e; margin-bottom:4px;">
        Overall Progress — {pct}%
      </div>
      <div class="timeline-bar">
        <div class="timeline-fill"
             style="width:{pct}%; background:{bar_color};"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Timeline cards ──
    st.markdown('<div class="section-title">Milestone Timeline</div>',
                unsafe_allow_html=True)

    if milestones_df.empty:
        st.info("No milestones found for this project.")
        return

    proj_row       = get_projects()
    proj_start_str = proj_row.loc[proj_row["id"] == project_id, "start_date"].values[0]
    proj_start_dt  = date.fromisoformat(proj_start_str)
    proj_end_dt    = date.fromisoformat(milestones_df["target_date"].max())
    total_span     = max((proj_end_dt - proj_start_dt).days, 1)

    for _, row in milestones_df.iterrows():
        td       = date.fromisoformat(row["target_date"])
        elapsed  = (td - proj_start_dt).days
        bar_pct  = int(elapsed / total_span * 100)
        is_over  = (td < today and row["status"] != "complete")
        badge_cl = f"badge badge-{row['status']}"

        overdue_tag = (
            f'<span class="overdue-chip">⚠ OVERDUE {(today - td).days}d</span>'
            if is_over else ""
        )
        fill_color = (
            "#16a34a" if row["status"] == "complete"
            else "#f0a500" if row["status"] == "in_progress"
            else "#dc2626" if (is_over or row["status"] == "delayed")
            else "#4b5563"
        )
        notes_html = (
            f'<div style="font-size:0.75rem;color:#8b949e;margin-top:4px;">📝 {row["notes"]}</div>'
            if row["notes"] else ""
        )

        st.markdown(f"""
        <div style="background:#161b22;border:1px solid #30363d;
                    border-radius:8px;padding:12px 16px;margin-bottom:8px;">
          <div style="display:flex;justify-content:space-between;
                      align-items:center;flex-wrap:wrap;gap:6px;">
            <div>
              <span style="font-weight:600;color:#e6edf3;">{row['name']}</span>
              &nbsp;{overdue_tag}
            </div>
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
              <span class="{badge_cl}">{row['status'].upper()}</span>
              <span style="font-size:0.78rem;color:#8b949e;
                           font-family:'IBM Plex Mono',monospace;">
                Target: {td.strftime('%d %b %Y')}
              </span>
            </div>
          </div>
          <div class="timeline-bar" style="margin-top:8px;">
            <div class="timeline-fill"
                 style="width:{bar_pct}%;background:{fill_color};"></div>
          </div>
          {notes_html}
        </div>
        """, unsafe_allow_html=True)

    # ── Raw data expander ──
    with st.expander("🗃️ View Raw Table"):
        display_df = milestones_df[[
            "name", "target_date", "actual_date", "status", "notes", "offset_days"
        ]].copy()
        display_df.columns = [
            "Milestone", "Target Date", "Actual Date", "Status", "Notes", "Offset (days)"
        ]
        st.dataframe(display_df, use_container_width=True, hide_index=True)