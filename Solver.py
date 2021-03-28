import math
import copy
import time
from statistics import stdev

import numpy as np
import matplotlib.pyplot as plt

from Model import Model


# Exact solving of the problem
def solve(problem, settings=None, bounds=None):
    # Create regular model
    model = Model(problem, settings, bounds=bounds)
    model.write(problem.instance_name)
    model.solve(problem.instance_name)
    # Load the solution into our problem object
    problem.read_solution(problem.instance_name)
    return problem


# Heuristic method applied to problem
def heuristic(problem, settings, create_initial_solution=True):
    time_used = []
    # Step 1 - Create or load initial solution.
    # --------------------------------------------------------------------------------------
    start_time = time.time()
    print()
    # Generate new scenario's for Step 1
    if problem.random:
        problem.generate_scenarios(settings['heuristic_scenarios'])
    if create_initial_solution:
        print('Step 1 | Creating initial solution')
        print('-' * 70)
        # Create relaxed version of the model and solve it
        relaxed_model = Model(problem, {
            'all_links_open': True,
            'non_integer_trucks': True,
            'linear_backlog_approx': False,
            'perfect_delivery': False
        }, surpress_logs=settings['step_1']['surpress_gurobi'])
        relaxed_model.write(problem.instance_name + '_relaxed')
        relaxed_model.solve(problem.instance_name + '_relaxed', {
            'gap': settings['step_1']['epsilon'],
            'time': settings['step_1']['time']
        })
    else:
        print('Step 1 | Loading initial solution')
        print('-' * 70)
    # Load the solution into our problem object
    problem.read_solution(problem.instance_name + '_relaxed')
    problem.display()
    end_time = time.time()
    time_used.append(end_time - start_time)
    # Step 2 - Mass link dropping (all low capacity links are removed if improvement found)
    # --------------------------------------------------------------------------------------
    start_time = time.time()
    current_objective = problem.compute_objective()
    original_problem = copy.deepcopy(problem)
    # Try mass link dropping
    print()
    print('Step 2 | Mass link dropping (current objective', str(round(current_objective, 2)) + ')')
    print('-' * 70)
    start_capacity = settings['step_2']['start_capacity']
    capacity_step = settings['step_2']['capacity_step']
    current_capacity = start_capacity
    while current_capacity >= 0:
        step = round((start_capacity - current_capacity) / capacity_step)
        # Create alternative problem in which all low-capacity links are dropped
        alternative_problem = copy.deepcopy(problem)
        drop_links(alternative_problem, current_capacity)
        # Fix the capacity of all remaining links equal to their current value
        v_bounds = get_v_bounds(alternative_problem, method='exact')
        # Construct and solve the alternative model
        alternative_model = Model(alternative_problem, {
            'non_integer_trucks': True,
            'linear_backlog_approx': not problem.random
        }, {'v': v_bounds}, surpress_logs=True, parameters=settings['model_parameters'])
        alternative_objective = alternative_model.solve(problem.instance_name + '_alternative', {
            'bound': current_objective
        })
        # If the solution to the alternative model is an improvement, use it as new starting point (skip to Step 3)
        if alternative_objective < current_objective:
            print('(' + str(step + 1) + '/' + str(round(start_capacity / capacity_step) + 1) + ')',
                  '| Found improvement by dropping all links with capacity <', current_capacity)
            current_objective = alternative_objective
            problem = alternative_problem
            problem.read_solution(problem.instance_name + '_alternative')
            print('New objective |', round(current_objective, 2))
            break
        else:
            print('(' + str(step + 1) + '/' + str(round(start_capacity / capacity_step) + 1) + ')',
                  '| Rejected dropping all links with capacity <', current_capacity)
            current_capacity -= capacity_step
    end_time = time.time()
    time_used.append(end_time - start_time)
    problem.display()
    # Step 3 - Dropping individual links
    # --------------------------------------------------------------------------------------
    start_time = time.time()
    found_improvement = True
    iteration = 0
    print()
    print('Step 3 | Dropping individual links (current objective', str(round(current_objective, 2)) + ')')
    print('-' * 70)
    rejected_links = set()
    while found_improvement:
        iteration += 1
        found_improvement = False
        print('Iteration', iteration, '|')
        # Initialize best link/problem for this iteration
        best_dropped_link = None
        start_objective = current_objective
        alternative_problem = copy.deepcopy(problem)
        sorted_links = get_utilization_costs(alternative_problem)
        for (link_index, dropped_link) in enumerate(sorted_links):
            rejection_reason = ''
            if dropped_link in rejected_links:
                rejection_reason = '(Does not need to be reevaluated)'
                alternative_objective = math.inf
            else:
                # Construct a v_bounds object that will limit our allowed choices of capacity
                v_bounds = get_v_bounds(alternative_problem, method='exact')
                v_bounds[dropped_link] = {'lb': 0, 'ub': 0}
                alternative_destination_links = get_alternative_links(alternative_problem, dropped_link[1],
                                                                      dropped_link)
                # If this link is our only link to a customer, reject dropping it by default
                if alternative_destination_links == [] and dropped_link[1] in alternative_problem.C:
                    rejection_reason = '(Only route to customer)'
                    alternative_objective = math.inf
                else:
                    # Allow for extra capacity to be used on all alternative links to dropped_link's destination
                    for alternative_link in alternative_destination_links:
                        v_bounds[alternative_link].pop('ub')
                    # Construct alternative model using the previously constructed v_bounds and solve it
                    alternative_model = Model(alternative_problem, {
                        'non_integer_trucks': True,
                        'linear_backlog_approx': not problem.random
                    }, {'v': v_bounds}, surpress_logs=True, parameters=settings['model_parameters'])
                    alternative_objective = alternative_model.solve(problem.instance_name + '_alternative', {
                        'bound': start_objective
                    })
            # Check if the alternative capacity procurement leads to an objective improvement
            if alternative_objective < start_objective:
                # Dropping this link is an improvement compared to last iteration
                found_improvement = True
                if alternative_objective < current_objective:
                    # Dropping this link is the best improvement so far
                    current_objective = alternative_objective
                    best_dropped_link = dropped_link
                    problem.read_solution(problem.instance_name + '_alternative')
                    # If we are going to check the full list, simply note that this is the best so far
                    if settings['step_3']['check_full_list']:
                        print('(' + str(link_index + 1) + '/' + str(len(sorted_links)) + ')',
                              '| Current best improvement by dropping link', dropped_link,
                              round(alternative_objective, 2))
                    # If we run a greedy approach, immediately break to end this iteration
                    else:
                        print('(' + str(link_index + 1) + '/' + str(len(sorted_links)) + ')',
                              '| Found improvement by dropping link', dropped_link)
                        break
                else:
                    # Dropping this link is an improvement, but not the best one in this iteration
                    print('(' + str(link_index + 1) + '/' + str(len(sorted_links)) + ')',
                          '| Found improvement by dropping link', dropped_link, round(alternative_objective, 2))
            else:
                # Dropping this link is not an improvement compared to last iteration, it is therefore rejected.
                print('(' + str(link_index + 1) + '/' + str(len(sorted_links)) + ')',
                      '| Rejected dropping link', dropped_link, rejection_reason)
                # Store the rejected link
                rejected_links.add(dropped_link)
        if best_dropped_link is not None:
            print('Dropped link |', best_dropped_link)
            print('New objective |', round(current_objective, 2))
            print('-' * 70)
            # Drop selected link from problem
            drop_link(problem, best_dropped_link)
            # Remove links from rejected set that we now want to re-evaluate
            connected_links = set()
            connected_links = connected_links.union(get_connected_links(problem, best_dropped_link[0])[1])
            connected_links = connected_links.union(get_connected_links(problem, best_dropped_link[1])[1])
            rejected_links = rejected_links - connected_links
    end_time = time.time()
    time_used.append(end_time - start_time)
    problem.display()
    # Step 4 - Converting to integer solution
    # --------------------------------------------------------------------------------------
    if not problem.random:
        start_time = time.time()
        print()
        print('Step 4 | Converting to integer solution, finalizing operational decisions')
        print('-' * 70)
        # Construct bounds to be used in reduced problem
        bounds = {
            'v': get_v_bounds(problem, method='integer')
        }
        # Create reduced, non-relaxed model
        reduced_model = Model(problem, {
            'linear_backlog_approx': True
        }, bounds=bounds, surpress_logs=settings['step_4']['surpress_gurobi'], parameters=settings['model_parameters'])
        reduced_model.solve(problem.instance_name, {
            'gap': settings['step_4']['epsilon'],
            'time': settings['step_4']['time']
        })
        end_time = time.time()
        time_used.append(end_time - start_time)
    else:
        model = Model(problem, bounds={'v': get_v_bounds(problem, method='integer_round_up')}, surpress_logs=True)
        model.solve(problem.instance_name, {'time': 5})
    # Load the feasible solution into our problem object
    original_problem.read_solution(problem.instance_name)
    # Log used time
    print('Time overview:')
    print('-' * 70)
    for i, t in enumerate(time_used):
        print('Time for step', i + 1, '| Time spent:', str(round(t, 2)) + 's')
    print('-' * 70)
    print('Total time      |', str(round(sum(time_used), 2)) + 's')
    print('-' * 70)
    return original_problem


