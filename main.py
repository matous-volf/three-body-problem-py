import threading
import time

from body_problem import *


def bodies_solar_system():
    bodies = [
        Body(1e17, [0, 0], [0, 0]),
        Body(1e15, [300, 0], [0, 577.5]),
        Body(1e13, [320, 0], [0, 577.5 + 258.2]),
    ]
    bodies[1].velocity[1] = math.sqrt(
        gravitational_constant * bodies[0].mass / abs(bodies[0].position[0] - bodies[1].position[0])
    )
    bodies[2].velocity[1] = bodies[1].velocity[1] + math.sqrt(
        gravitational_constant * bodies[1].mass / abs(bodies[1].position[0] - bodies[2].position[0])
    )
    bodies[0].velocity[1] = -1.5
    return bodies, 1e-4


def bodies_simple():
    return ([
                Body(1e16, [0, 0], [0, 0]),
                Body(1e16, [100, -100], [0, 0]),
                Body(1e16, [-200, -100], [0, 0]),
            ], 1 * 10 ** -4.3)


def bodies_flower():
    return ([
                Body(1e16, [1000, -300], [-100, 0]),
                Body(1e16, [0, -200], [-100, 0]),
                Body(1 * 10 ** 16.5, [0, 0], [0, 0]),
                Body(1e16, [-2000, 450], [50, 0]),
                Body(1e16, [-200, 0], [0, 100]),
                Body(1e16, [200, 0], [0, -100]),
                Body(1e16, [0, 200], [100, 0]),
            ], 1 * 10 ** -4.3)


class App(Tk):
    def __init__(self):
        Tk.__init__(self)

        # self.resizable(False, False)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.config()
        # self.attributes("-fullscreen", True)
        self.title("Body problem")

        self.canvas = Canvas(self, background="#2b2d30", highlightthickness=0, width=1000, height=500)
        self.canvas.grid(column=0, row=0, sticky="nsew")
        self.bind("<Configure>", self.on_resize)

        self.simulation_tick_step = 0.001
        self.render_simulation_ratio = 10
        self.simulation_reality_ratio = 1

        self.settings_frame = Frame(self)
        self.settings_frame.grid(column=0, row=1, sticky="ew")

        self.is_paused = False
        self.pause_button = Button(self.settings_frame, text="pause", width=10, command=self.toggle_pause)
        self.pause_button.pack(side="right", fill="y")

        self.simulation_tick_step_slider = Scale(self.settings_frame, from_=0.001, to=0.1, resolution=0.001,
                                                 orient=HORIZONTAL, label="simulation tick step",
                                                 command=self.update_simulation_tick_step)
        self.simulation_tick_step_slider.pack(side="left", fill="x", expand=True)
        self.simulation_tick_step_slider.set(self.simulation_tick_step)

        self.render_simulation_ratio_slider = Scale(self.settings_frame, from_=1, to=100, resolution=1,
                                                    orient=HORIZONTAL,
                                                    label="render to simulation ratio",
                                                    command=self.update_render_simulation_ratio)
        self.render_simulation_ratio_slider.pack(side="left", fill="x", expand=True)
        self.render_simulation_ratio_slider.set(self.render_simulation_ratio)

        self.simulation_reality_ratio_slider = Scale(self.settings_frame, from_=0.01, to=10, resolution=0.01,
                                                     orient=HORIZONTAL, label="simulation to reality ratio",
                                                     command=self.update_simulation_reality_ratio)
        self.simulation_reality_ratio_slider.pack(side="left", fill="x", expand=True)
        self.simulation_reality_ratio_slider.set(self.simulation_reality_ratio)

        self.trajectory_fade_out_length_slider = Scale(self.settings_frame, from_=0, to=100000, resolution=1,
                                                       orient=HORIZONTAL, label="trajectory length",
                                                       command=self.update_trajectory_fade_out_length)
        self.trajectory_fade_out_length_slider.pack(side="left", fill="x", expand=True)
        self.trajectory_fade_out_length_slider.set(4000)

        bodies, oval_radius = bodies_flower()

        self.simulator = GravitySimulator(bodies)
        self.renderers_simulation_dependent = [
            TrajectoryRenderer(bodies, self.canvas),
        ]
        self.renderers_simulation_independent = [
            OvalRenderer(bodies, self.canvas, oval_radius=oval_radius, oval_radius_affect_by_mass=True),
        ]

        self.start_tick_thread()

    def update_simulation_tick_step(self, val):
        self.simulation_tick_step = float(val)

    def update_render_simulation_ratio(self, val):
        self.render_simulation_ratio = int(val)

    def update_simulation_reality_ratio(self, val):
        self.simulation_reality_ratio = float(val)

    def update_trajectory_fade_out_length(self, val):
        for renderer in self.renderers_simulation_dependent:
            if isinstance(renderer, TrajectoryRenderer):
                renderer.trajectory_fade_out_count = int(val)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_button.config(text="resume" if self.is_paused else "pause")

    def start_tick_thread(self):
        tick_thread = threading.Thread(target=self.repeat_tick)
        tick_thread.daemon = True
        tick_thread.start()

    def repeat_tick(self):
        while True:
            if self.is_paused:
                time.sleep(0.1)
                continue

            self.tick()

    def tick(self):
        time_start_nanoseconds = time.time_ns()

        for renderer in self.renderers_simulation_independent:
            renderer.render()

        for _ in range(self.render_simulation_ratio):
            for renderer in self.renderers_simulation_dependent:
                renderer.render()

        for _ in range(self.render_simulation_ratio):
            self.simulator.tick(self.simulation_tick_step)

        time_elapsed_nanoseconds = (time.time_ns() - time_start_nanoseconds)

        time_waited = 0
        while True:
            time_to_wait_remaining = (
                    self.simulation_tick_step
                    * self.render_simulation_ratio
                    / self.simulation_reality_ratio
                    - time_elapsed_nanoseconds / 1e9
                    - time_waited
            )

            if time_to_wait_remaining <= 0:
                break

            time.sleep(min(time_to_wait_remaining, 1))
            time_waited += 1

    def on_resize(self, _):
        # keep the canvas origin ([0; 0]) at the center
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        self.canvas.configure(scrollregion=(-width / 2, -height / 2, width / 2, height / 2))
        self.canvas.xview_moveto(0.5)
        self.canvas.yview_moveto(0.5)


if __name__ == "__main__":
    app = App()
    app.mainloop()
