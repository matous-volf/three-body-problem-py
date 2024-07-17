import math
import os
from abc import ABC, abstractmethod
from copy import deepcopy
from tkinter import *
from typing import List

import numpy as np
from numpy.linalg import norm
from scipy.constants import gravitational_constant

colors = [
    "#fae4be",
    "#faafb6",
    "#926fbf",
    "#e890c5",
    "#c76fc7",
]

mimon_image_filenames = sorted([f for f in os.listdir("images") if os.path.isfile(os.path.join("images", f))])


class Body:
    def __init__(self, mass: float, position: List[float], velocity: List[float]):
        self.mass = mass
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity, dtype=float)


class Renderer(ABC):
    def __init__(self, bodies: List[Body], canvas: Canvas):
        self.bodies = bodies
        self.canvas = canvas

    @abstractmethod
    def render(self):
        pass


class OvalRenderer(Renderer):
    def __init__(self, bodies: List[Body], canvas: Canvas,
                 oval_radius: float = 5, oval_radius_affect_by_mass: bool = False, oval_fill_color: str | None = None,
                 oval_outline_color: str = "#000000"):
        super().__init__(bodies, canvas)
        self.oval_radius = oval_radius
        self.oval_radius_affect_by_mass = oval_radius_affect_by_mass
        self.oval_fill_color = oval_fill_color
        self.oval_outline_color = oval_outline_color

        self.ovals = list(map(
            self.create_oval,
            enumerate(bodies)
        ))

    def create_oval(self, enumerate_body_pair: (int, Body)):
        index, body = enumerate_body_pair

        return self.canvas.create_oval(
            round(body.position[0]
                  - (self.oval_radius * (math.cbrt(body.mass) if self.oval_radius_affect_by_mass else 1))),
            round(- body.position[1]
                  - (self.oval_radius * (math.cbrt(body.mass) if self.oval_radius_affect_by_mass else 1))),
            round(body.position[0]
                  + (self.oval_radius * (math.cbrt(body.mass) if self.oval_radius_affect_by_mass else 1))),
            round(- body.position[1]
                  + (self.oval_radius * (math.cbrt(body.mass) if self.oval_radius_affect_by_mass else 1))),
            fill=self.oval_fill_color if self.oval_fill_color is not None else colors[index % len(colors)],
            outline=self.oval_outline_color
        ),

    def render(self):
        for i, body in enumerate(self.bodies):
            self.canvas.moveto(
                self.ovals[i],
                round(body.position[0]
                      - (self.oval_radius * (math.cbrt(body.mass) if self.oval_radius_affect_by_mass else 1))),
                round(- body.position[1]
                      - (self.oval_radius * (math.cbrt(body.mass) if self.oval_radius_affect_by_mass else 1))),
            )
            self.canvas.tag_raise(self.ovals[i])


class MimonRenderer(Renderer):
    def __init__(self, bodies: List[Body], canvas: Canvas):
        super().__init__(bodies, canvas)

        self.mimon_images = [PhotoImage(file="images/" + f) for f in mimon_image_filenames]
        self.mimons = list(map(
            self.create_mimon,
            enumerate(bodies)
        ))

    def create_mimon(self, enumerate_body_pair: (int, Body)):
        index, body = enumerate_body_pair

        return self.canvas.create_image(body.position[0], body.position[1], image=self.mimon_images[index % len(
            self.mimon_images)])

    def render(self):
        for i, body in enumerate(self.bodies):
            self.canvas.moveto(
                self.mimons[i],
                round(body.position[0] - 30),
                round(- body.position[1] - 30),
            )
            self.canvas.tag_raise(self.mimons[i])


class TrajectoryRenderer(Renderer):
    def __init__(self, bodies: List[Body], canvas: Canvas, trajectory_color: str | None = None,
                 trajectory_fade_out_count: int = 4000):
        super().__init__(bodies, canvas)

        self.trajectory_color = trajectory_color
        self.trajectory_fade_out_count = trajectory_fade_out_count

        self.previous_body_positions = list(map(lambda b: deepcopy(b.position), bodies))
        self.lines: List[List[int]] = []

    def render(self):
        lines_created = []

        for index, body in enumerate(self.bodies):
            previous_body_position = self.previous_body_positions[index]
            line_x0 = round(previous_body_position[0])
            line_y0 = round(- previous_body_position[1])
            line_x1 = round(body.position[0])
            line_y1 = round(- body.position[1])

            if line_x0 == line_x1 and line_y0 == line_y1:
                continue

            line = self.canvas.create_line(
                line_x0, line_y0, line_x1, line_y1,
                fill=self.trajectory_color if self.trajectory_color is not None else colors[index % len(colors)]
            )
            lines_created.append(line)

        self.lines.append(lines_created)

        if len(self.lines) > self.trajectory_fade_out_count:
            lines_to_delete_count = len(self.lines) - self.trajectory_fade_out_count
            for line in [l for ls in self.lines[:lines_to_delete_count] for l in ls]:
                self.canvas.delete(line)
            self.lines = self.lines[lines_to_delete_count:]

        self.previous_body_positions = list(map(lambda b: deepcopy(b.position), self.bodies))


class Simulator(ABC):
    def __init__(self, bodies: List[Body]):
        self.bodies = bodies

    @abstractmethod
    def tick(self, step: float):
        pass


class FallSimulator(Simulator):
    def tick(self, step: float = 0.1):
        for body in self.bodies:
            body.velocity += np.array([0, step * 10])
            body.position -= np.array([0, body.velocity[1] * step])


class GravitySimulator(Simulator):
    def __init__(self, bodies: List[Body]):
        super().__init__(bodies)
        self.DISTANCE_MIN = 50

    def tick(self, step: float = 0.1):
        for body1 in self.bodies:
            force = sum(map(
                lambda body2:
                gravitational_constant * body1.mass * body2.mass * (body2.position - body1.position)
                / max(norm(body2.position - body1.position) ** 3, self.DISTANCE_MIN),
                filter(lambda b: b != body1, self.bodies))
            )
            acceleration = force / body1.mass
            body1.velocity = body1.velocity + step * acceleration

        for body in self.bodies:
            body.position = body.position + body.velocity * step
