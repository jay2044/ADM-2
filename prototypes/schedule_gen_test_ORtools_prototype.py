from ortools.sat.python import cp_model
from datetime import datetime, time

# --- Scale factor ---
# We use a scale factor to convert fractional hours into integer units.
# The CP-SAT solver works best with integers.
scale = 10  # For example, 3.5 hours becomes 35 units.

# --- Data Setup ---
# The days_list defines our scheduling days and the available time blocks.
days_list = [
    {
        "date": "2025-03-10",               # Date for this schedule
        "buffer_ratio": 0.15,               # Fraction of time reserved as buffer
        "reserved_time": 1.0,               # Reserved time in hours (not used directly here)
        "time_blocks": [
            {
                "id": 101,                # Unique ID for this time block
                "name": "Morning Unscheduled",  # Descriptive name
                "block_type": "system_defined", # Type of block
                "start_time": "04:00",     # Start time of the block
                "end_time": "09:00",       # End time of the block
                "duration": 5.0,           # Total duration in hours (5 hours)
                "buffer_ratio": 0.15,      # 15% of the block is reserved as buffer (unavailable)
                "task_chunks": []          # List where assigned tasks will be stored
            }
        ]
    },
    {
        "date": "2025-03-11",
        "buffer_ratio": 0.10,
        "reserved_time": 0.5,
        "time_blocks": [
            {
                "id": 201,
                "name": "Morning Unscheduled",
                "block_type": "system_defined",
                "start_time": "04:00",
                "end_time": "08:00",
                "duration": 4.0,           # 4 hours duration
                "buffer_ratio": 0.10,      # 10% buffer
                "task_chunks": []
            }
        ]
    }
]

# The chunks_list contains the tasks that need scheduling.
# Each chunk now has a "min_size" and a "max_size" (both in hours) that define
# the smallest and largest amount that can be scheduled in one time block.
# "chunk_type" is set to "auto" (i.e. splittable) in this example.
chunks_list = [
    {
        "id": "chunk_A1",           # Unique identifier for this chunk
        "task": {},                 # Task details (omitted for simplicity)
        "chunk_type": "auto",       # "auto" means the chunk can be split among blocks
        "unit": "time",
        "size": 3.5,                # Total size in hours
        "min_size": 0.5,            # Minimum allocation allowed per block (hours)
        "max_size": 2.0,            # Maximum allocation allowed per block (hours)
        "timeblock_ratings": [],    # Placeholder for ratings (if provided per block)
        "is_recurring": False,
        "status": "active",
        "task_global_rating": 0.25  # Global rating: higher means higher priority
    },
    {
        "id": "chunk_B1",
        "task": {},
        "chunk_type": "auto",       # You could mark some as "manual" if they must be unsplit
        "unit": "time",
        "size": 2.0,
        "min_size": 2.0,            # For this chunk, min_size equals full size → unsplittable
        "max_size": 2.0,            # Maximum equals full size
        "timeblock_ratings": [],
        "is_recurring": False,
        "status": "active",
        "task_global_rating": 0.20
    },
    {
        "id": "chunk_C1",
        "task": {},
        "chunk_type": "auto",
        "unit": "time",
        "size": 3.0,
        "min_size": 1.0,            # At least 1 hour must be allocated when splitting
        "max_size": 2.5,            # No more than 2.5 hours can be allocated in a single block
        "timeblock_ratings": [],
        "is_recurring": False,
        "status": "active",
        "task_global_rating": 0.30
    },
    {
        "id": "chunk_D1",
        "task": {},
        "chunk_type": "auto",
        "unit": "time",
        "size": 1.0,
        "min_size": 1.0,            # Since size equals min_size, it must be scheduled whole if used
        "max_size": 1.0,
        "timeblock_ratings": [],
        "is_recurring": False,
        "status": "active",
        "task_global_rating": 0.35
    }
]

# --- Dummy Settings and Rating Function ---
# These are placeholders for more complex settings and rating logic.
# The rating function uses the chunk's global rating and the time block's capacity.
class ScheduleSettings:
    def __init__(self):
        self.peak_productivity_hours = (time(17, 0), time(19, 0))
        self.off_peak_hours = (time(22, 0), time(6, 0))

settings = ScheduleSettings()

class TaskManager:
    def get_task_list_category_name(self, list_name):
        # Return a dummy category name.
        return "test"

task_manager = TaskManager()

def calculate_rating(chunk, timeblock, day_date, settings, task_manager):
    # Calculate a simple rating for a chunk in a given time block.
    # The available capacity of the block is (duration * (1 - buffer_ratio)).
    capacity = timeblock["duration"] * (1 - timeblock["buffer_ratio"])
    # The rating is based on the chunk's global rating plus a bonus from the capacity ratio.
    # Higher capacity relative to chunk size gives a bonus.
    return int(chunk["task_global_rating"] * 100 + 50 * min(1, capacity / chunk["size"]))

