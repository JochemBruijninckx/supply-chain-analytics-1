import math
import copy
import time

from Model import Model


def solve(problem, settings=None, bounds=None):
    # Create regular model
    model = Model(problem, settings, bounds=bounds)
    model.write(problem.instance_name)
    model.solve(problem.instance_name)
    # Load the solution into our problem object
    problem.read_solution(problem.instance_name)
    return problem


def heuristic(problem, settings, create_initial_solution=True):
    time_used = []
    # Step 1 - Create or load initial solution.
    # --------------------------------------------------------------------------------------
    start_time = time.time()
    print()
    if create_initial_solution:
        print('Step 1 | Creating initial solution')
        print('-' * 70)
        # Create relaxed version of the model and solve it
        relaxed_model = Model(problem, {
            'all_links_open': True,
            'non_integer_trucks': True,
            'linear_backlog_approx': False,
            'perfect_delivery': True
        }, surpress_logs=settings['step_1']['surpress_gurobi'])
        relaxed_model.write(problem.instance_name + '_relaxed')
        relaxed_model.solve(problem.instance_name + '_relaxed', {
            'gap': settings['step_1']['epsilon']
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
        alternative_problem = copy.deepcopy(original_problem)
        drop_links(alternative_problem, current_capacity)
        # Set lower bounds on the capacity of all remaining links equal to their current value
        v_bounds = get_v_bounds(alternative_problem, method='exact')
        # Construct and solve the alternative model
        alternative_model = Model(alternative_problem, {
            'non_integer_trucks': True,
            'linear_backlog_approx': True
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
        sorted_links = get_utilization_costs(problem)
        for (link_index, dropped_link) in enumerate(sorted_links):
            rejection_reason = ''
            if dropped_link in rejected_links:
                rejection_reason = '(Does not need to be reevaluated)'
                alternative_objective = math.inf
            else:
                # Construct a v_bounds object that will limit our allowed choices of capacity
                v_bounds = get_v_bounds(problem, method='exact')
                v_bounds[dropped_link] = {'lb': 0, 'ub': 0}
                alternative_links = get_alternative_links(problem, dropped_link[1], dropped_link)
                # If this link is our only link to a customer, reject dropping it by default
                if alternative_links == [] and dropped_link[1] in problem.C:
                    rejection_reason = '(Only route to customer)'
                    alternative_objective = math.inf
                else:
                    for alternative_link in alternative_links:
                        v_bounds[alternative_link].pop('ub')
                    # Construct alternative model using the previously constructed v_bounds and solve it
                    alternative_model = Model(problem, {
                        'non_integer_trucks': True,
                        'linear_backlog_approx': True
                    }, {'v': v_bounds}, surpress_logs=True, parameters=settings['model_parameters'])
                    alternative_objective = alternative_model.solve(problem.instance_name + '_alternative', {
                        'bound': current_objective
                    })
            # Check if the alternative capacity procurement leads to an objective improvement
            if alternative_objective < current_objective:
                print('(' + str(link_index + 1) + '/' + str(len(sorted_links)) + ')',
                      '| Found improvement by dropping link', dropped_link)
                print('New objective |', round(alternative_objective, 2))
                print('-' * 70)
                problem.read_solution(problem.instance_name + '_alternative')
                drop_link(problem, dropped_link)
                current_objective = alternative_objective
                # Remove links from rejected set that we now want to re-evaluate
                connected_links = set()
                connected_links = connected_links.union(get_connected_links(problem, dropped_link[0])[1])
                connected_links = connected_links.union(get_connected_links(problem, dropped_link[1])[1])
                rejected_links = rejected_links - connected_links
                found_improvement = True
                break
            else:
                print('(' + str(link_index + 1) + '/' + str(len(sorted_links)) + ')',
                      '| Rejected dropping link', dropped_link, rejection_reason)
                # Store the rejected link
                rejected_links.add(dropped_link)
    end_time = time.time()
    time_used.append(end_time - start_time)
    problem.display()
    # Step 4 - Converting to integer solution
    # --------------------------------------------------------------------------------------
    start_time = time.time()
    print()
    print('Step 4 | Converting to integer solution, finalizing operational decisions')
    print('-' * 70)
    # Construct bounds to be used in reduced problem
    bounds = {
        'v': get_v_bounds(problem, method='integer_round_up')
    }
    # Create reduced, non-relaxed model
    reduced_model = Model(problem, {
        'linear_backlog_approx': True
    }, bounds=bounds, surpress_logs=settings['step_4']['surpress_gurobi'], parameters=settings['model_parameters'])
    reduced_model.solve(problem.instance_name, {
        'gap': settings['step_4']['epsilon']
    })
    # Load the feasible solution into our problem object
    original_problem.read_solution(problem.instance_name)
    end_time = time.time()
    time_used.append(end_time - start_time)
    # Log used time
    print('Time overview:')
    print('-' * 70)
    for i, t in enumerate(time_used):
        print('Time for step', i + 1, '| Time spent:', str(round(t, 2)) + 's')
    print('-' * 70)
    print('Total time      |', str(round(sum(time_used), 2)) + 's')
    print('-' * 70)
    return original_problem


def drop_link(problem, link):
    problem.links.remove(link)
    for t in problem.T:
        problem.link_time.remove((link[0], link[1], t))
        for p in problem.P:
            problem.link_product_time.remove((link[0], link[1], p, t))


def drop_links(problem, maximum_capacity=0.0):
    unused_links = [link for link in problem.links if problem.solution['v'][link] <= maximum_capacity]
    # Remove unused links form all relevant sets
    for link in unused_links:
        problem.links.remove(link)
        for t in problem.T:
            problem.link_time.remove((link[0], link[1], t))
            for p in problem.P:
                problem.link_product_time.remove((link[0], link[1], p, t))
    return unused_links


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


def get_utilization_costs(problem):
    utilization_costs = {}
    for link in problem.links:
        if link in problem.solution['v']:
            v = problem.solution['v'][link]
            if v > 0:
                link_costs = problem.opening_cost[link] + problem.capacity_cost[link] * v
                link_utilization = sum([problem.product_volume[p] * problem.solution['x'][link[0], link[1], p, str(t)]
                                        for p in problem.P for t in problem.T])
                if link_utilization == 0:
                    utilization_costs[link] = math.inf
                else:
                    utilization_costs[link] = link_costs / link_utilization
    utilization_costs = dict(sorted(utilization_costs.items(), key=lambda item: -item[1]))
    return utilization_costs


def get_alternative_links(problem, destination, dropped_link, alternative_links=None):
    if alternative_links is None:
        alternative_links = []
    new_links = []
    for i in problem.S_and_D:
        if (i, destination) not in alternative_links:
            if (i, destination) in problem.links and problem.solution['v'][(i, destination)] > 0\
                    and (i, destination) != dropped_link:
                new_links += [(i, destination)]
    alternative_links += new_links
    for new_link in new_links:
        alternative_links = get_alternative_links(problem, new_link[0], dropped_link, alternative_links)
    return alternative_links


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