# Random case
def performance_analysis(problem, M):
    drop_links(problem)
    # Generate scenarios for evaluation
    objectives = []
    for m in range(M):
        problem.generate_scenarios(1)
        model = Model(problem, bounds={'v': get_v_bounds(problem, method='exact')}, surpress_logs=True)
        model.write(problem.instance_name + '_test')
        if m == 0:
            print()
            print('Evaluation |')
            print('-' * 70)
        objective = model.solve(stopping_criteria={'gap': 0.01}, instance_name=problem.instance_name + '_evaluation')
        print(f'({m + 1}/{M}) | Found objective: {round(objective, 2)}')
        objectives.append(objective)
        # These lines can be used to log the evaluation scenario objectives
        # problem.read_solution(problem.instance_name + '_evaluation')
        # problem.log_objective(summary_only=True)
    print('-' * 70)
    np.savetxt('Evaluations/' + problem.instance_name + '_M' + str(M) + '_T' + str(problem.end) + '.txt',
               objectives, fmt="%s")


def monte_carlo_histogram(problem, M):
    plt.figure()
    plt.xlabel('Objective')
    plt.ylabel('Frequency (as fraction of total)')
    objectives = np.loadtxt('Evaluations/' + problem.instance_name + '_M' + str(M) + '_T' + str(problem.end) + '.txt')
    plt.hist(objectives, bins=20, weights=np.ones(M) / M)
    print('Monte Carlo statistics |', str(M), 'scenarios')
    print('-' * 70)
    print('Minimum objective |', round(min(objectives), 2))
    print('Average objective |', round(np.average(objectives), 2))
    print('Maximum objective |', round(max(objectives), 2))
    print('-' * 70)
    print('CI Lower bound    |', round(np.average(objectives) - 1.96 * (stdev(objectives) / math.sqrt(M)), 2))
    print('CI Upper bound    |', round(np.average(objectives) + 1.96 * (stdev(objectives) / math.sqrt(M)), 2))
    print('-' * 70)


