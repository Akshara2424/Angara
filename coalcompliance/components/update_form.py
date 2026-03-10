"""
components/update_form.py — Tab 2: Update milestone status, notes, actual date
"""

import streamlit as st
import pandas as pd
from datetime import date
from db import update_milestone

STATUS_OPTIONS  = ["pending", "in_progress", "complete", "delayed"]
STATUS_EMOJI    = {"pending": "🟡", "in_progress": "🔵", "complete": "🟢", "delayed": "🔴"}


def render(milestones_df: pd.DataFrame):
    st.markdown('<div class="section-title">Update Status & Notes</div>',
                unsafe_allow_html=True)

    if milestones_df.empty:
        st.info("No milestones to update.")
        return

    for _, row in milestones_df.iterrows():
        emoji  = STATUS_EMOJI.get(row["status"], "⚪")
        label  = f"{emoji}  {row['name']}  — Target: {row['target_date']}"

        with st.expander(label):
            with st.form(f"update_form_{row['id']}", clear_on_submit=False):
                col_a, col_b = st.columns([1, 1])

                with col_a:
                    new_status = st.selectbox(
                        "Status",
                        options=STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(row["status"]),
                        key=f"status_{row['id']}",
                    )
                with col_b:
                    actual_val = (
                        date.fromisoformat(row["actual_date"])
                        if row["actual_date"] else None
                    )
                    new_actual = st.date_input(
                        "Actual Completion Date (optional)",
                        value=actual_val,
                        key=f"actual_{row['id']}",
                    )

                new_notes = st.text_area(
                    "Notes",
                    value=row["notes"] or "",
                    placeholder="Add observations, blockers, or document references…",
                    key=f"notes_{row['id']}",
                    height=80,
                )

                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    update_milestone(
                        row["id"],
                        new_status,
                        new_notes,
                        new_actual.isoformat() if new_actual else None,
                    )
                    st.success("✅ Milestone updated!")
                    st.rerun()