# --- Preprocessing: Build Allowed Assignments and Capacity ---
# Determine which chunks can be assigned to which blocks and compute each block's capacity.
allowed_assignments = {}  # Key: (chunk_id, block_id); Value: dict with 'rating' and full chunk size in scaled units.
block_capacity = {}       # Key: block_id; Value: capacity in scaled units.

# Loop over each day.
for day in days_list:
    # Convert the date string to a date object.
    day_date = datetime.strptime(day["date"], "%Y-%m-%d").date()
    # Loop over the time blocks in the day.
    for block in day["time_blocks"]:
        if block["block_type"] == "unavailable":
            continue  # Skip blocks that are not available.
        # Compute available capacity: duration multiplied by (1 - buffer_ratio).
        cap = block["duration"] * (1 - block["buffer_ratio"])
        # Scale the capacity to integer units.
        block_capacity[block["id"]] = int(cap * scale + 0.5)
        # For each chunk, assume it can be scheduled in this block.
        for chunk in chunks_list:
            # Calculate the rating for this (chunk, block) pair.
            rating = calculate_rating(chunk, block, day_date, settings, task_manager)
            # Save the allowed assignment info, including the full weight (scaled).
            allowed_assignments[(chunk["id"], block["id"])] = {
                "rating": rating,
                "full_weight": int(chunk["size"] * scale + 0.5)
            }

# --- CP-SAT Model ---
# Create a new model.
model = cp_model.CpModel()

# --- Decision Variables ---
# For each allowed (chunk, block) pair, we create:
#   - assign[(i, j)]: a binary variable (1 if some portion of chunk i is assigned to block j).
#   - alloc[(i, j)]: an integer variable representing how many scaled units of chunk i are allocated to block j.
assign = {}
alloc = {}

for (c_id, b_id), data in allowed_assignments.items():
    # Create the binary decision variable.
    assign[(c_id, b_id)] = model.NewBoolVar(f"assign_{c_id}_{b_id}")
    # Create the allocation variable, with an upper bound equal to the full weight (scaled).
    full_weight = data["full_weight"]
    alloc[(c_id, b_id)] = model.NewIntVar(0, full_weight, f"alloc_{c_id}_{b_id}")

# --- Unscheduled Variables ---
# These variables capture any part of a chunk that is not scheduled.
# For non-splittable (manual) chunks, we use a binary variable.
# For splittable (auto) chunks, we use an integer variable (in scaled units).
unsched_manual = {}
unsched_auto = {}

# We also record each chunk's full weight (scaled) and, for auto chunks, the minimum and maximum allocations per block.
chunk_weight = {}
chunk_min = {}  # Minimum allocation per block (scaled) for auto chunks.
chunk_max = {}  # Maximum allocation per block (scaled) for auto chunks.

for chunk in chunks_list:
    # Scale the total chunk size.
    w = int(chunk["size"] * scale + 0.5)
    chunk_weight[chunk["id"]] = w
    if chunk["chunk_type"] == "auto":
        # Scale the minimum size. Use default 0.5 if not provided.
        m = int(chunk.get("min_size", 0.5) * scale + 0.5)
        chunk_min[chunk["id"]] = m
        # Scale the maximum size. If not provided, default to full size.
        M = int(chunk.get("max_size", chunk["size"]) * scale + 0.5)
        chunk_max[chunk["id"]] = M

# Create unscheduled variables based on chunk type.
for chunk in chunks_list:
    if chunk["chunk_type"] == "manual":
        # For manual chunks, unscheduled is a binary flag (1 means not scheduled anywhere).
        unsched_manual[chunk["id"]] = model.NewBoolVar(f"unsched_{chunk['id']}")
    else:
        # For auto chunks, unscheduled is an integer variable (units left unscheduled).
        unsched_auto[chunk["id"]] = model.NewIntVar(0, chunk_weight[chunk["id"]], f"unsched_{chunk['id']}")

# --- Constraints ---

# (1) Full Allocation Constraints:
# For each chunk, the sum of allocations over all blocks plus any unscheduled amount must equal the full chunk weight.
# For manual chunks, the chunk must be fully assigned in one block or marked unscheduled.
for chunk in [c for c in chunks_list if c["chunk_type"] == "manual"]:
    possible_assignments = []
    for (cid, b_id) in assign:
        if cid == chunk["id"]:
            possible_assignments.append(assign[(cid, b_id)])
            # If assigned to a block, then allocation must equal the full chunk weight.
            model.Add(alloc[(cid, b_id)] == chunk_weight[chunk["id"]]).OnlyEnforceIf(assign[(cid, b_id)])
            # Otherwise, no allocation is made.
            model.Add(alloc[(cid, b_id)] == 0).OnlyEnforceIf(assign[(cid, b_id)].Not())
    # Ensure that the chunk is assigned exactly once or left unscheduled.
    model.Add(sum(possible_assignments) + unsched_manual[chunk["id"]] == 1)

