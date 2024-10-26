### Advanced Task:

1. **Title**: The name of the task, defining its main purpose.
2. **Description**: Additional details or instructions for the task.
3. **Due Date and Time**: Set deadlines in `YYYY-MM-DD` and `HH:MM` format, respectively, to track task timelines.
4. **Priority Level**: A numeric or labeled level to signify the task's importance (`Urgent`, `High`, `Medium`, `Low`).
5. **Importance Flag**: A boolean attribute to mark a task as important.
6. **Status**: The current state of the task (e.g., `Not Started`, `In Progress`, `Completed`, `Failed`, `On Hold`).
7. **Recurring Setting**: A boolean to indicate if the task repeats, with an interval attribute (daily, weekly, etc.)
   defining recurrence frequency.
8. **Category**: Tags or labels (like `Work`, `Personal`, `Urgent`) to organize tasks into groups.
9. **Last Completed Date**: Tracks the last time a recurring task was completed.
10. **Estimate**: An estimation of time needed to complete the task (in hours or days).
11. **Count/Increment Requirement**: A counter that tracks the number of actions or subtasks completed toward the task’s
    goal (e.g., “5/10 actions completed”).
12. **Progress Tracker**: An attribute that calculates and stores progress as a percentage, based on completed actions,
    subtasks, or time logged.
13. **Subtasks**: A list of smaller tasks associated with the main task. Each subtask can have its own title, status,
    and deadline.
14. **Dependencies**: A list of other tasks that must be completed before this task can begin, useful for project-based
    workflows.
15. **Deadline Flexibility**: An attribute (like `Strict` or `Flexible`) to indicate if the task deadline can adjust
    based on dependency delays.
16. **Effort Level**: Labels (like `Easy`, `Medium`, `Hard`) indicating task difficulty.
17. **Resource Links/Attachments**: URLs, file paths, or references to materials required for task completion.
18. **Notes/Comments**: A free-text field for any extra details, updates, or session notes.
19. **Time Logged**: A tracker for actual hours spent on the task, compared against the estimate to monitor time usage.
20. **Recurring Subtasks**: Smaller, regularly recurring tasks within a larger task for consistent updates or checks.
21. **Priority Weighting**: A dynamic calculation adjusting the priority based on due dates, dependencies, and estimated
    completion time.