import math

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
    if create_initial_solution:
        # Create relaxed version of the model and solve it
        relaxed_model = Model(problem, {
            'all_links_open': True,
            'non_integer_trucks': True,
            'linear_backlog_approx': False,
            'perfect_delivery': True
        })
        relaxed_model.write(problem.instance_name + '_relaxed')
        relaxed_model.solve(problem.instance_name + '_relaxed')
    # Load the solution into our problem object
    problem.read_solution(problem.instance_name + '_relaxed')
    problem.display()
    # Drop any unused links from our problem object
    drop_links(problem)
    # Step 2 -
    # --------------------------------------------------------------------------------------
    current_objective = problem.compute_objective()
    found_improvement = True
    iteration = 0
    print()
    print('Initial objective |', current_objective)
    print()
    while found_improvement:
        iteration += 1
        found_improvement = False
        print('ITERATION', iteration)
        print('-' * 70)
        sorted_links = get_utilization_costs(problem)
        for (link_index, dropped_link) in enumerate(sorted_links):
            # Construct a v_bounds object that will limit our allowed choices of capacity
            v_bounds = get_v_bounds(problem, exact=True)
            v_bounds[dropped_link] = {'lb': 0, 'ub': 0}
            alternative_links = get_alternative_links(problem, dropped_link[1], dropped_link)
            for alternative_link in alternative_links:
                v_bounds[alternative_link].pop('ub')
            # Construct alternative model using the previously constructed v_bounds and solve it
            alternative_model = Model(problem, {
                'non_integer_trucks': True,
                'linear_backlog_approx': True
            }, {'v': v_bounds}, surpress_logs=True)
            alternative_objective = alternative_model.solve(problem.instance_name + '_alternative')
            # Check if the alternative capacity procurement leads to an objective improvement
            if alternative_objective < current_objective:
                found_improvement = True
                print('(' + str(link_index + 1) + '/' + str(len(sorted_links)) + ')',
                      '| Found improvement by dropping link', dropped_link)
                print('New objective |', alternative_objective)
                problem.read_solution(problem.instance_name + '_alternative')
                drop_link(problem, dropped_link)
                current_objective = alternative_objective
                break
            else:
                print('(' + str(link_index + 1) + '/' + str(len(sorted_links)) + ')',
                      '| Rejected dropping link', dropped_link)
    problem.display()
    # Step 3 -
    # --------------------------------------------------------------------------------------
    # # Construct bounds to be used in reduced problem
    # bounds = {
    #     'r': problem.solution['r'],
    #     'v': get_v_bounds(problem)
    # }
    # # Create reduced, non-relaxed model
    # reduced_model = Model(problem, {
    #     'all_links_open': False,
    #     'non_integer_trucks': False,
    #     'linear_backlog_approx': True
    # }, bounds=bounds)
    # reduced_model.solve(problem.instance_name)
    # # Load the feasible solution into our problem object
    # problem.read_solution(problem.instance_name)


def drop_link(problem, link):
    problem.links.remove(link)
    for t in problem.T:
        problem.link_time.remove((link[0], link[1], t))
        for p in problem.P:
            problem.link_product_time.remove((link[0], link[1], p, t))


def drop_links(problem, minimum_capacity=0):
    unused_links = [link for link in problem.links if problem.solution['v'][link] <= minimum_capacity]
    # Remove unused links form all relevant sets
    for link in unused_links:
        problem.links.remove(link)
        for t in problem.T:
            problem.link_time.remove((link[0], link[1], t))
            for p in problem.P:
                problem.link_product_time.remove((link[0], link[1], p, t))


def get_v_bounds(problem, all_zero=False, exact=False):
    if all_zero:
        v_bounds = {(i, j): {'lb': 0,
                             'ub': 0}
                    for (i, j) in problem.links}
    else:
        if exact:
            v_bounds = {(i, j): {'lb': problem.solution['v'][(i, j)],
                                 'ub': problem.solution['v'][(i, j)]}
                        for (i, j) in problem.links}
        else:
            v_bounds = {(i, j): {'lb': math.floor(problem.solution['v'][(i, j)]),
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
            if (i, destination) in problem.links and problem.solution['v'][(i, destination)] > 0 and (i, destination) != dropped_link:
                new_links += [(i, destination)]
    alternative_links += new_links
    for new_link in new_links:
        alternative_links = get_alternative_links(problem, new_link[0], dropped_link, alternative_links)
    return alternative_links
