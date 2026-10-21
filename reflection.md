# PawPal+ Project Reflection

## 1. System Design

Users need to be able to create and plan tasks, make restraints for the plans such as time constraints and task overlaps, and the users need to be able to generate a schedule based off of the plans provided.

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

PawPal+ is built from four classes. Task represents a single care activity, holding its title, category, duration, priority, due time, frequency and completion status, and it can mark itself complete, reschedule, or check whether it's overdue. Pet represents one animal and owns its list of tasks, with methods to add, remove and filter them. Owner represents the user, holding their pets and daily time budget, and it gives one combined view of every task across all pets. Scheduler holds the planning logic: it reads the owner's pending tasks, orders them by priority and due time, fits them into the available time, flags conflicts, and explains why each task was placed where it was. Task, Pet and Owner store and manage data, while Scheduler alone makes decisions, so each class has one reason to change.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Task now has a pet back-reference, so the scheduler can still tell which pet a task belongs to after Owner.get_all_tasks() flattens everything into one list. Pet.add_task is meant to set that link. I excluded it from the dataclass repr and compare, because otherwise printing a pet would loop forever (Pet → Task → Pet …). Task.due_time became a full datetime called due, because a bare time of day can't express weekly recurrence, overdue checks, or scheduling for a specific date. priority, category and frequency are now enums (Priority as an IntEnum so HIGH > LOW sorts naturally), which makes a typo like "daily " fail loudly instead of silently breaking recurrence. I added a ScheduledItem dataclass (task, start, end, reason, plus an overlaps() method) to replace the bare (time, Task) tuples. It gives conflict detection real start and end times and gives explain_plan() somewhere to keep each placement's reason. Scheduler.schedule now holds ScheduledItems. I split generate_schedule into private helpers (_collect_pending, _rank, _fit) so each step can be tested separately, and its docstring says to clear schedule and skipped_tasks first, so calling it twice can't produce duplicates.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers the owner's daily time budget, each task's priority, whether it is medication, how overdue it is, its requested time, and how far it can be moved from that time. I treated the time budget and medication as the hard constraints: medication tasks are always scheduled, even if they exceed the budget (with a warning), because skipping a pet's medicine costs more than running over, while every other task has to fit within the minutes available. Priority came next and sets the value of each task, with a bonus for tasks overdue from an earlier day, and a knapsack then picks the most valuable set that fits, so important work wins over low-priority filler. Requested times came last as a soft preference: tasks keep their time when it is free, shift to the next open slot when it is not, and are reported as unplaced if they would move more than 60 minutes, since a plan that quietly buries a task hours from its time is worse than saying it didn't fit.


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

One of the tradeoffs is that the tasks that are deemed "Mandatory" are not manual even though somethings in reality have the same level of importance it can be overlooked on rare occasions. This tradeoff is reasonable as it should properly schedule the mandatory tasks to be done at reasonable times compared to the other tasks, so it shouldn't be something that we would have to worry about.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

The AI tools helped a lot when it came to breaking down the logic and creating skeleton as well as the implementation of methods. It helped me figure out bottlenecks and areas where more clarification as well as additional information was needed. It also was able to refactor the initial uml logic adjusting to new changes and finding gaps in the flow of data which we were able to fix. The prompts that helped the most was the implementation of methods and creation the uml logic as it thought of things I couldn't in very little time allowing me to tackle the code faster than if I were working without it.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

There wasn't a time where I had to reject the AI suggestion, however there was a few times where I had to go back and refactor the flow of data to make it clearer. I evaluated it by examining the flow of data and ensuring that everything made sense and that all methods had enough information to correctly execute it's purpose.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

We tested time conflictions and priorities. These tests are important as we need to ensure that the schedule is logically correct and actually usable to the user, as well as ensuring that we get high priority tasks done correct. This is for the usablility of the app as well as the safety of the pet.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I believe that the scheuler works very well as I did enough testing the ensure that everything works properly from a basic user's perspective. Some edge cases I would want to try more is having a lot of pets and possibly overlapping name and identity of pets.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I am satisfied with how the scheduler deals with the tasks when it comes to marking it complete as well as building the schedule with them.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I could improve the overall look of the webapp as I left it very plain.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

It is very important to go back and refactor the logic of code and have multiple iterations of it if needed. Knowing that not each attempt at creating an app will be successful and not knowing the flow of data on the first try is very important. AI is also really good at helping you trouble shoot and find holes that need to be filled within the code even if it wrote the code itself.