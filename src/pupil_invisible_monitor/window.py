import logging
import typing as T

import glfw.GLFW as glfw
import numpy as np
from pyglui import cygl, ui

from . import gl_utils
from .event_loop import WindowEventLoop
from .observable import Observable

logger = logging.getLogger(__name__)


def normalize(pos, size, flip_y=False):
    """
    normalize return as float
    """
    width, height = size
    x = pos[0]
    y = pos[1]
    x /= float(width)
    y /= float(height)
    if flip_y:
        return x, 1 - y
    return x, y


def denormalize(pos, size, flip_y=False):
    """
    denormalize
    """
    width, height = size
    x = pos[0]
    y = pos[1]
    x *= width
    if flip_y:
        y = 1 - y
    y *= height
    return x, y


class Window(Observable):
    scroll_factor = 10.0

    def __init__(self, texture, frame_rate: float, callables: T.List[T.Callable] = ...):
        if callables is ...:
            callables = []

        self.texture = texture

        callables.insert(0, self.draw_texture)
        self._window = None
        self.event_loop = WindowEventLoop(self, frame_rate, callables)

    def draw_texture(self):
        if self.is_minimized():
            return
        viewport_length = min(self.window_size)
        viewport_x_offset = (self.window_size[0] - viewport_length) // 2
        viewport_y_offset = (self.window_size[1] - viewport_length) // 2

        gl_utils.glViewport(
            viewport_x_offset, viewport_y_offset, viewport_length, viewport_length
        )
        gl_utils.make_coord_system_norm_based()
        self.texture.draw()
        gl_utils.make_coord_system_pixel_based(self.texture.shape)

    def is_minimized(self):
        return (self.window_size is not None) and (0 in self.window_size)

    def update_gui(self):
        user_input = self.gui.update()
        self.process_unconsumed_user_input(user_input)

    def update(self, timeout=0.0):
        glfw.glfwWaitEventsTimeout(timeout)
        self.update_gui()
        gl_utils.glFlush()
        glfw.glfwSwapBuffers(self._window)

    @property
    def should_draw(self):
        return self._window and not glfw.glfwWindowShouldClose(self._window)

    def open(self, size=(800, 800), pos=(50, 50), gui_scale=1.0, ui_config=None):
        if self._window:
            return

        glfw.glfwInit()
        # Window name needs to be equal to `StartupWMClass` field in Linux .desktop file
        # else the icon will not show correctly on Linux!
        self._window = glfw.glfwCreateWindow(
            *size, "Pupil Invisible Monitor", monitor=None, share=None
        )
        glfw.glfwSetWindowSizeLimits(
            self._window, 200, 200, glfw.GLFW_DONT_CARE, glfw.GLFW_DONT_CARE
        )
        glfw.glfwSetWindowAspectRatio(self._window, 1, 1)
        glfw.glfwSetWindowPos(self._window, *pos)
        glfw.glfwMakeContextCurrent(self._window)

        cygl.utils.init()

        self.gui = ui.UI()
        self.gui_user_scale = gui_scale

        # Adding an intermediate container fixes a pylgui display bug
        cont = ui.Container((0, 0), (0, 0), (0, 0))
        self.quickbar = ui.Horizontally_Stretching_Menu(
            "Quick Bar", (0.0, -120.0), (0.0, 0.0)
        )
        cont.append(self.quickbar)
        self.gui.append(cont)

        # Register callbacks main_window
        glfw.glfwSetFramebufferSizeCallback(self._window, self.on_resize)
        glfw.glfwSetKeyCallback(self._window, self.on_window_key)
        glfw.glfwSetCharCallback(self._window, self.on_window_char)
        glfw.glfwSetMouseButtonCallback(self._window, self.on_window_mouse_button)
        glfw.glfwSetCursorPosCallback(self._window, self.on_pos)
        glfw.glfwSetScrollCallback(self._window, self.on_scroll)
        self.gui.configuration = ui_config or {}
        gl_utils.basic_gl_setup()

        self.on_resize(self._window, *glfw.glfwGetFramebufferSize(self._window))

    def close(self):
        if not self._window:
            return

        glfw.glfwRestoreWindow(self._window)

        del self.gui[:]
        self.gui.terminate()
        glfw.glfwDestroyWindow(self._window)
        glfw.glfwTerminate()

        del self.gui
        self._window = None

    def run_event_loop(self):
        self.event_loop.run()

        # Callback functions

    def on_resize(self, window, w, h):
        self.window_size = w, h

        gl_utils.glClear(gl_utils.GL_COLOR_BUFFER_BIT)
        gl_utils.glClearColor(0, 0, 0, 1)
        if self.is_minimized():
            return
        self.hdpi_factor = glfw.glfwGetWindowContentScale(window)[0]
        self.gui.scale = self.gui_user_scale * self.hdpi_factor
        # gl_utils.adjust_gl_view(w, h)
        self.draw_texture()
        short_side_len = min(w, h)
        self.gui.update_window(short_side_len, short_side_len)
        self.gui.collect_menus()
        self.update_gui()
        gl_utils.glFlush()
        glfw.glfwSwapBuffers(self._window)

    def on_window_key(self, window, key, scancode, action, mods):
        self.gui.update_key(key, scancode, action, mods)

    def on_window_char(self, window, char):
        self.gui.update_char(char)

    def on_window_mouse_button(self, window, button, action, mods):
        self.gui.update_button(button, action, mods)

    def on_pos(self, window, x, y):
        x, y = x * self.hdpi_factor, y * self.hdpi_factor
        self.gui.update_mouse(x, y)

    def on_scroll(self, window, x, y):
        self.gui.update_scroll(x, y * self.scroll_factor)

    def process_unconsumed_user_input(self, user_input):
        if self.is_minimized():
            return
        x, y = glfw.glfwGetCursorPos(self._window)
        pos = x * self.hdpi_factor, y * self.hdpi_factor
        pos = normalize(pos, self.window_size)
        # Position in img pixels
        pos = denormalize(pos, self.texture.shape[:2])
        for button, action, mods in user_input.buttons:
            self.on_click(pos, button, action)

    def on_click(self, pos, button, action):
        pass
