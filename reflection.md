# PawPal+ Project Reflection

## 1. System Design
User should be able to schedule reoccuring monthly vet check ups.
User should be able to see today's task.
User should be able to add a pet.


**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
My initial UML design consists of 4 classes(Owner, Pet, Task, DailyPlan). The design is very simple, the class owner owns pet, the pet has tasks, and the tasks schedules the dailyplan. This flow allows for a simple 4 class diagram. The owner can add and remove pets, as well as retrieve a list of all of the pets. The pet can add and remove tasks, as well as retrieve a list of all tasks. The task schedules the dailyplan and can mark tasks completed and check when it is due and if it is overdue. The dailyplan can format the info need each day by pet and task and sort the tasks into a proper list keeping track of the time and explaining each task.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
No changes currently, only notes of what to keep track of in order for mistakes to not be made.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?
Due dates, priorities (high, medium, low), and category conflicts and time conflicts. I decided which constraints mattered the most by seeing which constraints prohibitted a functioning and logical schedule as a pet owner.
**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
The scheduler strictly prioritizes the priority order even though there might be other optimal schedules. High priority tasks may be scheduled even if a medium task may be a better fit due to the time constraints and how close the tasks may be put together. The tradeoff is reasonable for this scenario as we are simply trying to fit all of the tasks we are trying to get done in a schedule and not taking account the time in between.
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
