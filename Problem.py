import csv
import os
import pandas as pd
import numpy as np

from Display import Display


# Function that can create random instances
def gen_instance(seed, num_s, num_d, num_c, num_p, T):
    np.random.seed(seed)
    n = num_s + num_d + num_c
    s_coordinates = (1 / 10) * np.random.randint(0, 10 * n, (num_s, 2))
    d_coordinates = (1 / 10) * np.random.randint(2.5 * n, 7.5 * n, (num_d, 2))
    c_coordinates = (1 / 10) * np.random.randint(0, 10 * n, (num_c, 2))
    # Sheet 1 - Suppliers
    supplier_data = pd.DataFrame(index=['S' + str(i + 1) for i in range(num_s)],
                                 columns=['LocationX', 'LocationY'])
    supplier_data.index.name = 'SupplierID'
    for i in range(num_s):
        supplier_data.loc['S' + str(i + 1), :] = [s_coordinates[i][0], s_coordinates[i][1]]
    print(supplier_data)
    # Sheet 2 - Depots
    depot_data = pd.DataFrame(index=['D' + str(i + 1) for i in range(num_d)],
                              columns=['LocationX', 'LocationY', 'Capacity', 'Holding Cost'])
    depot_data.index.name = 'DepotID'
    for i in range(num_d):
        capacity = round(7 + 20 * np.random.random(), 2)
        holding_cost = round(0.3 + 0.3 * np.random.random(), 2)
        depot_data.loc['D' + str(i + 1), :] = [d_coordinates[i][0], d_coordinates[i][1],
                                               capacity, holding_cost]
    print(depot_data)
    # Sheet 3 - Customers
    customer_data = pd.DataFrame(index=['C' + str(i + 1) for i in range(num_c)],
                                 columns=['LocationX', 'LocationY'])
    customer_data.index.name = 'CustomerID'
    for i in range(num_c):
        customer_data.loc['C' + str(i + 1), :] = [c_coordinates[i][0], c_coordinates[i][1]]
    print(customer_data)
    # Sheet 4 - Products
    product_data = pd.DataFrame(index=['P' + str(i + 1) for i in range(num_p)],
                                columns=['Size'])
    product_data.index.name = 'ProductID'
    for i in range(num_p):
        product_data.loc['P' + str(i + 1), :] = round(0.2 + 0.8 * np.random.random(), 2)
    print(product_data)
    # Sheet 5 - Links
    origins = ['S' + str(i + 1) for i in range(num_s)] + ['D' + str(i + 1) for i in range(num_d)]
    destinations = ['D' + str(i + 1) for i in range(num_d)] + ['C' + str(i + 1) for i in range(num_c)]
    links = [(i, j) for i in origins for j in destinations if i != j]
    link_data = pd.DataFrame(index=pd.MultiIndex.from_tuples(links),
                             columns=['Opening Cost', 'Capacity Cost', 'Duration'])
    link_data.index.names = ['Origin', 'Destination']

    # Determine all distances
    locations = pd.concat([supplier_data.iloc[:, :3].rename(columns={'SupplierID': 'Location'}),
                           depot_data.iloc[:, :3].rename(columns={'DepotID': 'Location'}),
                           customer_data.iloc[:, :3].rename(columns={'CustomerID': 'Location'})])
    distance = {a: np.hypot(locations.loc[a[0]]['LocationX'] - locations.loc[a[1]]['LocationX'],
                            locations.loc[a[0]]['LocationY'] - locations.loc[a[1]]['LocationY']) for a in links}
    bins = [np.quantile(list(distance.values()), q) for q in [0.25, 0.5, 0.75]]
    durations = np.digitize(list(distance.values()), bins)
    link_index = 0
    for i in origins:
        for j in destinations:
            if i != j:
                opening_cost = round(50 + 100 * np.random.random(), 2)
                capacity_cost = round(5 + 10 * np.random.random(), 2)
                link_data.loc[i, j] = [opening_cost, capacity_cost, durations[link_index] + 1]
                link_index += 1
    print(link_data)
    # Sheet 6 - Demand
    demand_data = pd.DataFrame(index=pd.MultiIndex.from_product([['C' + str(i + 1) for i in range(num_c)],
                                                                 ['P' + str(j + 1) for j in range(num_p)],
                                                                 ['T' + str(t) for t in range(5, T + 1)]], ),
                               columns=['Amount'])
    demand_data.index.names = ['Customer', 'Product', 'Time']
    for i in range(1, num_c + 1):
        for j in range(1, num_p + 1):
            for t in range(5, T + 1):
                if np.random.random() > 0.7:
                    demand_data.loc['C' + str(i), 'P' + str(j), 'T' + str(t)] = round(18 * np.random.random(), 2)
                else:
                    demand_data.loc['C' + str(i), 'P' + str(j), 'T' + str(t)] = 0
    print(demand_data)
    # Sheet 7 - Backlogs
    backlog_data = pd.DataFrame(index=pd.MultiIndex.from_product([['C' + str(i + 1) for i in range(num_c)],
                                                                  ['P' + str(j + 1) for j in range(num_p)]]),
                                columns=['Amount'])
    backlog_data.index.names = ['Customer', 'Product']
    for i in range(num_c):
        for j in range(num_p):
            backlog_data.loc['C' + str(i + 1), 'P' + str(j + 1)] = round(7 + 10 * np.random.random(), 2)
    print(backlog_data)
    # Sheet 8 - Production
    production_data = pd.DataFrame(index=pd.MultiIndex.from_product([['S' + str(i + 1) for i in range(num_s)],
                                                                     ['P' + str(j + 1) for j in range(num_p)]]),
                                   columns=['Minimum', 'Maximum'])
    production_data.index.names = ['Supplier', 'Product']
    for i in range(num_s):
        for j in range(num_p):
            if np.random.random() <= 0.8:
                min_production = round(7 + 10 * np.random.random(), 2)
                max_production = round(min_production + 5 + 5 * np.random.random(), 2)
            else:
                min_production = 0
                max_production = 0
            production_data.loc['S' + str(i + 1), 'P' + str(j + 1)] = [min_production, max_production]
    print(production_data)
    # Sheet 9 - Parameters
    parameter_data = pd.DataFrame(index=['Truck Size', 'Start Time Horizon', 'End Time Horizon'],
                                  columns=['Value'])
    parameter_data.index.name = 'Parameter'
    parameter_data.loc['Truck Size', :] = round(1 + 2 * np.random.random(), 2)
    parameter_data.loc['Start Time Horizon', :] = 'T1'
    parameter_data.loc['End Time Horizon', :] = 'T' + str(T)
    print(parameter_data)

    with pd.ExcelWriter('Instances/' + str(seed) + '.xlsx') as writer:
        supplier_data.to_excel(writer, sheet_name='Suppliers', merge_cells=False)
        depot_data.to_excel(writer, sheet_name='Depots', merge_cells=False)
        customer_data.to_excel(writer, sheet_name='Customers', merge_cells=False)
        product_data.to_excel(writer, sheet_name='Products', merge_cells=False)
        link_data.to_excel(writer, sheet_name='Links', merge_cells=False)
        demand_data.to_excel(writer, sheet_name='Demand', merge_cells=False)
        backlog_data.to_excel(writer, sheet_name='Backlog Penalty', merge_cells=False)
        production_data.to_excel(writer, sheet_name='Production', merge_cells=False)
        parameter_data.to_excel(writer, sheet_name='Parameters', merge_cells=False)


