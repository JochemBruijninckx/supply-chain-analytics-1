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

        # Objective
        tot_opening_cost = gb.LinExpr()
        tot_capacity_cost = gb.LinExpr()
        tot_distance_cost = gb.LinExpr()
        tot_holding_cost = gb.LinExpr()
        tot_backlog_cost = gb.QuadExpr()

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
        if not settings['all_links_open']:
            tot_opening_cost += gb.quicksum(problem.opening_cost[i, j] * l[i, j] for i, j in problem.links)

        tot_capacity_cost += gb.quicksum(problem.capacity_cost[i, j] * v[i, j] for i, j in problem.links)
        tot_distance_cost += gb.quicksum(k[i, j, t] * problem.distance[i, j] for i, j, t in problem.link_time)
        tot_holding_cost += gb.quicksum(
            gb.quicksum(
                problem.holding_cost[d] * gb.quicksum(
                    problem.product_volume[p] * I[d, p, t] for p in problem.P) for d in problem.D) for t in
            problem.T)

        tot_backlog_cost += gb.quicksum(
            problem.backlog_pen[c, p] * (I[c, p, t] - problem.cum_demand[c, p, t]) ** 2 for c, p, t in
            problem.customer_product_time)
        # for c, p, t in problem.customer_product_time:
        #     tot_backlog_cost += problem.backlog_pen[c, p] * ((I[c, p, t] - problem.cum_demand[c, p, t]) ** 2)

        mdl.setObjective(tot_opening_cost + tot_capacity_cost + tot_distance_cost + tot_holding_cost + tot_backlog_cost,
                         gb.GRB.MINIMIZE)

        # Constraints
        # --------------------------------------------------------------------------------------
        # Truck capacity on links
        mdl.addConstrs(k[i, j, t] <= v[i, j] for i, j, t in problem.link_time)
        # Sufficient amount of trucks for transport size
        mdl.addConstrs(
            k[i, j, t] >= (
                    gb.quicksum(problem.product_volume[p] * x[i, j, p, t] for p in problem.P) / problem.truck_size)
            for i, j, t in problem.link_time)
        # Linking constraint for opening of links
        if not settings['all_links_open']:
            mdl.addConstrs(10000 * l[i, j] >= v[i, j] for i, j in problem.links)
        # Minimum production constraint for suppliers
        mdl.addConstrs(
            gb.quicksum(x[s, j, p, t] for j in problem.D_and_C if (s, j) in problem.links) >=
            problem.min_prod[s, p] * r[s, p, t] for s, p, t in problem.supplier_product_time)
        # Maximum production constraint for suppliers
        mdl.addConstrs(
            gb.quicksum(x[s, j, p, t] for j in problem.D_and_C if (s, j) in problem.links) <=
            problem.max_prod[s, p] * r[s, p, t] for s, p, t in problem.supplier_product_time)
        # Capacity constraint for depots
        mdl.addConstrs(
            gb.quicksum(problem.product_volume[p] * I[d, p, t] for p in problem.P) <= problem.capacity[d] for
            d, t in problem.depot_time)
        # Cannot transport more from depots than is in their inventories
        mdl.addConstrs(
            gb.quicksum(x[d, j, p, t] for j in problem.D_and_C if j != d and (d, j) in problem.links) <=
            I[d, p, t] + gb.quicksum(x[j, d, p, t - problem.duration[j, d]] for j in problem.S_and_D
                                     if d != j and t - problem.duration[j, d] > problem.start) for d, p, t in
            problem.depot_product_time)
        # Flow constraints
        mdl.addConstrs(
            I[d, p, t] == I[d, p, t - 1] +
            gb.quicksum(x[j, d, p, t - problem.duration[j, d]] for j in problem.S_and_D
                        if d != j and t - problem.duration[j, d] > problem.start)
            - gb.quicksum(x[d, c, p, t] for c in problem.C)
            for (d, p, t) in problem.depot_product_time
        )
        mdl.addConstrs(
            I[c, p, t] == I[c, p, t - 1] +
            gb.quicksum(x[j, c, p, t - problem.duration[j, c]] for j in problem.S_and_D
                        if t - problem.duration[j, c] > problem.start)
            for (c, p, t) in problem.customer_product_time
        )
        # Nodes start at zero inventory
        mdl.addConstrs(
            I[i, p, 0] == 0 for i in problem.D_and_C for p in problem.P
        )
        # All demand must be filled by end of period
        mdl.addConstrs(
            I[c, p, problem.end] == problem.cum_demand[c, p, problem.end] for (c, p) in problem.customer_product
        )

        # No backlog constraint
        if settings['perfect_delivery']:
            mdl.addConstrs(
                problem.demand[c, p, t] == gb.quicksum(x[i, c, p, t - problem.duration[i, c]] for i in problem.S_and_D
                                                       if t - problem.duration[i, c] >= problem.start
                                                       )
                for c, p, t in problem.demand_set
            )

        # Generate model
        mdl.update()
        mdl.optimize()

        print('Opening cost:', tot_opening_cost.getValue())
        print('Capacity cost:', tot_capacity_cost.getValue())
        print('Distance cost:', tot_distance_cost.getValue())
        print('Holding cost:', tot_holding_cost.getValue())
        print('Backlog cost:', tot_backlog_cost.getValue())
        self.mdl = mdl

    # Solve model and save solution to a solution file
    def solve(self, instance_name):
        # Optimize
        self.mdl.optimize()
        # Save solution
        self.mdl.write('Solutions/' + instance_name + '.sol')

    def write(self, instance_name):
        self.mdl.write('Instances/' + instance_name + '.lp')
