"""Import/export owner profile (pets + tasks) as JSON."""
import json
from pawpal_system import Owner, Pet, Task


def export_data(owner: Owner, pets: list[Pet], active_start: str = "", active_end: str = "") -> str:
    """Serialize owner + pets + tasks to a JSON string."""
    return json.dumps(
        {
            "owner": {
                "name":               owner.name,
                "available_time":     owner.available_time,
                "active_hours_start": active_start,
                "active_hours_end":   active_end,
            },
            "pets": [
                {
                    "name":          p.name,
                    "species":       p.species,
                    "age":           p.age,
                    "special_needs": p.special_needs,
                    "tasks": [
                        {
                            "name":      t.name,
                            "duration":  t.duration,
                            "priority":  t.priority,
                            "frequency": t.frequency,
                            "time":      t.time,
                            "due_date":  t.due_date,
                            "completed": t.completed,
                        }
                        for t in p.tasks
                    ],
                }
                for p in pets
            ],
        },
        indent=2,
    )


def import_data(json_str: str) -> tuple[Owner, list[Pet], str, str]:
    """Deserialize a JSON string. Returns (owner, pets, active_start, active_end)."""
    data = json.loads(json_str)
    try:
        owner_data = data["owner"]
        owner = Owner(
            name=owner_data["name"],
            available_time=owner_data["available_time"],
        )
    except KeyError as e:
        raise ValueError(f"Invalid export data: missing required field {e}") from e
    active_start = owner_data.get("active_hours_start", "")
    active_end   = owner_data.get("active_hours_end",   "")
    pets = []
    for pet_data in data.get("pets", []):
        pet = Pet(
            name=pet_data["name"],
            species=pet_data["species"],
            age=pet_data["age"],
            special_needs=pet_data.get("special_needs", ""),
        )
        for td in pet_data.get("tasks", []):
            pet.add_task(Task(
                name=td["name"],
                duration=td["duration"],
                priority=td["priority"],
                frequency=td["frequency"],
                time=td.get("time", ""),
                due_date=td.get("due_date", ""),
                completed=td.get("completed", False),
            ))
        pets.append(pet)
    return owner, pets, active_start, active_end
