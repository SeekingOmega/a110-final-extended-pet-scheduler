import os
from datetime import date, timedelta
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler
from calendar_auth import get_credentials, is_authenticated, revoke_credentials
from calendar_client import read_events, create_event
from data_io import export_data, import_data
from gemini_scheduler import GeminiScheduler
from calendar_component import generate_calendar_html, render_unschedulable_html

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("A daily pet care planner.")

# ── Session state init ────────────────────────────────────────────────────────
if "pets"            not in st.session_state: st.session_state.pets = []
if "schedule"        not in st.session_state: st.session_state.schedule = None
if "proposed_events" not in st.session_state: st.session_state.proposed_events = []
if "unschedulable"   not in st.session_state: st.session_state.unschedulable = []
if "agent_steps"     not in st.session_state: st.session_state.agent_steps = []
if "cal_events"      not in st.session_state: st.session_state.cal_events = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    # Google Calendar auth
    st.subheader("Google Calendar")
    if is_authenticated():
        st.success("Connected")
        if st.button("Disconnect"):
            revoke_credentials()
            st.rerun()
    else:
        if st.button("Connect Google Calendar"):
            try:
                get_credentials()
                st.rerun()
            except Exception as e:
                st.error(f"Auth failed: {e}")

    st.divider()

    # Week selection
    st.subheader("Week")
    next_monday = date.today() + timedelta(days=(7 - date.today().weekday()) % 7 or 7)
    week_start = st.date_input("Week starting (Monday)", value=next_monday)
    week_end   = week_start + timedelta(days=6)
    st.caption(f"{week_start.strftime('%b %d')} – {week_end.strftime('%b %d, %Y')}")

    st.divider()

    # Active hours
    st.subheader("Active Hours")
    import datetime as _dt
    col1, col2 = st.columns(2)
    with col1:
        active_start = st.time_input("From", value=_dt.time(7, 0), key="active_from")
    with col2:
        active_end = st.time_input("To", value=_dt.time(22, 0), key="active_to")

    st.divider()

    # Import / Export
    st.subheader("Data")
    if st.session_state.pets:
        _export_owner = Owner(
            name=st.session_state.get("owner_name_val", "Owner"),
            available_time=st.session_state.get("available_time_val", 60),
        )
        export_json = export_data(_export_owner, st.session_state.pets)
        st.download_button(
            label="⬇ Export pets & tasks",
            data=export_json,
            file_name="pawpal_data.json",
            mime="application/json",
        )
    uploaded = st.file_uploader("⬆ Import pets & tasks", type="json", label_visibility="collapsed")
    if uploaded is not None:
        try:
            _, imported_pets = import_data(uploaded.read().decode())
            st.session_state.pets = imported_pets
            st.success(f"Imported {len(imported_pets)} pet(s).")
            st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

st.divider()

# ── Owner ─────────────────────────────────────────────────────────────────────
st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_time = st.number_input("Available time (min/day)", min_value=1, max_value=480, value=60)
st.session_state["owner_name_val"]     = owner_name
st.session_state["available_time_val"] = available_time

st.divider()

# ── Add a pet ─────────────────────────────────────────────────────────────────
st.subheader("Pets")

with st.form("add_pet_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age", min_value=0, max_value=30, value=1)
    special_needs = st.text_input("Special needs (optional)")
    add_pet = st.form_submit_button("Add pet")

if add_pet:
    if not pet_name.strip():
        st.warning("Please enter a pet name.")
    else:
        st.session_state.pets.append(
            Pet(name=pet_name.strip(), species=species, age=age, special_needs=special_needs)
        )

if st.session_state.pets:
    st.write(f"{len(st.session_state.pets)} pet(s) registered:")
    st.table([
        {"Name": p.name, "Species": p.species, "Age": p.age, "Special needs": p.special_needs or "—"}
        for p in st.session_state.pets
    ])
    if st.button("Remove all pets"):
        st.session_state.pets = []
        st.rerun()
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ── Add a task ────────────────────────────────────────────────────────────────
st.subheader("Tasks")

