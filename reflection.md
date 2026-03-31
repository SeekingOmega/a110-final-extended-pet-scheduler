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
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
