from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner_jordan = Owner(name="Jordan", available_time=120, preferences="morning routines")

pet_mochi = Pet(name="Mochi", species="cat", age=3)
pet_buddy = Pet(name="Buddy", species="dog", age=5, special_needs="joint supplements")

# --- Tasks (two intentionally at the same time to trigger conflict) ---
pet_mochi.add_task(Task(name="Feeding",      duration=5,  priority="high",   frequency="daily", time="07:00"))
pet_mochi.add_task(Task(name="Playtime",     duration=20, priority="medium", frequency="daily", time="15:30"))

pet_buddy.add_task(Task(name="Morning walk", duration=30, priority="high",   frequency="daily", time="07:00"))  # conflicts with Feeding
pet_buddy.add_task(Task(name="Joint meds",   duration=5,  priority="high",   frequency="daily", time="07:30"))
pet_buddy.add_task(Task(name="Grooming",     duration=25, priority="low",    frequency="weekly",time="16:00"))

owner_jordan.add_pet(pet_mochi)
owner_jordan.add_pet(pet_buddy)

scheduler = Scheduler(owner_jordan)

# --- Conflict detection ---
print("=" * 50)
print("Conflict check:")
conflicts = scheduler.get_conflicts()
if conflicts:
    for slot, pairs in conflicts.items():
        winner_pet, winner = pairs[0]
        for loser_pet, loser in pairs[1:]:
            print(f"  [CONFLICT] {slot}: '{winner.name}' ({winner_pet.name}) takes priority over '{loser.name}' ({loser_pet.name})")
else:
    print("  No conflicts found.")

# --- Today's schedule ---
print("\n" + "=" * 50)
print(scheduler.get_summary())
