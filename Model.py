import gurobipy as gb


class Model:
    def __init__(self, problem, settings=None, bounds=None):
        if settings is None:
            settings = {
                'all_links_open': False,
                'non_integer_trucks': False,
                'perfect_delivery': False,
            }
        if bounds is None:
            bounds = {}

        # Model setup
        # --------------------------------------------------------------------------------------
        mdl = gb.Model()

        # Variables
        # --------------------------------------------------------------------------------------
        x = mdl.addVars(problem.link_product_time, vtype=gb.GRB.CONTINUOUS, lb=0, name='x')
        r = mdl.addVars(problem.supplier_product_time, vtype=gb.GRB.BINARY, name='r')
        if not settings['all_links_open']:
            l = mdl.addVars(problem.links, vtype=gb.GRB.BINARY, name='l')
        if settings['non_integer_trucks']:
            k = mdl.addVars(problem.link_time, vtype=gb.GRB.CONTINUOUS, lb=0, name='k')
            v = mdl.addVars(problem.links, vtype=gb.GRB.CONTINUOUS, lb=0, name='v')
        else:
            k = mdl.addVars(problem.link_time, vtype=gb.GRB.INTEGER, lb=0, name='k')
            v = mdl.addVars(problem.links, vtype=gb.GRB.INTEGER, lb=0, name='v')

        I = mdl.addVars(problem.dc_product_time, vtype=gb.GRB.CONTINUOUS, lb=0, name='I')

        # Set bounds if provided
        if 'r' in bounds:
            for (s, p, t) in bounds['r'].keys():
                r[s, p, int(t)].lb = bounds['r'][(s, p, t)]
                r[s, p, int(t)].ub = bounds['r'][(s, p, t)]
        if 'v' in bounds:
            for (i, j) in bounds['v'].keys():
                v[i, j].lb = bounds['v'][(i, j)]['lb']
                v[i, j].ub = bounds['v'][(i, j)]['ub']

        # Objective
        # --------------------------------------------------------------------------------------
        tot_opening_cost = gb.LinExpr()
        tot_capacity_cost = gb.LinExpr()
        tot_distance_cost = gb.LinExpr()
        tot_holding_cost = gb.LinExpr()
        tot_backlog_cost = gb.QuadExpr()

        # Opening costs
        if not settings['all_links_open']:
            tot_opening_cost += gb.quicksum(problem.opening_cost[i, j] * l[i, j] for i, j in problem.links)

        # Capacity costs
        tot_capacity_cost += gb.quicksum(problem.capacity_cost[i, j] * v[i, j] for i, j in problem.links)

        # Distance costs
        tot_distance_cost += gb.quicksum(problem.distance[i, j] * k[i, j, t] for i, j, t in problem.link_time)

        # Holding costs
        tot_holding_cost += gb.quicksum(problem.holding_cost[d] * gb.quicksum(problem.product_volume[p] * I[d, p, t]
                                                                              for p in problem.P)
                                        for d, t in problem.depot_time)

        # Backlog costs
        if not settings['perfect_delivery']:
            tot_backlog_cost += gb.quicksum(problem.backlog_pen[c, p] * (I[c, p, t] - problem.cum_demand[c, p, t]) ** 2
                                        for c, p, t in problem.customer_product_time)

        mdl.setObjective(tot_opening_cost + tot_capacity_cost + tot_distance_cost + tot_holding_cost + tot_backlog_cost,
                         gb.GRB.MINIMIZE)

        # Constraints
        # --------------------------------------------------------------------------------------
        # Linking constraint for opening of links
        if not settings['all_links_open']:
            mdl.addConstrs(
                (10000 * l[i, j] >= v[i, j] for i, j in problem.links),
                name='Links must be opened to procure capacity'
            )
        # Truck capacity on links
        mdl.addConstrs(
            (k[i, j, t] <= v[i, j] for i, j, t in problem.link_time),
            name='# Trucks cannot exceed capacity'
        )
        # Sufficient amount of trucks for transport size
        mdl.addConstrs(
            (k[i, j, t] >= gb.quicksum(problem.product_volume[p] * x[i, j, p, t]
                                       for p in problem.P) / problem.truck_size
             for i, j, t in problem.link_time),
            name='# Trucks required for transport volume'
        )
        # Minimum production constraint for suppliers
        mdl.addConstrs(
            (gb.quicksum(x[s, j, p, t] for j in problem.D_and_C if (s, j) in problem.links) >=
             problem.min_prod[s, p] * r[s, p, t] for s, p, t in problem.supplier_product_time),
            name='Minimum required production if supplier used'
        )
        # Maximum production constraint for suppliers
        mdl.addConstrs(
            (gb.quicksum(x[s, j, p, t] for j in problem.D_and_C if (s, j) in problem.links) <=
             problem.max_prod[s, p] * r[s, p, t] for s, p, t in problem.supplier_product_time),
            name='Maximum allowed production if supplier used'
        )
        # Capacity constraint for depots
        mdl.addConstrs(
            (gb.quicksum(problem.product_volume[p] * I[d, p, t] for p in problem.P) <= problem.capacity[d]
             for d, t in problem.depot_time),
            name='Depot inventory volume cannot exceed capacity'
        )
        # Cannot transport more from depots than is in their inventories
        mdl.addConstrs(
            (gb.quicksum(x[d, j, p, t] for j in problem.D_and_C if (d, j) in problem.links) <=
             I[d, p, t - 1] + gb.quicksum(x[j, d, p, t - problem.duration[j, d]] for j in problem.S_and_D
                                          if (j, d) in problem.links and t - problem.duration[j, d] >= problem.start)
             for d, p, t in problem.depot_product_time),
            name='Outgoing transport from depot cannot exceed inventory'
        )
        # Flow constraints
        mdl.addConstrs(
            (I[d, p, t] == I[d, p, t - 1]
             + gb.quicksum(x[j, d, p, t - problem.duration[j, d]] for j in problem.S_and_D
                           if (j, d) in problem.links and t - problem.duration[j, d] >= problem.start)
             - gb.quicksum(x[d, j, p, t] for j in problem.D_and_C if (d, j) in problem.links)
             for d, p, t in problem.depot_product_time),
            name='Depot inventory flow constraint'
        )
        mdl.addConstrs(
            (I[c, p, t] == I[c, p, t - 1]
             + gb.quicksum(x[i, c, p, t - problem.duration[i, c]] for i in problem.S_and_D
                           if t - problem.duration[i, c] >= problem.start and (i, c) in problem.links)
             for c, p, t in problem.customer_product_time),
            name='Customer inventory flow constraint'
        )
        # Nodes start at zero inventory
        mdl.addConstrs(
            (I[i, p, 0] == 0 for i in problem.D_and_C for p in problem.P),
            name='Nodes start at zero inventory'
        )
        # All demand must be filled by end of period
        mdl.addConstrs(
            (I[c, p, problem.end] == problem.cum_demand[c, p, problem.end] for c, p in problem.customer_product),
            name='Final customer inventory must match cumulative demand'
        )

        if settings['perfect_delivery']:
            mdl.addConstrs(
                (I[c, p, t] == problem.cum_demand[c, p, t] for c, p, t in problem.demand_set),
                name='Perfect delivery constraint'
            )

        # Generate model
        mdl.update()
        # mdl.optimize()
        #
        # print('Opening cost:', tot_opening_cost.getValue())
        # print('Capacity cost:', tot_capacity_cost.getValue())
        # print('Distance cost:', tot_distance_cost.getValue())
        # print('Holding cost:', tot_holding_cost.getValue())
        # print('Backlog cost:', tot_backlog_cost.getValue())
        self.mdl = mdl

    # Solve model and save solution to a solution file
    def solve(self, instance_name):
        # Optimize
        self.mdl.optimize()
        # Save solution
        self.mdl.write('Solutions/' + instance_name + '.sol')

    def write(self, instance_name):
        self.mdl.write('Instances/' + instance_name + '.lp')
