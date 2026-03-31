from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_time=60, preferences="morning routines")

mochi = Pet(name="Mochi", species="cat", age=3)
buddy = Pet(name="Buddy", species="dog", age=5, special_needs="joint supplements")

# --- Tasks for Mochi ---
mochi.add_task(Task(name="Feeding",       duration=5,  priority="high",   frequency="daily"))
mochi.add_task(Task(name="Playtime",      duration=20, priority="medium", frequency="daily"))

# --- Tasks for Buddy ---
buddy.add_task(Task(name="Morning walk",  duration=30, priority="high",   frequency="daily"))
buddy.add_task(Task(name="Joint meds",    duration=5,  priority="high",   frequency="daily"))
buddy.add_task(Task(name="Grooming",      duration=25, priority="low",    frequency="weekly"))

# --- Register pets with owner ---
owner.add_pet(mochi)
owner.add_pet(buddy)

# --- Generate and print schedule ---
scheduler = Scheduler(owner)
print(scheduler.get_summary())