if not st.session_state.pets:
    st.info("Add a pet first before adding tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_names  = [p.name for p in st.session_state.pets]
        target_pet = st.selectbox("Assign to pet", pet_names)

        col1, col2, col3 = st.columns(3)
        with col1:
            task_name = st.text_input("Task name")
        with col2:
            duration  = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            task_time = st.text_input("Scheduled time (HH:MM, optional)")

        col1, col2, col3 = st.columns(3)
        with col1:
            priority  = st.selectbox("Priority", ["high", "medium", "low"])
        with col2:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        with col3:
            due_date  = st.text_input("Due date (YYYY-MM-DD, optional)")
        add_task = st.form_submit_button("Add task")

    if add_task:
        if not task_name.strip():
            st.warning("Please enter a task name.")
        else:
            pet = next(p for p in st.session_state.pets if p.name == target_pet)
            pet.add_task(Task(
                name=task_name.strip(),
                duration=int(duration),
                priority=priority,
                frequency=frequency,
                time=task_time.strip(),
                due_date=due_date.strip(),
            ))

    # ── Sort & filter controls ────────────────────────────────────────────────
    total_tasks = sum(len(p.tasks) for p in st.session_state.pets)

    if total_tasks == 0:
        st.info("No tasks yet. Add one above.")
    else:
        st.markdown("#### View Task List")
        col1, col2, col3 = st.columns(3)
        with col1:
            sort_by = st.selectbox("Sort by", ["Default (by pet)", "Scheduled time"])
        with col2:
            filter_status = st.selectbox("Filter by status", ["All", "Pending", "Completed"])
        with col3:
            pet_filter_options = ["All pets"] + [p.name for p in st.session_state.pets]
            filter_pet = st.selectbox("Filter by pet", pet_filter_options)

        # Build a temporary owner + scheduler just for sorting/filtering
        _owner = Owner(name=owner_name, available_time=int(available_time))
        for p in st.session_state.pets:
            _owner.add_pet(p)
        _scheduler = Scheduler(_owner)

        # Apply filter
        completed_filter = None if filter_status == "All" else (filter_status == "Completed")
        pet_name_filter  = None if filter_pet == "All pets" else filter_pet
        tasks = _scheduler.filter_tasks(completed=completed_filter, pet_name=pet_name_filter)

        # Apply sort
        if sort_by == "Scheduled time":
            tasks = sorted(tasks, key=lambda t: t.time if t.time else "99:99")

        if not tasks:
            st.info("No tasks match the current filter.")
        else:
            pet_by_task = {id(task): pet for pet in st.session_state.pets for task in pet.tasks}
            rows = [
                {
                    "🗑️":            False,
                    "Done":           t.completed,
                    "Pet":            pet_by_task[id(t)].name if id(t) in pet_by_task else "—",
                    "Task":           t.name,
                    "Due date":       t.due_date or "—",
                    "Time":           t.time or "—",
                    "Duration (min)": t.duration,
                    "Priority":       t.priority,
                    "Frequency":      t.frequency,
                    "_task_ref":      t,
                }
                for t in tasks
            ]
            edited = st.data_editor(
                [{k: v for k, v in r.items() if k != "_task_ref"} for r in rows],
                column_config={
                    "🗑️":  st.column_config.CheckboxColumn("🗑️"),
                    "Done": st.column_config.CheckboxColumn("Done"),
                },
                disabled=["Pet", "Task", "Due date", "Time", "Duration (min)", "Priority", "Frequency"],
                hide_index=True,
                use_container_width=True,
            )
            changed = False
            for row, original in zip(edited, rows):
                task = original["_task_ref"]
                pet  = pet_by_task.get(id(task))
                if row["🗑️"]:
                    pet.remove_task(task)
                    changed = True
                elif row["Done"] and not task.completed:
                    _scheduler.handle_completion(pet, task)
                    changed = True
                elif not row["Done"] and task.completed:
                    task.reset()
                    changed = True
            if changed:
                st.rerun()

st.divider()

# ── Generate Schedule ─────────────────────────────────────────────────────────
st.subheader("Generate Weekly Schedule")

gemini_key = os.environ.get("GEMINI_API_KEY", "")
if not gemini_key:
    st.warning("Set the GEMINI_API_KEY environment variable to enable scheduling.")
elif not is_authenticated():
    st.info("Connect your Google Calendar in the sidebar to generate a schedule.")
elif not st.session_state.pets or sum(len(p.tasks) for p in st.session_state.pets) == 0:
    st.info("Add at least one pet and one task before generating a schedule.")
else:
    def _calendar_reader(start_date: str, end_date: str) -> list[dict]:
        from datetime import date as _date
        return read_events(
            _date.fromisoformat(start_date),
            _date.fromisoformat(end_date),
        )

    def _task_lister() -> dict:
        return {
            "owner": {
                "name": owner_name,
                "active_hours_start": active_start.strftime("%H:%M"),
                "active_hours_end":   active_end.strftime("%H:%M"),
            },
            "pets": [
                {
                    "name":    p.name,
                    "species": p.species,
                    "tasks": [
                        {
                            "name":      t.name,
                            "duration":  t.duration,
                            "priority":  t.priority,
                            "frequency": t.frequency,
                            "due_date":  t.due_date,
                        }
                        for t in p.get_pending_tasks()
                    ],
                }
                for p in st.session_state.pets
            ],
            "week_start": week_start.isoformat(),
            "week_end":   week_end.isoformat(),
        }

    if st.button("✨ Generate Schedule with Gemini", type="primary"):
        with st.spinner("Gemini is reading your calendar and proposing a schedule..."):
            try:
                scheduler = GeminiScheduler(
                    api_key=gemini_key,
                    calendar_reader=_calendar_reader,
                    task_lister=_task_lister,
                )
                result = scheduler.generate_schedule()

                st.session_state.cal_events      = read_events(week_start, week_end)
                st.session_state.proposed_events = result.get("proposed_events", [])
                st.session_state.unschedulable   = result.get("unschedulable", [])
                st.session_state.agent_steps     = scheduler.steps
                st.session_state.schedule        = result

            except Exception as e:
                st.error(f"Scheduling failed: {e}")

    if st.session_state.schedule is not None:
        st.success(f"Gemini proposed {len(st.session_state.proposed_events)} event(s).")

        summary = st.session_state.schedule.get("reasoning_summary", "")
        if summary:
            st.caption(f"💬 {summary}")

        if st.session_state.agent_steps:
            with st.expander("🔍 Gemini's tool call steps"):
                for step in st.session_state.agent_steps:
                    st.json(step)

        st.markdown("#### Proposed Week")

        cal_html = generate_calendar_html(
            week_start=week_start,
            existing_events=st.session_state.cal_events,
            proposed_events=st.session_state.proposed_events,
            active_start=active_start.strftime("%H:%M"),
            active_end=active_end.strftime("%H:%M"),
        )
        st.components.v1.html(cal_html, height=500, scrolling=True)

        if st.session_state.unschedulable:
            unsch_html = render_unschedulable_html(st.session_state.unschedulable)
            st.components.v1.html(unsch_html, height=max(60, len(st.session_state.unschedulable) * 32 + 40))

        st.markdown("#### Review & Approve Events")
        st.caption("Uncheck events to reject them. Edit Day or Time to adjust.")

        rows = [
            {
                "Approve":        True,
                "Pet":            ev["pet_name"],
                "Task":           ev["task_name"],
                "Day":            ev["day"],
                "Time":           ev["start_time"],
                "Duration(min)":  ev["duration_min"],
                "Priority":       ev["priority"],
                "_idx":           i,
            }
            for i, ev in enumerate(st.session_state.proposed_events)
        ]

        edited = st.data_editor(
            [{k: v for k, v in r.items() if k != "_idx"} for r in rows],
            column_config={
                "Approve": st.column_config.CheckboxColumn("Approve"),
                "Day":     st.column_config.TextColumn("Day (YYYY-MM-DD)"),
                "Time":    st.column_config.TextColumn("Time (HH:MM)"),
            },
            disabled=["Pet", "Task", "Duration(min)", "Priority"],
            hide_index=True,
            use_container_width=True,
            key="schedule_editor",
        )

        for row, original in zip(edited, rows):
            ev = st.session_state.proposed_events[original["_idx"]]
            ev["day"]        = row["Day"]
            ev["start_time"] = row["Time"]

        approved = [
            st.session_state.proposed_events[r["_idx"]]
            for row, r in zip(edited, rows)
            if row["Approve"]
        ]
        rejected = [
            st.session_state.proposed_events[r["_idx"]]
            for row, r in zip(edited, rows)
            if not row["Approve"]
        ]

        col1, col2 = st.columns(2)

        with col1:
            if approved:
                if st.button(f"✅ Add {len(approved)} event(s) to Google Calendar", type="primary"):
                    written, failed = 0, []
                    for ev in approved:
                        try:
                            create_event(
                                title=f"🐾 {ev['task_name']} ({ev['pet_name']})",
                                day=ev["day"],
                                start_time=ev["start_time"],
                                duration_min=ev["duration_min"],
                                description=f"PawPal+ scheduled pet care task – Priority: {ev['priority']}",
                            )
                            written += 1
                        except Exception as e:
                            failed.append(f"{ev['task_name']}: {e}")
                    if failed:
                        st.error("Some events failed to write:\n" + "\n".join(failed))
                    else:
                        st.success(f"✅ {written} event(s) added to your Google Calendar!")
                        st.session_state.schedule        = None
                        st.session_state.proposed_events = []
                        st.session_state.unschedulable   = []
                        st.session_state.agent_steps     = []
                        st.rerun()

        with col2:
            if rejected and gemini_key and is_authenticated():
                if st.button(f"↺ Reschedule {len(rejected)} rejected event(s)"):
                    with st.spinner("Gemini is finding new slots for rejected events..."):
                        try:
                            sched = GeminiScheduler(
                                api_key=gemini_key,
                                calendar_reader=_calendar_reader,
                                task_lister=_task_lister,
                            )
                            result = sched.reschedule_rejected(
                                rejected=rejected,
                                confirmed=approved,
                            )
                            remaining = [
                                ev for ev in st.session_state.proposed_events
                                if ev not in rejected
                            ]
                            st.session_state.proposed_events = remaining + result.get("proposed_events", [])
                            st.session_state.unschedulable  += result.get("unschedulable", [])
                            st.session_state.agent_steps     = sched.steps
                            st.rerun()
                        except Exception as e:
                            st.error(f"Reschedule failed: {e}")
