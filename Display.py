import matplotlib.pyplot as plt


class Display:
    def __init__(self, problem):
        self.problem = problem
        self.fig, self.ax = plt.subplots()
        # Display settings
        self.fig.canvas.set_window_title('Display')
        plt.ion()

    def draw(self, t, settings=None):
        self.ax.cla()
        self.ax.axis('equal')
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22"]

        def annotate_link(link, text):
            a, b = self.problem.locations.loc[link[0]], self.problem.locations.loc[link[1]]
            x = [a['LocationX'], b['LocationX']]
            y = [a['LocationY'], b['LocationY']]
            plt.plot(x, y, color=colors[0])
            self.ax.text(0.5 * sum(x), 0.5 * sum(y), text, color="black", fontsize=9, fontweight='bold')

        if settings:
            if self.problem.solution != {}:
                for link in self.problem.links:
                    if settings['show_capacities']:
                        if link in self.problem.solution['v']:
                            v = self.problem.solution['v'][link]
                            if v > 0:
                                text = str(round(v, 2)) if not settings['integer'] else str(int(v))
                                annotate_link(link, text)
                    if settings['show_trucks']:
                        link_time = link + (str(t),)
                        k = self.problem.solution['k'][link_time]
                        if k > 0:
                            annotate_link(link, 'k=' + str(round(k, 2)))
                    if settings['show_transport']:
                        link_product_time = link + ('P1', str(t),)
                        transport = self.problem.solution['x'][link_product_time]
                        if transport > 0:
                            annotate_link(link, 'x=' + str(round(transport, 2)))

                if settings['show_inventory']:
                    for d in self.problem.D:
                        location = self.problem.locations.loc[d]
                        x, y = location.LocationX, location.LocationY
                        I = self.problem.inventory_depot(d, 'P1', t)
                        self.ax.text(x + 0.25, y - 0.25, round(I, 2), color="black", fontsize=12)

        # Draw location markers
        for i, location in self.problem.locations.iterrows():
            x, y = location.LocationX, location.LocationY
            color_indices = {'S': 1, 'D': 3, 'C': 2}
            self.ax.plot(x, y, 'o', color=colors[color_indices[location['Location'][0]]])
            self.ax.text(x, y, '$' + location['Location'] + '$', color="black", fontsize=11)

        # plt.grid()
        plt.show()
