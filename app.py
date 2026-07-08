from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app. Add an owner, add pets, add tasks for each pet,
then build today's schedule.
"""
)

# --- Owner setup (stored once in the session vault) ---
st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")
owner_contact = st.text_input("Owner contact info", value="jordan@example.com")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, contact_info=owner_contact)
owner: Owner = st.session_state.owner
owner.name = owner_name
owner.contact_info = owner_contact

st.divider()

# --- Adding a Pet ---
st.subheader("Add a Pet")
col1, col2, col3, col4 = st.columns(4)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    breed = st.text_input("Breed", value="Unknown")
with col4:
    age = st.number_input("Age", min_value=0, max_value=40, value=2)

if st.button("Add pet"):
    new_pet = Pet(name=pet_name, species=species, breed=breed, age=int(age))
    owner.add_pet(new_pet)
    st.success(f"Added {new_pet.name} to {owner.name}'s pets.")

if owner.get_pets():
    st.write("Current pets:")
    st.table(
        [
            {"name": pet.name, "species": pet.species, "breed": pet.breed, "age": pet.age}
            for pet in owner.get_pets()
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Scheduling a Task (i.e. attaching tasks to a pet) ---
st.subheader("Add a Task")

if not owner.get_pets():
    st.info("Add a pet first before adding tasks.")
else:
    pet_names = [pet.name for pet in owner.get_pets()]
    selected_pet_name = st.selectbox("Pet", pet_names)
    selected_pet = next(pet for pet in owner.get_pets() if pet.name == selected_pet_name)

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
        category = st.text_input("Category", value="exercise")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col3:
        recurrence = st.selectbox("Recurrence", [None, "daily", "weekly", "monthly"])
        due_date = st.date_input("Next due date", value=date.today())

    if st.button("Add task"):
        new_task = Task(
            title=task_title,
            category=category,
            duration_minutes=int(duration),
            priority=priority,
            recurrence=recurrence,
            next_due_date=due_date,
        )
        selected_pet.add_task(new_task)
        st.success(f"Added task '{new_task.title}' to {selected_pet.name}.")

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        status_filter = st.radio("Show", ["All", "Pending", "Completed"], horizontal=True)
        if status_filter == "Pending":
            visible_tasks = owner.get_tasks_by_status(completed=False)
        elif status_filter == "Completed":
            visible_tasks = owner.get_tasks_by_status(completed=True)
        else:
            visible_tasks = all_tasks

        if visible_tasks:
            st.table(
                [
                    {
                        "pet": task.pet.name if task.pet else "",
                        "title": task.title,
                        "category": task.category,
                        "duration_minutes": task.duration_minutes,
                        "priority": task.priority,
                        "recurrence": task.recurrence,
                        "next_due_date": task.next_due_date,
                        "completed": task.completed,
                    }
                    for task in visible_tasks
                ]
            )
        else:
            st.info(f"No {status_filter.lower()} tasks.")
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Build Schedule ---
st.subheader("Build Schedule")
schedule_date = st.date_input("Schedule date", value=date.today(), key="schedule_date")
time_budget = st.number_input("Time budget (minutes)", min_value=1, max_value=1440, value=60)

if st.button("Generate schedule"):
    scheduler = Scheduler.build(owner, schedule_date, int(time_budget))
    st.session_state.scheduler = scheduler

if "scheduler" in st.session_state:
    scheduler: Scheduler = st.session_state.scheduler

    if not scheduler.scheduled_tasks:
        st.info(f"No tasks scheduled for {scheduler.date}.")
    else:
        ordered_pairs = scheduler.sort_by_time(
            scheduler.sort_by_priority([task for _, task in scheduler.scheduled_tasks])
        )
        pet_by_task = {task: pet for pet, task in scheduler.scheduled_tasks}

        col1, col2 = st.columns(2)
        col1.metric("Time used", f"{scheduler.total_duration()} min")
        col2.metric("Time remaining", f"{scheduler.remaining_time()} min")

        st.table(
            [
                {
                    "pet": pet_by_task[task].name,
                    "task": task.title,
                    "priority": task.priority,
                    "duration_minutes": task.duration_minutes,
                    "scheduled_time": task.scheduled_time or "",
                }
                for task in ordered_pairs
            ]
        )

        conflicts = scheduler.detect_conflicts()
        time_conflicts = scheduler.detect_time_conflicts()

        for first, second in conflicts:
            st.warning(f"Conflict: '{first.title}' vs '{second.title}' ({first.category})")

        for warning in time_conflicts:
            st.warning(warning)

        if not conflicts and not time_conflicts:
            st.success("Schedule built with no conflicts.")
