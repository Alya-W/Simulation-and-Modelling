"""
Simulation and animation of a sidewalk where infected agents can transmiss
infection with a certain probability and in a certain distance.
"""

import statistics
from matplotlib import pyplot as plt, colors
from matplotlib.animation import FuncAnimation
import random

rand = random.Random()
SIDEWALK_WIDTH = 10  # This is the y-dimension of the sidewalk
SIDEWALK_LENGTH = 200  # This is the x-dimension of the sidewalk
TRANSPROB = 0.1  # Probability of transmission of virus in 1 time step at distance 1
INFECTED_PROP = 0.1  # The proportion of people who enter the simulation already carrying the virus
INTERARRIVALS = 3  # Average number of time steps between arrivals (each side handled separately)

# Setup for graphical display
colourmap = colors.ListedColormap(["lightgrey", "green", "red", "yellow"])
normalizer = colors.Normalize(vmin=0.0, vmax=3.0)

all_agents = []


# An agent representing a single person traversing the sidewalk.  Simple movement is demonstrated.  It is up
# to the user to implement behaviour according to the assignment specification, and to collect data as
# necessary.
# A person occupies an x,y position on the sidewalk.  While the person can access their own position, they
# cannot change their coordinates directly.  Instead, they must make movement requests to the sidewalk, which
# (if the move is valid) updates the person's x and y coordinates.
class Person:
    def __init__(self, id, sidewalk, direction):
        self.id = id
        self.active = False
        self.sidewalk = sidewalk
        self.infected = True if rand.random() <= INFECTED_PROP else False
        self.newlyinfected = False
        self.direction = direction
        self.num_of_infections = 0  # number of agents that got infected by one agent

        self.x = None
        self.y = rand.randint(0, SIDEWALK_WIDTH - 1)

    def enter_sidewalk(self, x, y):
        if self.sidewalk.enter_sidewalk(self, x, y):
            self.active = True
            all_agents.append(self)

    # This is the method that is called by the simulation once for each time step.  It is during this call
    # that the agent is active and can take action: examining surroundings, attempting to move, etc.
    # This method should only be called when the agent's 'active' flag is true, but you might want to check here
    # as well for safety.

    def step(self):
        # Simple random movement in one of four cardinal directions (written for clarity, not efficiency!)
        desiredx = self.x
        desiredy = self.y

        # leave the sidewalk if an agent reached the end
        if (self.x == 0 and self.direction == -1) or (self.x == SIDEWALK_LENGTH - 1 and self.direction == 1):
            self.sidewalk.leave_sidewalk(self)

        # if there is an agent in from of the current agent
        elif self.sidewalk.storage.get_item(self.x + self.direction, self.y) is not None:
            # move right or left with the same probability
            change_y = random.choices([-1, 1], [0.5, 0.5])[0]
            desiredy = self.y + change_y
            desiredy = max(min(desiredy, SIDEWALK_WIDTH - 1), 0)
            self.sidewalk.attemptmove(self, desiredx, desiredy)

        # if there is an agent to the right or to the left side of the current agent
        elif self.sidewalk.storage.get_item(self.x, self.y + 1) \
                or self.sidewalk.storage.get_item(self.x, self.y - 1) is not None:
            # move forward, left or right
            change = random.choices(["forward", "left or right"], [0.6, 0.4])[0]
            if change == "forward":
                desiredx = self.x + self.direction
                desiredx = max(min(desiredx, SIDEWALK_LENGTH - 1), 0)
                self.sidewalk.attemptmove(self, desiredx, desiredy)
            elif change == "left or right":
                change_y = random.choices([-1, 1], [0.5, 0.5])[0]
                desiredy = self.y + change_y
                desiredy = max(min(desiredy, SIDEWALK_WIDTH - 1), 0)
                self.sidewalk.attemptmove(self, desiredx, desiredy)

        # get to this point only if there is no neighbour agents
        else:
            change = random.choices(["forward", "back", "left or right"], [0.7, 0.1, 0.2])[0]

            if change == "forward":
                desiredx = self.x + self.direction

            elif change == "back":
                if self.direction == 1:
                    desiredx = self.x - 1
                elif self.direction == -1:
                    desiredx = self.x + 1

            elif change == "left or right":
                change_y = random.choices([-1, 1], [0.5, 0.5])[0]
                desiredy = self.y + change_y

            # Ensure x and y don't go off edge of sidewalk
            desiredx = max(min(desiredx, SIDEWALK_LENGTH - 1), 0)
            desiredy = max(min(desiredy, SIDEWALK_WIDTH - 1), 0)
            self.sidewalk.attemptmove(self, desiredx, desiredy)

    def __str__(self):
        return "id: %d  x: %d  y: %d" % (self.id, self.x, self.y)


