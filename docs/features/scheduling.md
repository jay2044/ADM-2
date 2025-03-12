# Scheduling in ADM-2

## Overview
**ADM-2** is a dynamic scheduling engine designed to intelligently plan your day based on task priorities, effort levels, deadlines, and personal preferences. Unlike traditional to-do list apps, ADM-2 doesn't just create a static schedule — it **adapts in real-time** as tasks are completed, delayed, or reprioritized.

ADM-2 leverages an advanced **constraint-based scheduling system** and a **task rating algorithm** to handle complex scheduling scenarios. Tasks are broken into chunks and placed into time blocks based on a combination of user-defined rules, real-world constraints, and dynamic adjustments.

---

## Scheduling Components
### 1. Task Attributes
Each task in ADM-2 is defined by a rich set of attributes that influence how it is scheduled. These attributes are combined to calculate a task's **global weight** — a measure of the task’s overall importance and scheduling urgency.

| **Attribute** | **Description** |
|--------------|-----------------|
| **Priority** | Higher-priority tasks are scheduled before lower-priority ones. |
| **Due Date** | Tasks with closer due dates are weighted more heavily. |
| **Effort Level** | High-effort tasks are scheduled during peak productivity hours. |
| **Flexibility** | Flexible tasks are scheduled in off-peak hours or open blocks. |
| **Time Estimate** | Determines how much space the task will require in the schedule. |
| **Preferred Workdays** | Tasks are scheduled on the user's preferred workdays when possible. |
| **Recurrence** | Recurring tasks are automatically rescheduled according to user-defined patterns. |
| **Manual vs. Auto Chunking** | Tasks can be split into smaller chunks or scheduled as a whole. |
| **Time-of-Day Preference** | Tasks can be scheduled at specific times based on user preference. |
| **Added Date** | Older tasks are given higher urgency over time. |

---

### 2. Time Blocks
A **time block** is a fixed period in the schedule where tasks are placed. Tasks are assigned to time blocks based on size, priority, and scheduling rules.

**Types of Time Blocks:**
- **User-Defined Blocks** – Custom blocks created by the user (e.g., "Workout Time").  
- **System-Defined Blocks** – Open blocks automatically created by ADM-2 to fill gaps between user-defined blocks.  
- **Unavailable Blocks** – Fixed blocks where no scheduling is allowed (e.g., sleep, travel).  

**Example:**
- Morning Workout → 6:00 AM – 7:00 AM (User-defined)  
- Study Session → 9:00 AM – 11:00 AM (User-defined)  
- Open Block → 11:00 AM – 1:00 PM (System-defined)  
- Sleep → 10:00 PM – 6:00 AM (Unavailable)  

ADM-2 maintains a list of time blocks for each day. The system automatically determines which tasks can be placed into which blocks based on their size, priority, and other constraints.

---

### 3. Day Schedule
A **Day Schedule** is a single day’s structured plan, consisting of:
- A **start time** – Defined by the user (e.g., 4:00 AM).  
- An **end time** – Adjusted based on sleep duration and user preferences.  
- A list of **time blocks** – User-defined, system-defined, and unavailable blocks.  

**Example Day Schedule:**  

| **Start Time** | **End Time** | **Type** | **Task(s)** |
|---------------|-------------|----------|-------------|
| 6:00 AM       | 7:00 AM     | User-Defined | Workout         |
| 7:00 AM       | 9:00 AM     | Open Block   | Available for scheduling |
| 9:00 AM       | 11:00 AM    | User-Defined | Study           |
| 11:00 AM      | 1:00 PM     | Open Block   | Available for scheduling |
| 10:00 PM      | 6:00 AM (next day) | Unavailable   | Sleep            |  

ADM-2 fills open blocks with tasks based on calculated task ratings and available time.

---

## Scheduling Algorithm
### Step 1: Task Weighting
Before scheduling begins, ADM-2 assigns each task a **global weight**. This weight determines how important a task is relative to others.

The global weight is calculated using the following formula:

<pre>
W = αP + β(1/D) + γF + δ(A/Mₐ) + εE + ζ(T/Mₜ) + η(L/T) + Q + M
</pre>

Where:  
- **P** = Priority  
- **D** = Days until due date (smaller = more urgent)  
- **F** = Flexibility (Strict = 0, Flexible = 1, Very Flexible = 2)  
- **A** = Days since task was added  
- **Mₐ** = Maximum days since task was added across all tasks  
- **E** = Effort level (Low = 1, Medium = 2, High = 3)  
- **T** = Task time estimate  
- **Mₜ** = Maximum task time estimate  
- **L** = Logged time on task  
- **Q** = Quick task weight  
- **M** = Manual scheduling weight
---

### Step 2: Time Block Rating
Once a task’s global weight is calculated, ADM-2 computes how suitable each time block is for the task using the **Time Block Rating Algorithm**:

<pre>
R = A + B + C + D + E + F + G + H
</pre>

Where:  
- **A** = Due Date Influence → Tasks with closer due dates are preferred.  
- **B** = Added Date Influence → Tasks added earlier are preferred.  
- **C** = Priority → Higher-priority tasks are preferred.  
- **D** = Flexibility → Less flexible tasks are preferred for early scheduling.  
- **E** = Days from Today → Tasks scheduled closer to today are preferred.  
- **F** = Preferred Workdays → Tasks are more likely to be scheduled on preferred days.  
- **G** = Time of Day Preferences → Tasks are scheduled in preferred time periods.  
- **H** = Effort Level → High-effort tasks are preferred during peak productivity hours.  

**Example:**  
- Task priority = 8  
- Due date = Tomorrow  
- Flexibility = Strict  
- Preferred time of day = Morning  
- Effort level = High  

A high-effort task due tomorrow will receive a high rating for a morning peak block — making it likely to be scheduled there.

---

### Step 3: Constraint Satisfaction
ADM-2 uses a **constraint satisfaction solver** to place tasks in time blocks while respecting the following constraints:
1. **Capacity Constraint** – Total task duration in a block cannot exceed available time.  
2. **Priority Constraint** – High-priority tasks are scheduled first.  
3. **Flexibility Constraint** – Strict tasks cannot be rescheduled.  
4. **Manual Override** – User-scheduled tasks cannot be moved unless explicitly allowed.  
5. **Conflict Resolution** – Overlapping tasks are automatically rescheduled.  

---

### Step 4: Objective Function  
The goal of the solver is to **maximize the total task rating** across all scheduled tasks:

<pre>
max ∑(c, b) R₍c,b₎ · alloc₍c,b₎ - Pₘ · Uₘ - Pₐ · Uₐ
</pre>

Where:  
- **R₍c,b₎** = Task rating for chunk `c` in block `b`  
- **Pₘ** = Penalty for unscheduled manual tasks  
- **Pₐ** = Penalty for unscheduled auto tasks  
- **Uₘ**, **Uₐ** = Unscheduling penalties  

---

### Step 5: Dynamic Rebalancing
Once the schedule is generated:
- If a task is completed early → Remaining time is reallocated to other tasks.  
- If a new task is added → Schedule rebalances automatically.  
- If a task runs over time → Conflicting tasks are shifted to open blocks.  

---