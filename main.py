from Problem import Problem, gen_instance
from Solver import *
import winsound

# Task to run
# --------------------------------------------------------------------------------------
instance_name = 'small_data_set'  # Enter a number to generate a random instance
method = 'heuristic'                     # Options are 'read', 'solve', 'heuristic'

# Task settings (only used if method is 'heuristic')
# --------------------------------------------------------------------------------------
create_initial_solution = True         # If False, the initial solution is loaded from an existing file
heuristic_settings = {
    'model_parameters': {
        'boundary': 2.5,                # B
        'delta': 0.25,                  # Delta_B
    },
    'step_1': {
        'epsilon': 0.001,               # Optimality gap stopping criterion for Step 1
        'time': 120,
        'surpress_gurobi': False
    },
    'step_2': {
        'start_capacity': 2.5,          # m
        'capacity_step': 0.25           # Delta_m
    },
    'step_3': {
        'check_full_list': False        # If True, the best improvement from the entire list is chosen on each iteration
    },
    'step_4': {
        'epsilon': 0.001,               # Optimality gap stopping criterion for Step 4
        'time': 7200,
        'surpress_gurobi': False
    }
}

# Function calls
# --------------------------------------------------------------------------------------
if instance_name not in ['small_data_set', 'large_data_set']:
    # This function can be called to generate an .xlsx instance file
    gen_instance(seed=int(instance_name),
                 num_s=6,
                 num_d=6,
                 num_c=12,
                 num_p=1,
                 T=20)
    instance_name = str(instance_name)

# Read and create problem
problem = Problem(instance_name)

# Solve it using the heuristic and display the solution
if method == 'read':
    problem.read_solution(instance_name)
elif method == 'solve':
    problem = solve(problem)
elif method == 'heuristic':
    problem = heuristic(problem, heuristic_settings, create_initial_solution)

# Log functions for solution
# --------------------------------------------------------------------------------------
problem.log_objective(summary_only=True)
problem.display(integer=True)
input('Press enter to exit..')
