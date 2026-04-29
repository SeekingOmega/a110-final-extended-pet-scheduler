import json
from pawpal_system import Owner, Pet, Task
from data_io import export_data, import_data


def _sample_owner_and_pets():
    pet = Pet(name="Mochi", species="cat", age=3, special_needs="")
    pet.add_task(Task(name="Feeding", duration=5, priority="high", frequency="daily", time="07:00"))
    owner = Owner(name="Jordan", available_time=60)
    return owner, [pet]


def test_export_data_produces_valid_json():
    owner, pets = _sample_owner_and_pets()
    result = export_data(owner, pets)
    parsed = json.loads(result)
    assert parsed["owner"]["name"] == "Jordan"
    assert len(parsed["pets"]) == 1
    assert parsed["pets"][0]["name"] == "Mochi"
    assert len(parsed["pets"][0]["tasks"]) == 1


def test_import_data_restores_owner_and_pets():
    owner, pets = _sample_owner_and_pets()
    json_str = export_data(owner, pets)
    restored_owner, restored_pets, _, _ = import_data(json_str)
    assert restored_owner.name == "Jordan"
    assert restored_owner.available_time == 60
    assert len(restored_pets) == 1
    assert restored_pets[0].name == "Mochi"


def test_import_data_restores_tasks():
    owner, pets = _sample_owner_and_pets()
    _, restored_pets, _, _ = import_data(export_data(owner, pets))
    task = restored_pets[0].tasks[0]
    assert task.name == "Feeding"
    assert task.duration == 5
    assert task.priority == "high"
    assert task.frequency == "daily"
    assert task.time == "07:00"


def test_roundtrip_preserves_multiple_pets():
    pet1 = Pet(name="Mochi", species="cat", age=3)
    pet2 = Pet(name="Buddy", species="dog", age=5, special_needs="joint supplements")
    pet2.add_task(Task(name="Walk", duration=30, priority="high", frequency="daily"))
    owner = Owner(name="Jordan", available_time=90)
    _, restored, _, _ = import_data(export_data(owner, [pet1, pet2]))
    assert len(restored) == 2
    assert restored[0].name == "Mochi"
    assert restored[1].special_needs == "joint supplements"
    assert restored[1].tasks[0].name == "Walk"


def test_completed_field_roundtrips():
    pet = Pet(name="Rex", species="dog", age=2)
    task = Task(name="Bath", duration=20, priority="low", frequency="weekly", completed=True)
    pet.add_task(task)
    owner = Owner(name="Sam", available_time=120)
    _, restored, _, _ = import_data(export_data(owner, [pet]))
    assert restored[0].tasks[0].completed is True


def test_active_hours_roundtrip():
    owner, pets = _sample_owner_and_pets()
    json_str = export_data(owner, pets, active_start="08:00", active_end="21:00")
    _, _, active_start, active_end = import_data(json_str)
    assert active_start == "08:00"
    assert active_end == "21:00"