# The class representing the sidewalk itself.  Agents must enter the sidewalk to be active in the simulation.
# The sidewalk controls agents' positions/movement.
class Sidewalk:

    def __init__(self):
        # Tracking of positions of agents
        self.storage = SWGrid()

        # Bitmap is for graphical display
        self.bitmap = [[0.0 for i in range(SIDEWALK_LENGTH)] for j in range(SIDEWALK_WIDTH)]

    # An agent must enter the sidewalk at one of the ends (i.e., with an x coordinate of either zero or
    # the maximum.  They may attempt to enter at any y coordinate.  The function returns true if successful, false
    # if the agent is not added to the sidewalk (e.g., if the desired square is already occupied.)
    # The method will set the agent's x and y position if the attempt is successful.
    def enter_sidewalk(self, person, x, y):
        # New entrant to the sidewalk, must attempt to start at one end
        # if x!=0 and x!=SIDEWALK_LENGTH-1:
             # print("Must start at an end!")
             # return False

        # Only allow move if space not currently occupied
        if self.storage.isoccupied(x, y):
            print("Move rejected: occupied")
            return False
        self.storage.add_item(x, y, person)
        person.x = x
        person.y = y
        return True

    # An agent must leave the sidewalk at one of the ends (i.e., with an x coordinate of either zero or
    # the maximum.  The function returns true if successful, false if not.
    # You should be sure to get any information you want from the agent before doing so, because you may not
    # have a handle for it afterwards.
    def leave_sidewalk(self, person):
        # Must attempt to leave at one end
        if person.x != 0 and person.x != SIDEWALK_LENGTH - 1:
            print("Must leave at an end!")
            return False

        self.storage.remove_item(person)

    # Returns True if person successfully moved, False if not (e.g., the desired square is occupied).
    # An agent can only move one square in a cardinal direction from its current position; any other attempt will
    # be rejected.
    # The method will set the agent's x and y position if the attempt is successful.
    def attemptmove(self, person, x, y):

        # Reject move of more than 1 square
        if (abs(person.x - x) + abs(person.y - y)) > 1:
            print("Attempt to move more than one square!")
            return False

        # Only allow move if space not currently occupied
        if self.storage.isoccupied(x, y):
            # print("Move rejected: occupied")
            return False
        person.x = x
        person.y = y
        self.storage.move_item(x, y, person)
        return True

    # When called, infects new agents (with some probability) who are in proximity to infected agents.  The risk
    # is equal to the simulation parameter at distance of 1, and decreases with greater distance.
    # You may add to this function, e.g., for gathering data, but do not modify the actual determination of infection.
    def spread_infection(self):
        for person in self.storage.get_list():
            currentx = person.x
            currenty = person.y
            if person.infected:
                # Find all agents within a square of 'radius' 2 of the infected agent
                for x in range(currentx - 2, currentx + 3):
                    for y in range(currenty - 2, currenty + 3):
                        target = self.storage.get_item(x, y)

                        # If target is not infected, infect with probability dependent on distance
                        if target is not None and not target.infected:
                            riskfactor = 1 / ((currentx - x) ** 2 + (currenty - y) ** 2)
                            tranmission_prob = TRANSPROB * riskfactor
                            if rand.random() < tranmission_prob:
                                person.num_of_infections += 1
                                target.infected = True
                                target.newlyinfected = True
                                print('New infection! %s' % target)

    # Updates the graphic for display
    def refresh_image(self):
        self.bitmap = [[0.0 for i in range(SIDEWALK_LENGTH)] for j in range(SIDEWALK_WIDTH)]
        for person in self.storage.get_list():
            x = person.x
            y = person.y
            colour = 1
            if person.newlyinfected:
                colour = 3
            elif person.infected:
                colour = 2
            self.bitmap[y][x] = colour

    # Function that is called at each time step, to execute the step.  Calls the step() function of every active
    # agent, spreads infection after the agents have moved, and updates the image for display.  You will need to add
    # code here to, for example, have new agents enter.
    def run_step(self, time_step):
        for person in self.storage.get_list():
            if person.active:
                person.step()

        if time_step % INTERARRIVALS == 0:
            # every 3rd time_stamp
            self.new_agents(time_step, 1, 0)
            self.new_agents(time_step, -1, SIDEWALK_LENGTH - 1)

        self.spread_infection()
        self.refresh_image()

    def new_agents(self, time_step, direction, starting_point):
        """ Add new agents (between 1 and 3 every time the function is called)"""
        num = random.randint(1, 3)
        personlist = [Person(time_step, sw, direction) for _ in range(num)]
        for person in personlist:
            person.enter_sidewalk(starting_point, person.y)

    # Returns true if x,y is occupied by an agent, false otherwise.  This is the only information that an agent
    # has about other agents; it can't (e.g.) see if other agents are infected!
    def isoccupied(self, x, y):
        return self.storage.isoccupied(x, y)


