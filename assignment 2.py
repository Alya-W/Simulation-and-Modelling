"""
Simulation of a Pizza Restaurant. Cooking and delivery.
"""

import simpy
from random import random
from numpy import average
import numpy as np
from math import sqrt
from matplotlib import pyplot as plt

TIME = 180  # in minutes (for how long the simulation will run)
VELOCITY = 30  # km/h  (velocity of a driver)
TIME_TO_COOK_PIZZA = 10  # in minutes
PIZZA_TEMP = 150  # in F (temp. of pizza straight from the oven)
OVEN_CAPACITY = 4


def utilization_rate(time_stamps):
    differences = [(0, time_stamps[0][0])]
    for y in range(len(time_stamps) - 1):
        if time_stamps[y][1] < time_stamps[y + 1][0]:
            differences.append((time_stamps[y][1], time_stamps[y + 1][0]))

    util = 0
    for i, j in differences:
        resting_time = j - i
        util += resting_time
    return round((100 - util / TIME * 100), 2)


class PizzaRestaurant:

    def __init__(self):
        self.drivers = 0
        self.order_rate = 0  # in minutes
        self.delivery_radius = 0  # in km
        self.velocity = VELOCITY * 16.667  # converting from km/h to m/min

        self.order_oven = []  # Time from order placement to pizza going in the oven
        self.cooked_driver_pickup = []  # Time from pizza finished cooking until delivery driver collects it
        self.total_time = []  # Time from order placement till customer receives pizza
        self.pizza_temperature = []  # Temperature at delivery
        self.number_of_pizzas = 0
        self.delivered_pizzas = 0

        self.ovens_utilization = []
        self.drivers_utilization = []

    def runsim(self, number_of_drivers, order_rate, delivery_radius):
        self.drivers = number_of_drivers
        self.order_rate = order_rate
        self.delivery_radius = delivery_radius * 1000

        env = simpy.Environment()
        oven = simpy.Resource(env, capacity=OVEN_CAPACITY)
        drivers = simpy.Resource(env, capacity=number_of_drivers)
        env.process(self.pizza(env, oven, drivers))
        env.run(until=TIME)

    def pizza(self, env, oven, drivers):
        """ Generates new orders"""
        while True:
            # yield env.timeout(random.normal(self.order_rate, 0.7))
            env.process(self.order(env, oven, drivers))
            yield env.timeout(np.random.normal(self.order_rate, 0.7))

    def order(self, env, oven, drivers):
        """ Cooks pizza"""
        order_time = env.now

        with oven.request() as request:
            yield request

            oven_time = env.now
            self.order_oven.append(oven_time - order_time)
            yield env.timeout(TIME_TO_COOK_PIZZA)
            cooked = env.now

            self.number_of_pizzas += 1
            self.ovens_utilization.append((order_time, cooked))

            c = self.delivery(env, drivers, order_time, cooked)
            env.process(c)

    def delivery(self, env, drivers, order_time, cooked):
        """ Delivers pizza"""
        delivery_placed = env.now

        with drivers.request() as request:
            yield request

            collected = env.now
            self.cooked_driver_pickup.append(collected - cooked)

            distance = self.delivery_radius * sqrt(random())

            time_to_deliver = distance / self.velocity

            yield env.timeout(time_to_deliver)

            delivered = env.now
            self.total_time.append(delivered - order_time)
            pizza_temp = PIZZA_TEMP - (delivered - cooked)
            self.pizza_temperature.append(pizza_temp)

            yield env.timeout(2)

            self.delivered_pizzas += 1

            yield env.timeout(time_to_deliver)

            finished = env.now

            self.drivers_utilization.append((delivery_placed, finished))

    def statistic(self):
        """ Print and plot statistics"""
        print("Time from order placement to pizza going in the oven:", round(average(self.order_oven), 2))
        plt.figure(1)
        plt.hist(self.order_oven)
        plt.title("Time from order placement to pizza going in the oven")

        print("Time from pizza finished cooking until delivery driver collects it:",
              round(average(self.cooked_driver_pickup), 2))
        plt.figure(2)
        plt.hist(self.cooked_driver_pickup)
        plt.title("Time from pizza finished cooking until delivery driver collects it")

        print("Total time from order placement to receiving pizza:", round(average(self.total_time), 2))
        plt.figure(3)
        plt.hist(self.total_time)
        plt.title("Total time from order placement to receiving pizza")

        print("Temperature at delivery:", round(average(self.pizza_temperature), 2))
        plt.figure(4)
        plt.hist(self.pizza_temperature)
        plt.title("Temperature at delivery")
        plt.show()

        print("Total number of pizzas cooked:", int(average(self.number_of_pizzas)))
        print("Total number of pizzas delivered:", int(average(self.delivered_pizzas)))
        print("Ovens' utilization:", utilization_rate(self.ovens_utilization), "%")
        print("Drivers' utilization:", utilization_rate(self.drivers_utilization), "%")


if __name__ == '__main__':
    sim = PizzaRestaurant()
    sim.runsim(5, 5, 10)
    sim.statistic()

    """PART B"""

    # part 1
    DELIVERED_WITHIN = 49
    number_of_cases = 0  # number of cases when the delivery was made within 50 minutes
    percentages = []  # we will run the simulation for 200 times, hence, we want to keep tracking of all percentages

    for i in range(200):
        sim = PizzaRestaurant()
        sim.runsim(5, 5, 10)
        for i in sim.total_time:
            if i <= DELIVERED_WITHIN:
                number_of_cases += 1
        percentages.append(number_of_cases/len(sim.total_time))
        number_of_cases = 0

    print("\n\nProbability of being delivered within", DELIVERED_WITHIN, "minutes:", round(average(percentages) * 100, 2))

    # part 2
    NUMBER_OF_DRIVERS = 7

    drivers_util = []
    for i in range(200):
        sim = PizzaRestaurant()
        sim.runsim(NUMBER_OF_DRIVERS, 5, 10)
        for i in sim.total_time:
            if i <= 30:
                number_of_cases += 1
        percentages.append(number_of_cases/len(sim.total_time))
        number_of_cases = 0
        drivers_util.append(utilization_rate(sim.drivers_utilization))

    print("\nProbability of being delivered within 30 minutes:", round(average(percentages) * 100, 2),
          "\nNumber of drivers required:", NUMBER_OF_DRIVERS,
          "\nDrivers' Utilisation rate:", round(average(drivers_util), 2), "%")
