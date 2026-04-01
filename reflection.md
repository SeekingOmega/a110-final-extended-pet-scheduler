# PawPal+ Project Reflection

## 1. System Design

**3 core actions for the app:**
- add a pet: name, type, age, and any special needs/preferences
- schedule tasks: walks, feeding, meds, enrichment, grooming, etc. with duration and priority
- create a daily plan based on the tasks and constraints

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

4 classes with minimal attributes:
Pet: name, species, age, special_needs
Owner: name, available_time, preferences
Task: name, duration, priority
Scheduler: tasks, constraints + generate_plan() method
Relationships:
Owner → owns → Pet
Owner → uses → Scheduler
Scheduler → schedules → Task (one-to-many)

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
Yes I did. The UML says Owner owns Pet, but neither class holds a reference to the other at first. The Scheduler has no way to know whose pet it's planning for, or respect that pet's special_needs.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

1. **Available time**: the owner's total minutes per day is the hard cap. Tasks are added greedily until no more fit.
2. **Priority**: tasks are sorted `high → medium → low` before scheduling. A lower-priority task never bumps a higher-priority one, even if it would fit in the remaining time.
3. **Time slot conflicts**: if two tasks share the same scheduled time (`HH:MM`), only the higher-priority one is scheduled. The other is omitted regardless of whether there's time left in the day.
4. **Completion status**: is also checked: already-completed tasks are excluded from the plan entirely before any of the above logic runs.

- How did you decide which constraints mattered most?
Priority was chosen as the primary constraint because pet care tasks have real urgency differences.

Available time was kept as a hard cap (not a soft suggestion) because the whole point of the scheduler is to produce a realistic plan the owner can actually do in a day.

Time slot conflicts were added last and treated as a secondary constraint. They only apply when the owner has explicitly assigned a time to a task. If no time is set, tasks don't conflict, which keeps the scheduler usable even with minimal input.

Owner `preferences` and pet `special_needs` are stored on the objects but intentionally left out of the scheduling logic for now. They're data the UI could use to guide the owner, but considering them in the schedule would require more complex logic and tradeoffs that takes too much time to implement right now.


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**Tradeoff 1: Exact time match instead of overlap detection**

The scheduler flags a conflict only when two tasks share the exact same `HH:MM` string. It does not check whether a 30-minute task starting at `08:00` actually overlaps with a 20-minute task starting at `08:15`. True overlap detection would require comparing start time + duration against every other task's window, which is significantly more complex to implement.

This is reasonable for a class project because the scheduler's primary goal is demonstrating priority-based planning, not building a calendar engine. In practice, owners can avoid overlap by being mindful when entering times, and the conflict warning still catches the most obvious case.

---

**Tradeoff 2: Available time is treated as a single daily pool, not per-day**

The scheduler draws from `owner.available_time` as one flat budget and fills it greedily. If tasks have different `due_date` values spanning multiple days, the scheduler may mix them into one plan — e.g., a task due today and a task due next week could both be scheduled as long as there's no time conflict and the budget allows. This doesn't make real-world sense since 60 free minutes on Monday doesn't carry over to Tuesday.

This is reasonable because implementing per-day bucketing would require grouping tasks by date, running the scheduling algorithm separately for each day, and presenting a multi-day view — a much larger feature. For a class project demonstrating the core scheduling concept, a single-day budget is a clean and understandable simplification.

---

**Tradeoff 3: Greedy priority scheduling with no backtracking**

The scheduler picks tasks in priority order and adds each one if it fits in the remaining time. It never backtracks — so if a 25-minute high-priority task is added and only 20 minutes remain, a 20-minute medium-priority task that would have fit perfectly is skipped, even though swapping them would result in a fuller schedule.

This is reasonable because greedy scheduling is simple to understand and explain, which matters in a class project. Optimal bin-packing with backtracking is an NP-hard problem. The greedy approach favors correctness of priority ordering over maximizing time utilization, which aligns with the app's stated goal: important tasks should always come first.


---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