# For auto (splittable) chunks, the sum of allocations across all blocks plus unscheduled units equals the full weight.
# Also, for each assignment, if it is made, the allocation must be between the min and max allowed.
for chunk in [c for c in chunks_list if c["chunk_type"] == "auto"]:
    possible_allocs = []
    for (cid, b_id) in alloc:
        if cid == chunk["id"]:
            # Enforce a minimum allocation if this assignment is made.
            m = chunk_min[chunk["id"]]
            model.Add(alloc[(cid, b_id)] >= m).OnlyEnforceIf(assign[(cid, b_id)])
            # Enforce a maximum allocation if this assignment is made.
            M = chunk_max[chunk["id"]]
            model.Add(alloc[(cid, b_id)] <= M).OnlyEnforceIf(assign[(cid, b_id)])
            # If not assigned, then allocation must be zero.
            model.Add(alloc[(cid, b_id)] == 0).OnlyEnforceIf(assign[(cid, b_id)].Not())
            possible_allocs.append(alloc[(cid, b_id)])
    model.Add(sum(possible_allocs) + unsched_auto[chunk["id"]] == chunk_weight[chunk["id"]])
    # Note: The flexibility of splitting is inherent in allowing multiple assignments
    # that each must satisfy the min and max limits.

# (2) Capacity Constraints:
# The total allocated units in each time block must not exceed its available capacity.
for day in days_list:
    for block in day["time_blocks"]:
        if block["block_type"] == "unavailable":
            continue  # Skip blocks that are not available.
        b_id = block["id"]
        allocs_in_block = []
        for (cid, bid) in alloc:
            if bid == b_id:
                allocs_in_block.append(alloc[(cid, bid)])
        model.Add(sum(allocs_in_block) <= block_capacity[b_id])

# (3) Feasibility Constraints:
# Our allowed_assignments dictionary ensures we only create variables for valid (chunk, block) pairs.
# Thus, no extra feasibility constraints are needed here.

# (4) Priority / Reallocation Consideration (Note):
# The objective function already factors in a rating that uses the task's global rating.
# Thus, chunks with higher global weight (importance) produce a higher contribution to the objective.
# This naturally incentivizes the solver to schedule those tasks.
# If a task with a high rating is competing for space with a lower rated task in the same block,
# the solver will tend to “bump” the lower rated task (i.e. leave it unscheduled or split it)
# in order to maximize the overall objective.
# More advanced reallocation logic (e.g., reified constraints for swapping) can be added if needed.

# --- Objective Function ---
# Our goal is to maximize the total rating (which factors in global importance) from all allocations
# while penalizing any unscheduled portions.
penalty_manual = 100  # Penalty for each unscheduled manual chunk (a high value discourages unscheduling)
penalty_auto = 100    # Penalty per unit (scaled) unscheduled for auto chunks

objective_terms = []

# For each allowed (chunk, block) pair, add its contribution (rating * allocation).
for (c_id, b_id), var in alloc.items():
    rating = allowed_assignments[(c_id, b_id)]["rating"]
    objective_terms.append(rating * var)

# Subtract penalty terms for unscheduled work.
for chunk in [c for c in chunks_list if c["chunk_type"] == "manual"]:
    objective_terms.append(-penalty_manual * unsched_manual[chunk["id"]])
for chunk in [c for c in chunks_list if c["chunk_type"] == "auto"]:
    objective_terms.append(-penalty_auto * unsched_auto[chunk["id"]])

# Set the objective to maximize the total benefit.
model.Maximize(sum(objective_terms))

# --- Solve the Model ---
# Create a solver instance and solve the model.
solver = cp_model.CpSolver()
status = solver.Solve(model)

# --- Reporting the Results ---
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("Solution found:")
    # Report results for manual chunks.
    for chunk in [c for c in chunks_list if c["chunk_type"] == "manual"]:
        assigned = False
        for (cid, b_id) in assign:
            if cid == chunk["id"] and solver.Value(assign[(cid, b_id)]) == 1:
                # Convert allocation from scaled units back to hours.
                allocated_hours = solver.Value(alloc[(cid, b_id)]) / scale
                print(f"Manual Chunk {cid} assigned fully to Block {b_id} (allocated {allocated_hours:.2f} hours)")
                assigned = True
        if not assigned and solver.Value(unsched_manual[chunk["id"]]) == 1:
            print(f"Manual Chunk {chunk['id']} is UNSCHEDULED.")
    # Report results for auto chunks.
    for chunk in [c for c in chunks_list if c["chunk_type"] == "auto"]:
        total_assigned = 0
        for (cid, b_id) in assign:
            if cid == chunk["id"]:
                alloc_val = solver.Value(alloc[(cid, b_id)])
                if solver.Value(assign[(cid, b_id)]) == 1 and alloc_val > 0:
                    print(f"Auto Chunk {cid} assigned {alloc_val / scale:.2f} hours to Block {b_id}")
                    total_assigned += alloc_val
        unsched_amt = solver.Value(unsched_auto[chunk["id"]])
        if unsched_amt > 0:
            print(f"Auto Chunk {chunk['id']} UNSCHEDULED for {unsched_amt / scale:.2f} hours")
    print("Objective value:", solver.ObjectiveValue())
else:
    print("No solution found.")