class Problem:

    def __init__(self, instance_name):
        # Retrieve instance file from Instances directory
        self.instance_name = instance_name
        cwd = os.getcwd()
        filename = os.path.join(cwd, 'Instances/' + instance_name + '.xlsx')
        data = pd.read_excel(filename, sheet_name=None, engine='openpyxl')

        # Data extraction
        # --------------------------------------------------------------------------------------
        supplier_data = data['Suppliers']
        depot_data = data['Depots']
        customer_data = data['Customers']
        product_data = data['Products']
        link_data = data['Links']
        demand_data = data['Demand']
        backlog_data = data['Backlog Penalty']
        production_data = data['Production']
        parameter_data = data['Parameters']
        self.truck_size = data['Parameters']['Value'][0]

        # Object- and index sets
        # --------------------------------------------------------------------------------------
        # Object sets
        self.S = supplier_data['SupplierID'].to_list()
        self.D = depot_data['DepotID'].to_list()
        self.C = customer_data['CustomerID'].to_list()
        self.S_and_D = self.S + self.D
        self.D_and_C = self.D + self.C
        self.P = product_data['ProductID'].to_list()
        self.start = int(parameter_data['Value'][1].replace('T', ''))
        self.end = int(parameter_data['Value'][2].replace('T', ''))
        self.T = [t for t in range(self.start, self.end + 1, 1)]
        self.links = [(link_data['Origin'][i], link_data['Destination'][i]) for i in range(len(link_data))]
        # Index sets
        self.customer_product = [(backlog_data['Customer'][i], backlog_data['Product'][i]) for i in
                                 range(len(backlog_data))]
        self.supplier_product = [(production_data['Supplier'][i], production_data['Product'][i])
                                 for i in range(len(production_data))]
        self.demand_set = [(demand_data['Customer'][i], demand_data['Product'][i],
                            int(demand_data['Time'][i].replace('T', ''))) for i in range(len(demand_data))]

        self.link_product_time = []
        for a in self.links:
            for p in self.P:
                for t in self.T:
                    self.link_product_time.append((a[0], a[1], p, t))

        self.link_time = []
        for a in self.links:
            for t in self.T:
                self.link_time.append((a[0], a[1], t))

        self.supplier_product_time = []
        for s in self.S:
            for p in self.P:
                for t in self.T:
                    self.supplier_product_time.append((s, p, t))

        self.depot_time = []
        for d in self.D:
            for t in self.T:
                self.depot_time.append((d, t))

        self.depot_product_time = []
        for d in self.D:
            for p in self.P:
                for t in self.T:
                    self.depot_product_time.append((d, p, t))

        self.customer_product_time = []
        for c in self.C:
            for p in self.P:
                for t in self.T:
                    self.customer_product_time.append((c, p, t))

        self.dc_product_time = []
        for i in self.D_and_C:
            for p in self.P:
                for t in [0] + self.T:
                    self.dc_product_time.append((i, p, t))

        # Parameter/data sets
        # --------------------------------------------------------------------------------------
        self.holding_cost = {self.D[i]: depot_data['Holding Cost'][i] for i in range(len(self.D))}
        self.capacity = {self.D[i]: depot_data['Capacity'][i] for i in range(len(self.D))}
        self.product_volume = {self.P[i]: product_data['Size'][i] for i in range(len(self.P))}
        self.opening_cost = {self.links[i]: link_data['Opening Cost'][i] for i in range(len(link_data))}
        self.capacity_cost = {self.links[i]: link_data['Capacity Cost'][i] for i in range(len(link_data))}
        self.duration = {self.links[i]: link_data['Duration'][i] for i in range(len(link_data))}
        self.locations = pd.concat([supplier_data.iloc[:, :3].rename(columns={'SupplierID': 'Location'}),
                                    depot_data.iloc[:, :3].rename(columns={'DepotID': 'Location'}),
                                    customer_data.iloc[:, :3].rename(columns={'CustomerID': 'Location'})])
        self.locations.set_index([self.locations['Location']], inplace=True)
        self.distance = {a: np.hypot(self.locations.loc[a[0]]['LocationX'] - self.locations.loc[a[1]]['LocationX'],
                                     self.locations.loc[a[0]]['LocationY'] - self.locations.loc[a[1]]['LocationY']) for
                         a in
                         self.links}
        self.demand = {self.demand_set[i]: demand_data['Amount'][i] for i in range(len(demand_data))}
        self.cum_demand = {(c, p, t): sum(self.demand[c, p, f] for f in range(self.start, t + 1)
                                          if (c, p, f) in self.demand_set) for (c, p, t) in self.customer_product_time}
        self.backlog_pen = {self.customer_product[i]: backlog_data['Amount'][i] for i in
                            range(len(backlog_data))}
        self.min_prod = {(s, p): 0 for s in self.S for p in self.P}
        self.max_prod = {(s, p): 0 for s in self.S for p in self.P}
        for i in range(len(production_data)):
            self.min_prod[self.supplier_product[i]] = production_data['Minimum'][i]
            self.max_prod[self.supplier_product[i]] = production_data['Maximum'][i]
        self.solution = {}
        self.objective = np.inf

    # Function that updates this problem object's solution based on a solution file
    def read_solution(self, instance_name):
        self.solution = {'x': {(i, j, p, str(t)): 0 for (i, j, p, t) in self.link_product_time},
                         'l': {(i, j): 0 for (i, j) in self.links},
                         'v': {(i, j): 0 for (i, j) in self.links},
                         'k': {(i, j, str(t)): 0 for (i, j, t) in self.link_time},
                         'r': {(s, p, str(t)): 0 for (s, p, t) in self.supplier_product_time},
                         'I': {(i, p, str(t)): 0 for (i, p, t) in self.dc_product_time}}
        # Read solution
        with open('Solutions/' + instance_name + '.sol', newline='\n') as file:
            reader = csv.reader((line.replace('  ', ' ') for line in file), delimiter=' ')
            header = next(reader)  # Skip header
            self.objective = header[-1]
            for var, value in reader:
                name = tuple(var[2:-1].split(','))
                if var[0] not in self.solution.keys():
                    self.solution[var[0]] = {}
                self.solution[var[0]][name] = float(value)

    def compute_objective(self):
        # Opening + capacity costs
        tot_opening_costs = 0
        tot_capacity_costs = 0
        for link in self.links:
            if self.solution['v'][link] > 0:
                extra_opening_cost = self.opening_cost[link]
                tot_opening_costs += extra_opening_cost
                extra_capacity_cost = self.capacity_cost[link] * self.solution['v'][link]
                tot_capacity_costs += extra_capacity_cost
        # Distance costs
        tot_distance_costs = 0
        for link in self.links:
            if self.solution['v'][link] > 0:
                total_trucks_sent = sum([self.solution['k'][link + (str(t),)] for t in self.T])
                extra_distance_cost = total_trucks_sent * self.distance[link]
                tot_distance_costs += extra_distance_cost
        # Holding costs
        tot_holding_costs = 0
        for d in self.D:
            for p in self.P:
                extra_holding_cost = self.holding_cost[d] * sum([self.solution['I'][d, p, str(t)]
                                                                 * self.product_volume[p] for t in self.T])
                tot_holding_costs += extra_holding_cost
        # Backlog costs
        tot_backlog_costs = 0
        for c, p, t in self.customer_product_time:
            extra_backlog = self.backlog_pen[c, p] * (self.solution['I'][c, p, str(t)] - self.cum_demand[c, p, t]) ** 2
            tot_backlog_costs += extra_backlog
        return tot_opening_costs + tot_capacity_costs + tot_distance_costs + tot_holding_costs + tot_backlog_costs

    # Log the amount of trucks sent over each link at each point in time
    def log_k(self):
        k = {}
        for link in self.links:
            if self.solution['l'][link] == 1:
                k[link] = [round(self.solution['k'][link + (str(t),)]) for t in self.T]
        print()
        print('Amount of trucks sent over each link at each point in time:')
        print('-' * 70)
        for link, trucks in k.items():
            print(link, trucks)

    def log_backlog(self):
        total_backlog_penalty = 0
        print()
        print('Backlog overview:')
        print('-' * 70)
        for c, p, t in self.customer_product_time:
            print(c, p, t)
            print('-' * 70)
            print('Total demand:', self.cum_demand[c, p, t])
            print('Inventory:', self.solution['I'][c, p, str(t)])
            print('Difference:', self.solution['I'][c, p, str(t)] - self.cum_demand[c, p, t])
            print('Difference squared:', (self.solution['I'][c, p, str(t)] - self.cum_demand[c, p, t]) ** 2)
            print('b:', self.backlog_pen[c, p])
            extra_penalty = self.backlog_pen[c, p] * (self.solution['I'][c, p, str(t)] - self.cum_demand[c, p, t]) ** 2
            print('Incurred penalty:', extra_penalty)
            print('-' * 70)
            total_backlog_penalty += extra_penalty
        print(total_backlog_penalty)

    def log_solution(self, display=None, draw_settings=None):
        print()
        print('Solution overview:')
        print('-' * 70)
        for t in self.T:
            if display:
                display.draw(t, draw_settings)
            print('Time', t)
            print('-' * 70)
            # Depot inventory
            for d in self.D:
                print(d, '| Inventory:', round(self.solution['I'][d, 'P1', str(t)], 2), '(Capacity',
                      str(round(self.capacity[d] /
                                self.product_volume['P1'], 2)) + ')')
            # Customer inventory
            for c in self.C:
                print(c, '| Inventory:', round(self.solution['I'][c, 'P1', str(t)], 2),
                      'Cumulative demand:', self.cum_demand[c, 'P1', t])

            print('-' * 70)
            # Supplier production
            for s in self.S:
                production = sum([self.solution['x'][(s, j, 'P1', str(t))] for j in self.D_and_C])
                print(s, '| Production:', round(production, 2), '(Min', self.min_prod[(s, 'P1')],
                      'Max', str(self.max_prod[(s, 'P1')]) + ')')
            print('-' * 70)
            # Outgoing transport
            print('Outgoing transport:')
            for i in self.S_and_D:
                for j in self.D_and_C:
                    if i is not j:
                        transport = self.solution['x'][(i, j, 'P1', str(t))]
                        if transport > 0:
                            print(i, '->', j, '| Units:', round(transport, 2),
                                  'Trucks:', round(self.solution['k'][i, j, str(t)]))
            print('-' * 70)
            # Arriving transport
            print('Arriving transport:')
            for f in range(1, t + 1):
                for i in self.S_and_D:
                    for j in self.D_and_C:
                        if i is not j:
                            # Check if transport would arrive now
                            if f + self.duration[(i, j)] == t:
                                transport = self.solution['x'][(i, j, 'P1', str(f))]
                                if transport > 0:
                                    print(i, '->', j, '| Units:', round(transport, 2),
                                          'Trucks:', round(self.solution['k'][i, j, str(f)]), '(Sent at time',
                                          str(f) + ')')

            input('Press enter to continue..')
            print()

    # Function that outputs the buildup of different cost types
    def log_objective(self, summary_only=False):
        print()
        print('Objective overview:')
        print('-' * 70)
        # Opening costs
        tot_opening_costs = 0
        for link in self.links:
            if link in self.solution['l'].keys():
                if self.solution['l'][link] == 1:
                    extra_opening_cost = self.opening_cost[link]
                    if not summary_only:
                        print(link, '| Cost:', extra_opening_cost)
                    tot_opening_costs += extra_opening_cost
        if not summary_only:
            print('Total opening costs:', round(tot_opening_costs, 2))
            print('-' * 70)
        # Capacity costs
        tot_capacity_costs = 0
        for link in self.links:
            if link in self.solution['v'].keys():
                if self.solution['v'][link] > 0:
                    extra_capacity_cost = self.capacity_cost[link] * self.solution['v'][link]
                    if not summary_only:
                        print(link, '| Amount: ', round(self.solution['v'][link], 2), '| Cost per:',
                              self.capacity_cost[link], '| Total cost:', round(extra_capacity_cost, 2))
                    tot_capacity_costs += extra_capacity_cost
        if not summary_only:
            print('Total capacity costs:', round(tot_capacity_costs, 2))
            print('-' * 70)
        # Distance costs
        tot_distance_costs = 0
        for link in self.links:
            if link in self.solution['v'].keys():
                if self.solution['v'][link] > 0:
                    total_trucks_sent = sum([self.solution['k'][link + (str(t),)] for t in self.T])
                    extra_distance_cost = total_trucks_sent * self.distance[link]
                    if not summary_only:
                        print(link, '| Total trucks sent on link: ', round(total_trucks_sent),
                              '| Cost per:', round(self.distance[link], 2), '| Total cost:',
                              round(extra_distance_cost, 2))
                    tot_distance_costs += extra_distance_cost
        if not summary_only:
            print('Total distance costs:', round(tot_distance_costs, 2))
            print('-' * 70)
        # Holding costs
        tot_holding_costs = 0
        for d in self.D:
            if not summary_only:
                print(d, '| Holding costs:', self.holding_cost[d], 'Capacity:', self.capacity[d])
            for p in self.P:
                if not summary_only:
                    print(d, p, '| Inventory:', [round(self.solution['I'][d, p, str(t)] * self.product_volume[p], 2)
                                                 for t in self.T])
                extra_holding_cost = self.holding_cost[d] * sum([self.solution['I'][d, p, str(t)]
                                                                 * self.product_volume[p] for t in self.T])
                if not summary_only:
                    print(d, p, '| Total inventory:', round(sum([round(self.solution['I'][d, p, str(t)]
                                                                       * self.product_volume[p], 2)
                                                                 for t in self.T]), 2),
                          '| Total cost:', round(extra_holding_cost, 2))
                tot_holding_costs += extra_holding_cost
        if not summary_only:
            print('Total holding costs:', round(tot_holding_costs, 2))
            print('-' * 70)
        # Backlog costs
        tot_backlog_costs = 0
        for c in self.C:
            customer_backlog = 0
            if not summary_only:
                print(c, '|')
                print('-' * 70)
            for p in self.P:
                if not summary_only:
                    print(c, p, '|', [round(self.cum_demand[c, p, t], 2) for t in self.T],
                          '- Cumulative demand over time')
                    print(c, p, '|', [round(self.solution['I'][c, p, str(t)], 2) for t in self.T],
                          '- Total delivered over time')
                product_backlog = 0
                for t in self.T:
                    product_backlog += self.backlog_pen[c, p] * ((self.solution['I'][c, p, str(t)]
                                                                  - self.cum_demand[c, p, t]) ** 2)
                customer_backlog += product_backlog
                if not summary_only:
                    print(c, p, '| Product backlog costs:', product_backlog)
                    print('-' * 70)
            if not summary_only:
                print(c, '| Customer backlog costs:', round(customer_backlog, 2))
                print('-' * 70)
        for c, p, t in self.customer_product_time:
            extra_backlog = self.backlog_pen[c, p] * abs(self.solution['I'][c, p, str(t)] - self.cum_demand[c, p, t])
            tot_backlog_costs += extra_backlog
        if not summary_only:
            print('Total backlog costs:', round(tot_backlog_costs, 2))
            print('-' * 70)
        tot_objective = tot_opening_costs + tot_capacity_costs + tot_distance_costs + tot_holding_costs + tot_backlog_costs
        print('Total opening costs  |', round(tot_opening_costs, 2))
        print('Total capacity costs |', round(tot_capacity_costs, 2))
        print('Total distance costs |', round(tot_distance_costs, 2))
        print('Total holding costs  |', round(tot_holding_costs, 2))
        print('Total backlog costs  |', round(tot_backlog_costs, 2))
        print('-' * 70)
        print('Total costs          |', round(tot_objective, 2))
        print('-' * 70)
        return {
            'backlog': tot_backlog_costs,
            'total': tot_objective
        }

    def log_production(self):
        for s in self.S:
            print(s, '|')
            print('-' * 70)
            for p in self.P:
                production = [round(sum(self.solution['x'][s, j, p, str(t)] for j in self.D_and_C), 2) for t in self.T]
                print(p, '|', production)
            print('-' * 70)

    def log_depot(self, d):
        for t in self.T:
            print('Time', t)
            print('-' * 70)
            # Depot inventory
            print(d, '| Inventory:', round(self.solution['I'][d, 'P1', str(t)], 2),
                  '(Capacity', str(round(self.capacity[d] / self.product_volume['P1'], 2)) + ')')
            print('-' * 70)
            # Outgoing transport
            print('Outgoing transport:')
            total_outgoing = 0
            for j in self.D_and_C:
                if d != j:
                    transport = self.solution['x'][(d, j, 'P1', str(t))]
                    if transport > 0:
                        total_outgoing += transport
                        print(d, '->', j, '| Units:', round(transport, 2))
            print('Total outgoing units:', round(total_outgoing, 2))
            print('-' * 70)
            # Arriving transport
            print('Arriving transport:')
            total_incoming = 0
            for f in range(1, t + 1):
                for j in self.S_and_D:
                    if d != j:
                        # Check if transport would arrive now
                        if f + self.duration[(j, d)] == t:
                            transport = self.solution['x'][(j, d, 'P1', str(f))]
                            if transport > 0:
                                total_incoming += transport
                                print(j, '->', d, '| Units:', round(transport, 2), '(Sent at time', str(f) + ')')
            print('Total incoming units:', round(total_incoming, 2))

            input('Press enter to continue..')
            print()

    def verify_constraints(self):
        # 1 - Link opening constraint
        for link in self.links:
            assert self.solution['l'][link] * 10000 >= self.solution['v'][link], 'Constraint 1 violation'
        # 2 - Link capacity constraint
        for link in self.links:
            for t in self.T:
                t = str(t)
                assert round(self.solution['k'][link[0], link[1], t]) <= round(self.solution['v'][link])
        # 3 - Required trucks constraint
        for i, j in self.links:
            for t in self.T:
                t = str(t)
                volume = sum([self.product_volume[p] * self.solution['x'][i, j, p, t] for p in self.P])
                assert self.solution['k'][i, j, t] >= round(volume / self.truck_size)
        # 4 - Min production constraint
        for s, p, t in self.supplier_product_time:
            t = str(t)
            production = sum([self.solution['x'][s, j, p, t] for j in self.D_and_C])
            assert round(production, 2) >= self.min_prod[s, p] * self.solution['r'][s, p, t]
        # 5 - Max production constraint
        for s, p, t in self.supplier_product_time:
            t = str(t)
            production = sum([self.solution['x'][s, j, p, t] for j in self.D_and_C])
            assert round(production, 2) <= self.max_prod[s, p] * self.solution['r'][s, p, t]
        # 6 - Depot outflow constraint
        for d, p, t in self.depot_product_time:
            outflow = sum([self.solution['x'][d, j, p, str(t)] for j in self.D_and_C if (d, j) in self.links])
            inflow = sum([self.solution['x'][j, d, p, str(t - self.duration[j, d])] for j in self.S_and_D
                          if (j, d) in self.links and t - self.duration[j, d] >= self.start])
            assert round(outflow, 2) <= round(self.solution['I'][d, p, str(t - 1)] + inflow, 2) + 0.01
        # 7 - Depot capacity constraint
        for d in self.D:
            for t in self.T:
                t = str(t)
                volume = sum([self.product_volume[p] * self.solution['I'][d, p, t] for p in self.P])
                assert volume <= self.capacity[d]
        # 8 - Flow constraints
        for i, p, t in self.dc_product_time:
            if t > 0:
                outflow = sum([self.solution['x'][i, j, p, str(t)] for j in self.D_and_C if (i, j) in self.links])
                inflow = sum([self.solution['x'][j, i, p, str(t - self.duration[j, i])] for j in self.S_and_D
                              if (j, i) in self.links and t - self.duration[j, i] >= self.start])
                assert round(self.solution['I'][i, p, str(t)], 4) - round(self.solution['I'][i, p, str(t - 1)] + inflow
                                                                          - outflow, 4) <= 0.0001
        # 9 - Inventories start at 0
        for i in self.D_and_C:
            for p in self.P:
                assert self.solution['I'][i, p, '0'] == 0
        # 10 - Total inventories must match cumulative demand
        for c in self.C:
            for p in self.P:
                assert round(self.solution['I'][c, p, str(self.end)], 5) == round(self.cum_demand[c, p, self.end], 5)
        print('Constraints succesfully verified.')
        return

    # Call display on this problem's solution showing only opened links and their capacities
    def display(self, integer=False):
        disp = Display(self)
        disp.draw(0, {'show_capacities': True, 'show_trucks': False, 'show_transport': False, 'show_inventory': False,
                      'integer': integer})
