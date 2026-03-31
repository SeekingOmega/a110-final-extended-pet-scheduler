from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner_jordan = Owner(name="Jordan", available_time=60, preferences="morning routines")

pet_mochi = Pet(name="Mochi", species="cat", age=3)
pet_buddy = Pet(name="Buddy", species="dog", age=5, special_needs="joint supplements")

# --- Tasks for Mochi ---
pet_mochi.add_task(Task(name="Feeding",       duration=5,  priority="high",   frequency="daily"))
pet_mochi.add_task(Task(name="Playtime",      duration=20, priority="medium", frequency="daily"))

# --- Tasks for Buddy ---
pet_buddy.add_task(Task(name="Morning walk",  duration=30, priority="high",   frequency="daily"))
pet_buddy.add_task(Task(name="Joint meds",    duration=5,  priority="high",   frequency="daily"))
pet_buddy.add_task(Task(name="Grooming",      duration=25, priority="low",    frequency="weekly"))

# --- Register pets with owner ---
owner_jordan.add_pet(pet_mochi)
owner_jordan.add_pet(pet_buddy)

# --- Generate and print schedule ---
scheduler = Scheduler(owner_jordan)
print(scheduler.get_summary())
