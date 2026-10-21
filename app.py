from datetime import date, datetime, time

import streamlit as st

from pawpal_system import Category, Frequency, Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("A pet care planner: add pets and tasks, then build a day plan.")

# Owner and Scheduler live in session_state so they survive Streamlit reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")
    st.session_state.scheduler = Scheduler(st.session_state.owner)
owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler
today = date.today()

# --- Owner and pets -------------------------------------------------------
st.subheader("Owner and pets")
col1, col2 = st.columns(2)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    owner.available_minutes_per_day = int(
        st.number_input("Minutes available per day", 10, 720, owner.available_minutes_per_day)
    )

with st.form("add_pet", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    new_pet_name = c1.text_input("Pet name")
    new_species = c2.selectbox("Species", ["dog", "cat", "other"])
    new_age = c3.number_input("Age", 0, 40, 1)
    if st.form_submit_button("Add pet"):
        if not new_pet_name.strip():
            st.error("Give the pet a name.")
        elif any(p.name.lower() == new_pet_name.strip().lower() for p in owner.pets):
            st.error(f"{new_pet_name} already exists.")
        else:
            owner.add_pet(Pet(new_pet_name.strip(), new_species, int(new_age)))
            st.rerun()

if not owner.pets:
    st.info("Add a pet to get started.")
    st.stop()

st.table(
    [
        {
            "Pet": p.name,
            "Species": p.species,
            "Age": p.age,
            "Special needs": p.special_needs or "-",
            "Tasks": len(p.tasks),
        }
        for p in owner.pets
    ]
)

with st.expander("Edit a pet"):
    edit_index = st.selectbox(
        "Pet to edit", range(len(owner.pets)), format_func=lambda i: owner.pets[i].name,
        key="edit_pet",
    )
    edit_pet = owner.pets[edit_index]
    species_options = ["dog", "cat", "other"]
    if edit_pet.species not in species_options:
        species_options.append(edit_pet.species)
    # Keys include the pet's name so the fields reset when another pet is picked.
    with st.form("edit_pet_form"):
        e1, e2, e3 = st.columns(3)
        edit_name = e1.text_input("Name", value=edit_pet.name, key=f"en_{id(edit_pet)}")
        edit_species = e2.selectbox(
            "Species", species_options, index=species_options.index(edit_pet.species),
            key=f"es_{id(edit_pet)}",
        )
        edit_age = e3.number_input("Age", 0, 40, edit_pet.age, key=f"ea_{id(edit_pet)}")
        edit_needs = st.text_input(
            "Special needs", value=edit_pet.special_needs, key=f"eh_{id(edit_pet)}"
        )
        if st.form_submit_button("Save changes"):
            new_name = edit_name.strip()
            if not new_name:
                st.error("A pet needs a name.")
            elif any(p is not edit_pet and p.name.lower() == new_name.lower() for p in owner.pets):
                st.error(f"{new_name} already exists.")
            else:
                edit_pet.name = new_name
                edit_pet.species = edit_species
                edit_pet.age = int(edit_age)
                edit_pet.special_needs = edit_needs.strip()
                st.success(f"Updated {new_name}.")
                st.rerun()

# --- Tasks ------------------------------------------------------------------
st.subheader("Tasks")
with st.form("add_task", clear_on_submit=False):
    c1, c2 = st.columns(2)
    pet_choice = c1.selectbox("Pet", [p.name for p in owner.pets])
    title = c2.text_input("Task title", value="Morning walk")
    c3, c4, c5 = st.columns(3)
    category = c3.selectbox("Category", list(Category), format_func=lambda c: c.value)
    duration = c4.number_input("Duration (min)", 1, 240, 20)
    priority = c5.selectbox("Priority", list(Priority), index=2, format_func=lambda p: p.name.title())
    c6, c7, c8 = st.columns(3)
    frequency = c6.selectbox("Repeats", list(Frequency), format_func=lambda f: f.value)
    set_time = c7.checkbox("Request a time")
    due_time = c8.time_input("Time", value=time(8, 0))
    if st.form_submit_button("Add task"):
        pet = next(p for p in owner.pets if p.name == pet_choice)
        due = datetime.combine(today, due_time) if set_time else None
        pet.add_task(
            Task(title.strip() or "Untitled", category, int(duration), priority, due, frequency)
        )
        st.rerun()

# Filtering and sorting come from the Scheduler.
pet_filter = st.selectbox("Show pet", ["All"] + [p.name for p in owner.pets])
pet_arg = None if pet_filter == "All" else pet_filter
pending = scheduler.sort_tasks_by_time(scheduler.filter_tasks(pet=pet_arg, status=False))
completed = scheduler.sort_tasks_by_time(scheduler.filter_tasks(pet=pet_arg, status=True))

PRIORITY_BADGE = {Priority.HIGH: "🔴 High", Priority.MEDIUM: "🟡 Medium", Priority.LOW: "🟢 Low"}


def task_rows(task_list):
    return [
        {
            "Pet": t.pet.name if t.pet else "?",
            "Task": t.title,
            "Category": t.category.value.title(),
            "Priority": PRIORITY_BADGE[t.priority],
            "Min": t.duration_minutes,
            "Requested time": f"{t.due:%a %H:%M}" if t.due else "Flexible",
            "Repeats": t.frequency.value.title(),
        }
        for t in task_list
    ]


if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

m1, m2, m3 = st.columns(3)
m1.metric("Pending", len(pending))
m2.metric("Minutes pending", sum(t.duration_minutes for t in pending))
m3.metric("Completed", len(completed))

st.markdown("#### ⏳ Pending")
if pending:
    st.caption("Sorted by requested time; flexible tasks last.")
    st.table(task_rows(pending))
    done_index = st.selectbox(
        "Mark a task complete",
        range(len(pending)),
        format_func=lambda i: f"{pending[i].pet.name if pending[i].pet else '?'}: {pending[i].title}",
    )
    if st.button("Complete task"):
        task = pending[done_index]
        nxt = scheduler.complete_task(task)
        if nxt is not None:
            when = f" due {nxt.due:%a %H:%M}" if nxt.due else ""
            st.session_state.flash = (
                f"Completed {task.title}. Next {nxt.frequency.value} occurrence added{when}."
            )
        else:
            st.session_state.flash = f"Completed {task.title}."
        st.session_state.generated = False  # the old plan still lists this task
        st.rerun()
else:
    st.info("No pending tasks.")

if completed:
    with st.expander(f"✅ Completed ({len(completed)})"):
        st.table(task_rows(completed))

# Conflict warnings about requested times, before any planning.
conflicts = scheduler.conflict_warnings(on_date=today)
if conflicts:
    st.warning(
        f"⚠️ {len(conflicts)} scheduling conflict(s) in the times you requested. "
        "The planner will shift tasks apart when you generate a schedule."
    )
    for warning in conflicts:
        st.warning(warning)
elif scheduler.filter_tasks(status=False):
    st.success("✅ No conflicts between requested times.")

st.divider()

# --- Schedule ---------------------------------------------------------------
st.subheader("Build schedule")
if st.button("Generate schedule"):
    scheduler.generate_schedule(today)
    st.session_state.generated = True

if st.session_state.get("generated"):
    v1, v2 = st.columns(2)
    order = v1.radio("Order by", ["Time", "Priority"], horizontal=True)
    view_pet = v2.selectbox("Pet", ["All"] + [p.name for p in owner.pets], key="view_pet")

    if view_pet == "All":
        items = scheduler.sort_by_time() if order == "Time" else scheduler.sort_by_priority()
    else:
        pet_obj = next(p for p in owner.pets if p.name == view_pet)
        items = scheduler.get_schedule_for(pet_obj)
        if order == "Priority":
            items = sorted(items, key=lambda i: (-i.task.priority, i.start))

    total = sum(i.task.duration_minutes for i in scheduler.schedule)
    budget = owner.available_minutes_per_day
    s1, s2, s3 = st.columns(3)
    s1.metric("Planned", f"{len(scheduler.schedule)} tasks")
    s2.metric("Time used", f"{total} / {budget} min")
    s3.metric("Not scheduled", len(scheduler.skipped_tasks) + len(scheduler.unplaced))
    st.progress(min(total / budget, 1.0))

    if items:
        st.success(f"Plan for {today:%A, %B %d}: {len(items)} task(s), sorted by {order.lower()}.")
        st.table(
            [
                {
                    "Time": f"{i.start:%H:%M} - {i.end:%H:%M}",
                    "Pet": i.task.pet.name if i.task.pet else "?",
                    "Task": i.task.title,
                    "Priority": PRIORITY_BADGE[i.task.priority],
                    "Why": i.reason,
                }
                for i in items
            ]
        )
    else:
        st.info("Nothing scheduled.")

    if not scheduler.detect_conflicts():
        st.success("✅ The generated plan has no overlapping tasks.")
    else:
        st.error("The generated plan has overlapping tasks.")

    for w in scheduler.warnings:
        st.warning(w)
    for task, why in scheduler.unplaced:
        st.warning(f"Could not place {task.pet.name if task.pet else '?'}: {task.title} - {why}")
    skipped = scheduler.skipped_tasks
    if view_pet != "All":
        skipped = scheduler.get_skipped_for(pet_obj)
    if skipped:
        st.info(
            "**Skipped (did not fit in the time budget):**\n"
            + "\n".join(
                f"- {t.pet.name if t.pet else '?'}: {t.title} ({t.duration_minutes} min)"
                for t in skipped
            )
        )

    with st.expander("Plan as text"):
        st.text(scheduler.explain_plan())
