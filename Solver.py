import math
import copy

from Model import Model


def solve(problem, settings=None, bounds=None):
    # Create regular model
    model = Model(problem, settings, bounds=bounds)
    model.write(problem.instance_name)
    model.solve(problem.instance_name)
    # Load the solution into our problem object
    problem.read_solution(problem.instance_name)


def heuristic(problem, create_initial_solution=True):
    # Step 1 - Create or load initial solution.
    # --------------------------------------------------------------------------------------
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
        })
        relaxed_model.write(problem.instance_name + '_relaxed')
        relaxed_model.solve(problem.instance_name + '_relaxed', {
            'gap': 0.1
        })
    else:
        print('Step 1 | Loading initial solution')
    # Load the solution into our problem object
    problem.read_solution(problem.instance_name + '_relaxed')
    problem.display()
    # Step 2 - Mass link dropping (all low capacity links are removed if improvement found)
    # --------------------------------------------------------------------------------------
    current_objective = problem.compute_objective()
    original_problem = copy.deepcopy(problem)
    # Try mass link dropping
    print()
    print('Step 2 | Mass link dropping (current objective', str(round(current_objective, 2)) + ')')
    print('-' * 70)
    start_capacity = 3
    step_size = 0.25
    current_capacity = start_capacity
    while current_capacity >= 0:
        step = round((start_capacity - current_capacity) / step_size)
        # Create alternative problem in which all low-capacity links are dropped
        alternative_problem = copy.deepcopy(original_problem)
        drop_links(alternative_problem, current_capacity)
        # Set lower bounds on the capacity of all remaining links equal to their current value
        v_bounds = get_v_bounds(alternative_problem, method='exact')
        # Construct and solve the alternative model
        alternative_model = Model(alternative_problem, {
            'non_integer_trucks': True,
            'linear_backlog_approx': True
        }, {'v': v_bounds}, surpress_logs=True)
        alternative_objective = alternative_model.solve(problem.instance_name + '_alternative', {
            'bound': current_objective
        })
        # If the solution to the alternative model is an improvement, use it as new starting point (skip to Step 3)
        if alternative_objective < current_objective:
            print('(' + str(step + 1) + '/' + str(round(start_capacity / step_size)) + ')',
                  '| Found improvement by dropping all links with capacity <', current_capacity)
            current_objective = alternative_objective
            problem = alternative_problem
            problem.read_solution(problem.instance_name + '_alternative')
            print('New objective |', current_objective)
            alternative_problem.display()
            break
        else:
            print('(' + str(step + 1) + '/' + str(round(start_capacity / step_size)) + ')',
                  '| Rejected dropping all links with capacity <', current_capacity)
            current_capacity -= step_size
    # Step 3 - Dropping individual links
    # --------------------------------------------------------------------------------------
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
            # Construct a v_bounds object that will limit our allowed choices of capacity
            v_bounds = get_v_bounds(problem, method='exact')
            v_bounds[dropped_link] = {'lb': 0, 'ub': 0}
            alternative_links = get_alternative_links(problem, dropped_link[1], dropped_link)
            # If this link is our only link to a customer, reject dropping it by default
            if alternative_links == [] and dropped_link[1] in problem.C:
                alternative_objective = math.inf
            else:
                for alternative_link in alternative_links:
                    v_bounds[alternative_link].pop('ub')
                # Construct alternative model using the previously constructed v_bounds and solve it
                alternative_model = Model(problem, {
                    'non_integer_trucks': True,
                    'linear_backlog_approx': True
                }, {'v': v_bounds}, surpress_logs=True)
                alternative_objective = alternative_model.solve(problem.instance_name + '_alternative', {
                    'bound': current_objective
                })
            # Check if the alternative capacity procurement leads to an objective improvement
            if alternative_objective < current_objective:
                print('(' + str(link_index + 1) + '/' + str(len(sorted_links)) + ')',
                      '| Found improvement by dropping link', dropped_link)
                print('New objective |', alternative_objective)
                print('-' * 70)
                problem.read_solution(problem.instance_name + '_alternative')
                drop_link(problem, dropped_link)
                current_objective = alternative_objective
                found_improvement = True
                break
            else:
                print('(' + str(link_index + 1) + '/' + str(len(sorted_links)) + ')',
                      '| Rejected dropping link', dropped_link)
                # Store the rejected link
                rejected_links.add(dropped_link)
    problem.display()
    # Step 4 - Converting to integer solution
    # --------------------------------------------------------------------------------------
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
    }, bounds=bounds)
    reduced_model.solve(problem.instance_name, {
        'gap': 0.1
    })
    # Load the feasible solution into our problem object
    problem.read_solution(problem.instance_name)
    problem.display()
    input('Press enter to exit..')


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
            if (i, destination) in problem.links and problem.solution['v'][(i, destination)] > 0 and (
            i, destination) != dropped_link:
                new_links += [(i, destination)]
    alternative_links += new_links
    for new_link in new_links:
        alternative_links = get_alternative_links(problem, new_link[0], dropped_link, alternative_links)
    return alternative_links