# Functions that remove one or multiple links from a problem
def drop_link(problem, link):
    problem.links.remove(link)
    for t in problem.T:
        problem.link_time.remove((link[0], link[1], t))
        for p in problem.P:
            problem.link_product_time.remove((link[0], link[1], p, t))


def drop_links(problem, maximum_capacity=0.0):
    unused_links = [link for link in problem.links if problem.solution['v'][link] <= maximum_capacity]
    # Remove links form all relevant sets
    for link in unused_links:
        problem.links.remove(link)
        for t in problem.T:
            problem.link_time.remove((link[0], link[1], t))
            for p in problem.P:
                problem.link_product_time.remove((link[0], link[1], p, t))
    return unused_links


# A method that returns a v-bounds object; accepts different method settings
def get_v_bounds(problem, method='integer'):
    v_bounds = {}
    if method == 'all_zero':
        v_bounds = {(i, j): {'lb': 0,
                             'ub': 0}
                    for (i, j) in problem.links}
    elif method == 'exact':
        v_bounds = {(i, j): {'lb': problem.solution['v'][(i, j)],
                             'ub': problem.solution['v'][(i, j)]}
                    for (i, j) in problem.links}
    elif method == 'integer':
        v_bounds = {(i, j): {'lb': math.floor(problem.solution['v'][(i, j)]),
                             'ub': math.ceil(problem.solution['v'][(i, j)])}
                    for (i, j) in problem.links}
    elif method == 'exact_lower_bounds':
        v_bounds = {(i, j): {'lb': problem.solution['v'][(i, j)]}
                    for (i, j) in problem.links}
    elif method == 'integer_round_up':
        v_bounds = {(i, j): {'lb': math.ceil(problem.solution['v'][(i, j)]),
                             'ub': math.ceil(problem.solution['v'][(i, j)])}
                    for (i, j) in problem.links}
    return v_bounds


