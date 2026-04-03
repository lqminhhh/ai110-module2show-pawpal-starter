import streamlit as st
from datetime import date

from pawpal_system import Owner, Pet, Task, Priority, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# Section 1: Owner & Pet Setup
# ---------------------------------------------------------------------------
st.subheader("1. Owner & Pet Setup")

with st.form("setup_form"):
    owner_name = st.text_input("Owner name", value="Jordan")
    available_minutes = st.number_input(
        "Available minutes per day", min_value=10, max_value=480, value=90
    )
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    submitted = st.form_submit_button("Save owner & pet")

if submitted:
    owner = Owner(name=owner_name, available_minutes=int(available_minutes))
    pet = Pet(name=pet_name, species=species)
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.success(f"Saved! {owner_name} is caring for {pet_name} ({species}).")

# ---------------------------------------------------------------------------
# Sections 2 & 3 only appear once an owner exists
# ---------------------------------------------------------------------------
if st.session_state.owner:
    owner: Owner = st.session_state.owner
    active_pet: Pet = owner.pets[0]

    # -----------------------------------------------------------------------
    # Section 2: Task Management
    # -----------------------------------------------------------------------
    st.divider()
    st.subheader("2. Add Tasks")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority_str = st.selectbox("Priority", ["LOW", "MEDIUM", "HIGH"], index=2)
    with col4:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"])

    if st.button("Add task"):
        new_task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=Priority[priority_str],
            frequency=frequency,
        )
        if new_task.is_valid():
            active_pet.add_task(new_task)
            st.success(f"Added '{task_title}' to {active_pet.name}'s tasks.")
        else:
            st.error("Task title cannot be empty and duration must be at least 1 minute.")

    # --- Task list with pending / completed split ---
    all_tasks = active_pet.tasks
    if all_tasks:
        pending  = owner.get_tasks_by_status(completed=False)
        done     = owner.get_tasks_by_status(completed=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Pending", len(pending))
        with col_b:
            st.metric("Completed", len(done))

        st.write(f"**{active_pet.name}'s tasks ({len(all_tasks)} total):**")
        st.dataframe(
            [t.to_dict() for t in all_tasks],
            use_container_width=True,
        )

        # Mark-complete button per pending task
        if pending:
            st.write("**Mark a task complete:**")
            task_titles = [t.title for t in pending]
            selected_title = st.selectbox("Select task", task_titles, key="complete_select")
            if st.button("Mark complete"):
                for t in pending:
                    if t.title == selected_title:
                        next_task = t.mark_complete()
                        st.success(f"'{selected_title}' marked complete.")
                        if next_task:
                            active_pet.add_task(next_task)
                            st.info(
                                f"Recurring task detected — '{next_task.title}' "
                                f"({next_task.frequency}) has been added for the next occurrence."
                            )
                        break
    else:
        st.info("No tasks yet. Add one above.")

    # -----------------------------------------------------------------------
    # Section 3: Generate Today's Schedule
    # -----------------------------------------------------------------------
    st.divider()
    st.subheader("3. Generate Today's Schedule")

    day_of_week = date.today().weekday()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    st.caption(f"Scheduling for: **{day_names[day_of_week]}** — only tasks due today will appear.")

    if st.button("Generate schedule"):
        pending_today = [
            t for t in owner.get_all_pending_tasks()
            if t.due_today(day_of_week)
        ]

        if not pending_today:
            st.warning("No tasks are due today. Try adding tasks or check their frequency setting.")
        else:
            scheduler = Scheduler(owner)
            schedule = scheduler.generate(day_of_week=day_of_week)

            # --- Summary banner ---
            st.success("Schedule generated!")
            st.markdown(schedule.summary())

            # --- Sorted schedule table ---
            if schedule.items:
                sorted_items = scheduler.sort_by_time(schedule.items)
                st.write("**Today's plan (sorted by time):**")
                st.dataframe(
                    [item.to_dict() for item in sorted_items],
                    use_container_width=True,
                )

            # --- Skipped tasks ---
            if schedule.skipped_tasks:
                st.warning(
                    f"**Not enough time for:** "
                    + ", ".join(t.title for t in schedule.skipped_tasks)
                    + f". Consider reducing task durations or increasing your available time "
                    f"(currently {owner.available_minutes} min)."
                )

            # --- Conflict detection ---
            # Conflicts are most useful as a prominent warning block so the
            # owner can act before starting their day, not discover surprises mid-task.
            conflicts = scheduler.detect_conflicts(schedule)
            if conflicts:
                st.error(
                    f"**⚠ Scheduling conflict detected ({len(conflicts)} overlap(s)):**\n\n"
                    + "\n\n".join(f"- {w}" for w in conflicts)
                    + "\n\nPlease adjust task durations or priorities and regenerate."
                )
            else:
                st.success("No scheduling conflicts — your plan looks good!")

            # --- Filter: show tasks for one specific pet ---
            if len(owner.pets) > 1:
                st.divider()
                st.write("**Filter by pet:**")
                pet_names = [p.name for p in owner.pets]
                chosen = st.selectbox("Show tasks for", pet_names, key="filter_pet")
                filtered = owner.get_tasks_for_pet(chosen)
                if filtered:
                    st.dataframe(
                        [t.to_dict() for t in filtered],
                        use_container_width=True,
                    )
                else:
                    st.info(f"No tasks found for {chosen}.")

else:
    st.info("Fill in the owner & pet setup above to get started.")