# Used to provide storage, lookup of occupants of sidewalk
class SWGrid:
    def __init__(self):
        self.dic = dict()

    def isoccupied(self, x, y):
        # self.check_coordinates(x, y)
        return (x, y) in self.dic

    # Stores item at coordinates x, y.  Throws an exception if the coordinates are invalid.  Returns false if
    # unsuccessful (e.g., the square is occupied) or true if successful.
    def add_item(self, x, y, item):
        self.check_coordinates(x, y)
        if (x, y) in self.dic:
            return False
        self.dic[(x, y)] = item
        return True

    # Removes item from its current coordinates (which do not need to be provided) and stores it
    # at coordinates x, y.  Throws an exception if the coordinates are invalid or if the square is occupied.
    def move_item(self, x, y, item):
        self.check_coordinates(x, y)
        if self.isoccupied(x, y):
            raise Exception("Move to occupied square!")

        # Find and remove previous location.  Assumed state is valid (meaning only one entry per x,y key)
        oldloc = next(key for key, value in self.dic.items() if value == item)
        del self.dic[oldloc]
        self.add_item(x, y, item)

    # Removes item (coordinates do not need to be provided)
    # Throws an exception if the item doesn't exist.
    def remove_item(self, item):
        # Find and remove previous location.  Assumed state is valid (meaning only one entry per x,y key)
        oldloc = next(key for key, value in self.dic.items() if value == item)
        if oldloc is None:
            raise Exception('Attempt to remove non-existent item!')
        del self.dic[oldloc]

    def get_item(self, x, y):
        # self.check_coordinates(x, y)
        return self.dic.get((x, y), None)

    # Returns a list of all agents in the simulation.
    def get_list(self):
        return list(self.dic.values())

    def check_coordinates(self, x, y):
        if x < 0 or x >= SIDEWALK_LENGTH or y < 0 or y >= SIDEWALK_WIDTH:
            raise Exception("Illegal coordinates!")


#
# Run simulation
#

sw = Sidewalk()

# Set up graphical display
display = plt.figure(figsize=(15, 5))
image = plt.imshow(sw.bitmap, cmap=colourmap, norm=normalizer, animated=True)

# Track time step
t = 0


# The graphical routine runs the simulation 'clock'; it calls this function at each time step.  This function
# calls the sidewalk's run_step function, as well as updating the display.  You should not implement your simulation
# here, but instead should do so in the run_step method.
def updatefigure(*args):
    global t
    t += 1

    if t % 100 == 0:
        print("Time: %d" % t)
    sw.run_step(t)
    sw.refresh_image()
    image.set_array(sw.bitmap)
    return image,


# Sets up the animation, and begins the process of running the simulation.  As configured below, it will
# run for 1000 steps.  After this point, it will simply stop, but the window will remain open.  You can close
# the window to proceed to the code below these lines (where you could add, for example, output of your statistics.
#
# You can change the speed of the simulation by changing the interval, and the duration by changing frames.
anim = FuncAnimation(display, updatefigure, frames=1000, interval=100, blit=True, repeat=False)
plt.show()

print("Done!")


def print_statistics():
    num_of_agents = 0
    num_infected_agents = []
    for i in all_agents:
        num_of_agents += 1
        if i.infected:
            num_infected_agents.append(i.num_of_infections)
    print("One infected agent got", round(statistics.mean(num_infected_agents), 3), "agents infected on average.\n"
          "STDEV:", round(statistics.stdev(num_infected_agents), 3))

    print("Overall number of infected agents divided by the total number of agents:",
          round(len(num_infected_agents)/num_of_agents, 3))

    # plotting distribution of num_of_infected_agents

    plt.hist(num_infected_agents)
    plt.title("Distribution of infected agents (part 1):")
    plt.show()


print_statistics()