# Returns the sorted utilization costs of all links with a non-zero capacity
def get_utilization_costs(problem):
    utilization_costs = {}
    for link in problem.links:
        if link in problem.solution['v']:
            v = problem.solution['v'][link]
            if v > 0:
                link_costs = problem.opening_cost[link] + problem.capacity_cost[link] * v
                if not problem.random:
                    link_utilization = sum(
                        [problem.product_volume[p] * problem.solution['x'][link[0], link[1], p, str(t)]
                         for p in problem.P for t in problem.T])
                else:
                    N = len(problem.scenarios)
                    link_utilization = (1 / N) * sum([problem.product_volume[p]
                                                      * problem.solution['x'][link[0], link[1], p, str(t), str(theta)]
                                                      for p in problem.P for t in problem.T
                                                      for theta in range(N)])
                if link_utilization == 0:
                    utilization_costs[link] = math.inf
                else:
                    utilization_costs[link] = link_costs / link_utilization
    utilization_costs = dict(sorted(utilization_costs.items(), key=lambda item: -item[1]))
    return utilization_costs


# Recursively returns all links that can be used to reach a destination if some link is dropped
def get_alternative_links(problem, destination, dropped_link, alternative_links=None):
    if alternative_links is None:
        alternative_links = []
    new_links = []
    for i in problem.S_and_D:
        if (i, destination) not in alternative_links:
            if (i, destination) in problem.links and problem.solution['v'][(i, destination)] > 0 \
                    and (i, destination) != dropped_link:
                new_links += [(i, destination)]
    alternative_links += new_links
    for new_link in new_links:
        alternative_links = get_alternative_links(problem, new_link[0], dropped_link, alternative_links)
    return alternative_links


# Recursively returns all links that can be reached from a start node without passing by a supplier/customer node
def get_connected_links(problem, start_node, connected_nodes=None, connected_links=None):
    if connected_links is None:
        connected_links = set()
    if connected_nodes is None:
        connected_nodes = set()
    connected_nodes.add(start_node)
    for node in problem.S + problem.D + problem.C:
        if node not in connected_nodes and node != start_node:
            for link in [(start_node, node), (node, start_node)]:
                if link in problem.solution['v'].keys():
                    connected_nodes.add(node)
                    connected_links.add(link)
                    if node in problem.D:
                        extra_nodes, extra_links = get_connected_links(problem, node, connected_nodes, connected_links)
                        connected_nodes = connected_nodes.union(extra_nodes)
                        connected_links = connected_links.union(extra_links)
    return connected_nodes, connected_links
