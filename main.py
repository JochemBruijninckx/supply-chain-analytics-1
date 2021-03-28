from Problem import Problem, gen_instance
from Solver import *
import winsound

# Task to run
# --------------------------------------------------------------------------------------
instance_name = 'random_data_set_small'   # Enter a number to generate a random instance
method = 'heuristic'                     # Options are 'read', 'solve', 'heuristic'
seed = 700                          # Seed is used when generating scenarios

# Task settings (only used if method is 'heuristic')
# --------------------------------------------------------------------------------------
create_initial_solution = True          # If False, the initial solution is loaded from an existing file
evaluation_scenarios = 100              # Number of scenarios to run in Monte Carlo evaluation
extra_time_periods = False              # If set to True, the model uses 10% extra time periods
heuristic_settings = {
    'heuristic_scenarios': 25,          # Number of scenarios to use in the SAA-models in our heuristic
    'model_parameters': {
        'boundary': 2.5,                # B
        'delta': 0.25,                  # Delta_B
    },
    'step_1': {
        'epsilon': 0.001,               # Optimality gap stopping criterion for Step 1
        'time': 99999,
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
if instance_name not in ['small_data_set', 'large_data_set', 'random_data_set', 'random_data_set_small']:
    # This function can be called to generate an .xlsx instance file
    gen_instance(seed=int(instance_name),
                 num_s=6,
                 num_d=6,
                 num_c=12,
                 num_p=1,
                 T=20)
    instance_name = str(instance_name)

# Check if we are dealing with a random data set
random = instance_name in ['random_data_set', 'random_data_set_small']
if not random:
    seed = None

# Read and create problem
problem = Problem(instance_name, random=random, seed=seed, extra_time_periods=extra_time_periods)

# Solve it using the heuristic and display the solution
if method == 'read':
    problem.read_solution(instance_name)
elif method == 'solve':
    problem = solve(problem)
elif method == 'heuristic':
    problem = heuristic(problem, heuristic_settings, create_initial_solution)

# Log functions for solution
# --------------------------------------------------------------------------------------
if not problem.random:
    problem.log_objective(summary_only=True)
problem.display(integer=True)

# Run Monte Carlo performance analysis
if random:
    M = evaluation_scenarios
    performance_analysis(problem, M)
    monte_carlo_histogram(problem, M)

input('Press enter to exit..')
