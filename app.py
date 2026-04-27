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

# ── Generate schedule ─────────────────────────────────────────────────────────
st.subheader("Generate Schedule")

if st.button("Generate schedule", type="primary"):
    if not st.session_state.pets:
        st.warning("Add at least one pet before generating a schedule.")
    elif sum(len(p.tasks) for p in st.session_state.pets) == 0:
        st.warning("Add at least one task before generating a schedule.")
    else:
        owner = Owner(name=owner_name, available_time=int(available_time))
        for pet in st.session_state.pets:
            owner.add_pet(pet)

        scheduler = Scheduler(owner)
        plan      = scheduler.generate_plan()

        st.success("Schedule generated!")
        st.text(scheduler.get_summary())

        pet_by_task  = {id(task): pet.name for pet in owner.pets for task in pet.tasks}
        all_tasks    = owner.get_all_tasks()
        not_in_plan  = [t for t in all_tasks if t not in plan]
        already_done = [t for t in not_in_plan if t.completed]
        skipped      = [t for t in not_in_plan if not t.completed]

        # Separate conflict-skipped tasks from time-overflow tasks
        conflicts      = scheduler.get_conflicts()
        conflicted_tasks = {id(task) for pairs in conflicts.values() for _, task in pairs[1:]}
        no_time    = [t for t in skipped if id(t) not in conflicted_tasks]
        conflicted = [t for t in skipped if id(t) in conflicted_tasks]

        def label(t):
            return f"{t.name} ({pet_by_task.get(id(t), '?')})"

        if already_done:
            st.info(
                f"{len(already_done)} task(s) already completed: "
                + ", ".join(label(t) for t in already_done)
            )
        for slot, pairs in conflicts.items():
            winner_pet, winner = pairs[0]
            losers = ", ".join(f"{t.name} ({p.name})" for p, t in pairs[1:])
            time_label = slot.replace("@", " on ") if "@" in slot else slot
            st.warning(
                f"Time conflict at {time_label}: **{winner.name} ({winner_pet.name})** was scheduled. "
                f"{losers} {'was' if len(pairs) == 2 else 'were'} omitted."
            )
        if no_time:
            st.warning(
                f"{len(no_time)} task(s) didn't fit in {available_time} min: "
                + ", ".join(label(t) for t in no_time)
            )
