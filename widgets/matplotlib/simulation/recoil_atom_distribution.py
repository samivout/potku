# coding=utf-8
"""
Created on 1.3.2018
Updated on 4.7.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen"
__version__ = "2.0"

import matplotlib
import modules.masses as masses
import os

from dialogs.simulation.element_simulation_settings import \
    ElementSimulationSettingsDialog
from dialogs.simulation.recoil_element_selection import \
    RecoilElementSelectionDialog
from dialogs.simulation.recoil_info_dialog import RecoilInfoDialog

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication

from matplotlib.widgets import SpanSelector
from modules.element import Element
from modules.point import Point
from modules.recoil_element import RecoilElement

from widgets.matplotlib.base import MatplotlibWidget
from widgets.matplotlib.simulation.element import ElementWidget
from widgets.simulation.controls import SimulationControlsWidget
from widgets.simulation.recoil_element import RecoilElementWidget


class ElementManager:
    """
    A class that manipulates the elements of the simulation.
    A Simulation can have 0...n ElementSimulations.
    Each ElementSimulation has 1 RecoilElement.
    Each RecoilElement has 1 Element, 1 ElementWidget and 2...n Points.
    """

    def __init__(self, parent_tab, parent, icon_manager, simulation):
        """
        Initializes element manager.

        Args:
            parent_tab: SimulationTabWidget object.
            parent: RecoilAtomDistributionWidget object.
            icon_manager: IconManager object.
            simulation: Simulation object.
        """
        self.parent_tab = parent_tab
        self.parent = parent
        self.icon_manager = icon_manager
        self.simulation = simulation
        self.element_simulations = self.simulation.element_simulations

    def get_element_simulation_with_recoil_element(self, recoil_element):
        """
        Get element simulation with recoil element.

        Args:
             recoil_element: A RecoilElement object.

        Return:
            ElementSimulation.
        """
        for element_simulation in self.element_simulations:
            if element_simulation.recoil_elements[0] == recoil_element:
                return element_simulation

    def get_element_simulation_with_radio_button(self, radio_button):
        """
        Get element simulation with radio button.

        Args:
             radio_button: A radio button widget.

        Return:
            ElementSimulation.
        """
        for element_simulation in self.element_simulations:
            for button in self.get_radio_buttons(element_simulation):
                if button == radio_button:
                    return element_simulation

    def get_recoil_element_with_radio_button(self, radio_button,
                                             element_simulation):
        """
        Get recoil element with radio button from given element simulation.

        Args:
            radio_button: A radio button widget.
            element_simulation: An ElementSimulation object.

        Return:
            RecoilElement.
        """
        for recoil_element in element_simulation.recoil_elements:
            if recoil_element.widgets[0].radio_button == radio_button:
                return recoil_element

    def add_new_element_simulation(self, element):
        """
        Create a new ElementSimulation and RecoilElement with default points.

        Args:
             element: Element that tells the element to add.

        Return:
            Created ElementSimulation
        """
        # Default points
        xs = [0.00, 35.00]
        ys = [1.0, 1.0]
        xys = list(zip(xs, ys))
        points = []
        for xy in xys:
            points.append(Point(xy))

        if element.isotope is None:
            element.isotope = int(round(masses.get_standard_isotope(
                element.symbol)))

        element_widget = ElementWidget(self.parent, element,
                                       self.parent_tab, None)
        recoil_element = RecoilElement(element, points)
        recoil_element.widgets.append(element_widget)
        element_simulation = self.simulation.add_element_simulation(
            recoil_element)
        element_widget.element_simulation = element_simulation
        element_widget.add_element_simulation_reference(element_simulation)

        # Add simulation controls widget
        simulation_controls_widget = SimulationControlsWidget(
            element_simulation)
        simulation_controls_widget.element_simulation = element_simulation
        self.parent_tab.ui.contentsLayout.addWidget(simulation_controls_widget)
        element_simulation.recoil_elements[0] \
            .widgets.append(simulation_controls_widget)

        return element_simulation

    def add_element_simulation(self, element_simulation):
        """
        Add an existing ElementSimulation.

        Args:
            element_simulation: ElementSimulation to be added.
        """
        main_element_widget =\
            ElementWidget(self.parent,
                          element_simulation.recoil_elements[0].element,
                          self.parent_tab, element_simulation)
        element_simulation.recoil_elements[0] \
            .widgets.append(main_element_widget)
        main_element_widget.element_simulation = element_simulation

        # Add simulation controls widget
        simulation_controls_widget = SimulationControlsWidget(
            element_simulation)
        simulation_controls_widget.element_simulation = element_simulation
        self.parent_tab.ui.contentsLayout.addWidget(simulation_controls_widget)
        element_simulation.recoil_elements[0] \
            .widgets.append(simulation_controls_widget)

        # Add other recoil element widgets
        i = 1
        while i in range(len(element_simulation.recoil_elements)):
            recoil_element_widget = RecoilElementWidget(
                self.parent,
                element_simulation.recoil_elements[i].element,
                self.parent_tab, main_element_widget, element_simulation)
            element_simulation.recoil_elements[i].widgets.append(
                recoil_element_widget)
            recoil_element_widget.element_simulation = element_simulation

            # Check if there are e.g. Default-1 named recoil elements. If so,
            #  increase element.running_int_recoil
            recoil_name = element_simulation.recoil_elements[i].name
            if recoil_name.startswith("Default-"):
                possible_int = recoil_name.split('-')[1]
                try:
                    integer = int(possible_int)
                    main_element_widget.running_int_recoil = integer + 1
                except ValueError:
                    pass
            i = i + 1

    def remove_element_simulation(self, element_simulation):
        """
        Remove element simulation.

        Args:
            element_simulation: An ElementSimulation object to be removed.
        """
        element_simulation.recoil_elements[0].delete_widgets()
        self.element_simulations.remove(element_simulation)

        # Delete all files that relate to element_simulation
        files_to_be_removed = []
        for file in os.listdir(element_simulation.directory):
            if file.startswith(element_simulation.name_prefix) and \
                    (file.endswith(".mcsimu") or file.endswith(".rec") or
                     file.endswith(".profile")):
                file_path = os.path.join(element_simulation.directory, file)
                files_to_be_removed.append(file_path)

        for file_path in files_to_be_removed:
            os.remove(file_path)

    def get_radio_buttons(self, element_simulation):
        """
        Get all radio buttons based on element simulation.

        Args:
            element_simulation: An ElementSimulation object.

        Return:
            List of buttons that have the same ElementSimulation reference.
        """
        radio_buttons = []
        for recoil_element in element_simulation.recoil_elements:
            radio_buttons.append(recoil_element.widgets[0].radio_button)
        return radio_buttons


class RecoilAtomDistributionWidget(MatplotlibWidget):
    """Matplotlib simulation recoil atom distribution widget.
    Using this widget, the user can edit the recoil atom distribution
    for the simulation.
    """
    selectionsChanged = QtCore.pyqtSignal("PyQt_PyObject")
    saveCuts = QtCore.pyqtSignal("PyQt_PyObject")
    color_scheme = {"Default color": "jet",
                    "Greyscale": "Greys",
                    "Greyscale (inverted)": "gray"}

    tool_modes = {0: "",
                  1: "pan/zoom",  # Matplotlib's drag
                  2: "zoom rect"  # Matplotlib's zoom
                  }

    def __init__(self, parent, simulation, target, tab, icon_manager):
        """Inits recoil atom distribution widget.

        Args:
            parent: A TargetWidget class object.
            icon_manager: An IconManager class object.
        """

        super().__init__(parent)
        self.canvas.manager.set_title("Recoil Atom Distribution")
        self.axes.format_coord = self.format_coord
        self.__icon_manager = icon_manager
        self.tab = tab
        self.simulation = simulation

        self.current_element_simulation = None
        self.current_recoil_element = None
        self.element_manager = ElementManager(self.tab, self,
                                              self.__icon_manager,
                                              self.simulation)
        self.target = target
        self.layer_colors = [(0.9, 0.9, 0.9), (0.85, 0.85, 0.85)]

        self.parent_ui = parent.ui
        # Setting up the element scroll area
        widget = QtWidgets.QWidget()
        self.recoil_vertical_layout = QtWidgets.QVBoxLayout()
        self.recoil_vertical_layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(self.recoil_vertical_layout)

        scroll_vertical_layout = QtWidgets.QVBoxLayout()
        self.parent_ui.recoilScrollAreaContents.setLayout(
            scroll_vertical_layout)

        scroll_vertical_layout.addWidget(widget)
        scroll_vertical_layout.addItem(
            QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum,
                                  QtWidgets.QSizePolicy.Expanding))

        self.parent_ui.addPushButton.clicked.connect(
            self.add_element_with_dialog)
        self.parent_ui.removePushButton.clicked.connect(
            self.remove_current_element)
        # self.parent_ui.settingsPushButton.clicked.connect(
        #     self.open_element_simulation_settings)

        self.radios = QtWidgets.QButtonGroup(self)
        self.radios.buttonToggled[QtWidgets.QAbstractButton, bool].connect(
            self.choose_element)

        self.parent_ui.editPushButton.clicked.connect(
            self.open_recoil_element_info)

        # TODO: Set lock on only when simulation has been run
        self.edit_lock_push_button = self.parent_ui.editLockPushButton
        self.edit_lock_push_button.setEnabled(False)
        self.edit_lock_push_button.clicked.connect(self.unlock_edit)
        self.edit_lock_on = False

        # Locations of points about to be dragged at the time of click
        self.click_locations = []
        # Distances between points about to be dragged
        self.x_dist_left = []  # x dist to leftmost point
        self.x_dist_right = []  # x dist to rightmost point
        self.y_dist_lowest = []  # y dist to lowest point
        # Index of lowest point about to be dragged
        self.lowest_dr_p_i = 0
        # Minimum x distance between points
        self.x_res = 0.01
        # Minimum y coordinate for points
        self.y_min = 0.0001
        # Markers representing points
        self.markers = None
        # Lines connecting markers
        self.lines = None
        # Markers representing selected points
        self.markers_selected = None
        # Points that are being dragged
        self.dragged_points = []
        # Points that have been selected
        self.selected_points = []

        self.annotations = []
        self.trans = matplotlib.transforms.blended_transform_factory(
            self.axes.transData, self.axes.transAxes)

        # Span selection tool (used to select all points within a range
        # on the x axis)
        self.span_selector = SpanSelector(self.axes, self.on_span_select,
                                          'horizontal', useblit=True,
                                          rectprops=dict(alpha=0.5,
                                                         facecolor='red'),
                                          button=3)

        # Connections and setup
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

        self.locale = QLocale.c()
        self.clipboard = QGuiApplication.clipboard()
        self.ratio_str = self.clipboard.text()
        self.clipboard.changed.connect(self.__update_multiply_action)

        # This customizes the toolbar buttons
        self.__fork_toolbar_buttons()

        # Remember x limits to set when the user has returned from Target view.
        self.original_x_limits = None

        self.name_y_axis = "Relative Concentration"
        self.name_x_axis = "Depth [nm]"

        self.on_draw()

        if self.simulation.element_simulations:
            self.__update_figure()

        for button in self.radios.buttons():
            button.setChecked(True)
            break

    def format_coord(self, x, y):
        """
        Format mouse coordinates.

        Args:
            x: X coordinate.
            y: Y coordinate.

        Return:
            Formatted text.
        """
        x_part = "\nx:{0:1.2f},".format(x)
        y_part = "\ny:{0:1.4f}".format(y)
        return x_part + y_part

    def __update_figure(self):
        """
        Update figure.
        """
        select_first_elem_sim = True
        for element_simulation in self.simulation.element_simulations:
            self.add_element(element_simulation.recoil_elements[0].element,
                             element_simulation)
            element_simulation.recoil_elements[0].widgets[0].\
                radio_button.setChecked(select_first_elem_sim)
            select_first_elem_sim = False

    def open_element_simulation_settings(self):
        """
        Open element simulation settings.
        """
        if not self.current_element_simulation:
            return
        ElementSimulationSettingsDialog(self.current_element_simulation)

    def open_recoil_element_info(self):
        """
        Open recoil element info.
        """
        dialog = RecoilInfoDialog(
            self.current_recoil_element)
        if dialog.isOk:
            new_values = {"name": dialog.name,
                          "description": dialog.description,
                          "reference_density": dialog.reference_density}
            try:
                self.current_element_simulation.update_recoil_element(
                    self.current_recoil_element,
                    new_values)
                self.update_recoil_element_info_labels()
            except KeyError:
                error_box = QtWidgets.QMessageBox()
                error_box.setIcon(QtWidgets.QMessageBox.Warning)
                error_box.addButton(QtWidgets.QMessageBox.Ok)
                error_box.setText("All recoil element information could not "
                                  "be saved.")
                error_box.setWindowTitle("Error")
                error_box.exec()

    def save_mcsimu_rec_profile(self, directory):
        """
        Save information to .mcsimu and .profile files.
        """
        for element_simulation in self.element_manager \
                .element_simulations:

            element_simulation.mcsimu_to_file(
                os.path.join(directory, element_simulation.name_prefix + "-" +
                             element_simulation.name +
                             ".mcsimu"))
            for recoil_element in element_simulation.recoil_elements:
                element_simulation.recoil_to_file(directory, recoil_element)
            element_simulation.profile_to_file(
                os.path.join(directory, element_simulation.name_prefix +
                             ".profile"))

    def unlock_edit(self):
        """
        Unlock full edit.
        """
        confirm_box = QtWidgets.QMessageBox()
        confirm_box.setIcon(QtWidgets.QMessageBox.Warning)
        yes_button = confirm_box.addButton(QtWidgets.QMessageBox.Yes)
        confirm_box.addButton(QtWidgets.QMessageBox.Cancel)
        confirm_box.setText("Are you sure you want to unlock full edit for this"
                            " element?\nAll previous results of this element's"
                            " simulation will be deleted!")
        confirm_box.setInformativeText("When full edit is unlocked, you can"
                                       " change the x coordinate of the"
                                       " rightmost point.")
        confirm_box.setWindowTitle("Confirm")

        confirm_box.exec()
        if confirm_box.clickedButton() == yes_button:
            self.current_element_simulation.unlock_edit(
                self.current_recoil_element)
            self.edit_lock_on = False
            self.edit_lock_push_button.setText("Full edit unlocked")
            self.edit_lock_push_button.setEnabled(False)
        self.update_plot()

    def choose_element(self, button, checked):
        """
        Choose element from view.

        Args:
            button: Radio button.
            checked: Whether button is checked or not.
        """
        if checked:
            current_element_simulation = self.element_manager \
                .get_element_simulation_with_radio_button(button)
            self.current_element_simulation = \
                current_element_simulation
            self.current_recoil_element = \
                self.element_manager.get_recoil_element_with_radio_button(
                    button, self.current_element_simulation)
            # Disable element simulation deletion button for other than main
            # recoil element.
            if self.current_recoil_element is not \
                    self.current_element_simulation.recoil_elements[0]:
                self.parent_ui.removePushButton.setEnabled(False)
            else:
                self.parent_ui.removePushButton.setEnabled(True)
            self.parent_ui.elementInfoWidget.show()
            if self.current_element_simulation.get_edit_lock_on(
                    self.current_recoil_element):
                self.edit_lock_on = True
                self.edit_lock_push_button.setText("Unlock full edit")
                self.edit_lock_push_button.setEnabled(True)
            else:
                self.edit_lock_on = False
                self.edit_lock_push_button.setText("Full edit unlocked")
                self.edit_lock_push_button.setEnabled(False)

            self.update_recoil_element_info_labels()
            self.dragged_points.clear()
            self.selected_points.clear()
            self.update_plot()
            # self.axes.relim()
            # self.axes.autoscale()

    def update_recoil_element_info_labels(self):
        """
        Update recoil element info labels.
        """
        self.parent_ui.nameLabel.setText(
            "Name: " + self.current_recoil_element.name)
        self.parent_ui.referenceDensityLabel.setText(
            "Reference density: " + "{0:1.2f}".format(
                self.current_recoil_element.reference_density) +
            "e22 at/cm\xb2"
        )

    def recoil_element_info_on_switch(self):
        """
        Show recoil element info on switch.
        """
        if self.current_element_simulation is None:
            self.parent_ui.elementInfoWidget.hide()
        else:
            self.parent_ui.elementInfoWidget.show()

    def add_element_with_dialog(self):
        """
        Add new element simulation with dialog.
        """
        dialog = RecoilElementSelectionDialog(self)
        if dialog.isOk:
            if dialog.isotope is None:
                isotope = int(round(masses.get_standard_isotope(
                    dialog.element)))
            else:
                isotope = dialog.isotope
            element_simulation = self.add_element(Element(
                dialog.element, isotope))

            if self.current_element_simulation is None:
                self.current_element_simulation = element_simulation
                self.current_recoil_element = element_simulation.\
                    recoil_elements[0]
                element_simulation.recoil_elements[0].widgets[0].radio_button \
                    .setChecked(True)

    def add_element(self, element, element_simulation=None):
        """
        Adds a new ElementSimulation based on the element. If elem_sim is
         not None, only UI widgets need to be added.

         Args:
             element: Element that is added.
             element_simulation: ElementSimulation that needs the UI widgets.
        """
        if element_simulation is None:
            # Create new ElementSimulation
            element_simulation = self.element_manager \
                .add_new_element_simulation(element)
        else:
            element_simulation = element_simulation
            self.element_manager.add_element_simulation(element_simulation)

        # Add recoil element widgets
        for recoil_element in element_simulation.recoil_elements:
            recoil_element_widget = recoil_element.widgets[0]
            self.radios.addButton(recoil_element_widget.radio_button)
            self.recoil_vertical_layout.addWidget(recoil_element_widget)

        return element_simulation

    def remove_element(self, element_simulation):
        """
        Remove element simulation.

        Args:
            element_simulation: An ElementSimulation object.
        """
        self.element_manager.remove_element_simulation(element_simulation)

    def remove_recoil_element(self, recoil_widget):
        """
        Remove recoil element that has the given recoil_widget.

        Args:
             recoil_widget: A RecoilElementWidget.
        """
        recoil_to_delete = None
        element_simulation = None
        for elem_sim in self.element_manager.element_simulations:
            for recoil_element in elem_sim.recoil_elements:
                if recoil_element.widgets[0] is recoil_widget:
                    recoil_to_delete = recoil_element
                    element_simulation = elem_sim
                    break
        if recoil_to_delete and element_simulation:
            # Remove radio button from list
            self.radios.remove(recoil_widget.radio_button)
            # Remove recoil widget from view
            recoil_widget.deleteLater()
            # Remove recoil element from element simulation
            element_simulation.recoil_elements.remove(recoil_to_delete)
            # TODO: Delete rec, recoil and simu files.

    def remove_current_element(self):
        """
        Remove current element simulation.
        """
        if not self.current_element_simulation:
            return
        if self.current_recoil_element is not \
                self.current_element_simulation.recoil_elements[0]:
            return
        reply = QtWidgets.QMessageBox.question(self, "Confirmation",
                                               "If you delete selected "
                                               "element simulation, "
                                               "all possible recoils "
                                               "connected to it will be "
                                               "also deleted.\n\nAre you sure "
                                               "you want to delete selected "
                                               "element simulation?",
                                               QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No |
                                               QtWidgets.QMessageBox.Cancel,
                                               QtWidgets.QMessageBox.Cancel)
        if reply == QtWidgets.QMessageBox.No or reply == \
                QtWidgets.QMessageBox.Cancel:
            return  # If clicked Yes, then continue normally
        element_simulation = self.element_manager\
            .get_element_simulation_with_radio_button(
             self.radios.checkedButton())
        self.remove_element(element_simulation)
        self.current_element_simulation = None
        self.parent_ui.elementInfoWidget.hide()
        self.update_plot()

    def export_elements(self):
        """
        Export elements from target layers into element simulations.
        """
        for layer in self.target.layers:
            for layer_element in layer.elements:
                already_exists = False

                for existing_element_simulation \
                        in self.element_manager.element_simulations:

                    for recoil_element \
                            in existing_element_simulation.recoil_elements:

                        if layer_element.isotope \
                                == recoil_element.element.isotope \
                                and layer_element.symbol \
                                == recoil_element.element.symbol:
                            already_exists = True
                            break
                if not already_exists:
                    self.add_element(layer_element)

    def on_draw(self):
        """Draw method for matplotlib.
        """
        self.axes.clear()  # Clear old stuff

        self.axes.set_ylabel(self.name_y_axis)
        self.axes.set_xlabel(self.name_x_axis)

        if self.current_element_simulation:
            self.lines, = self.axes.plot(
                self.current_element_simulation.get_xs(
                    self.current_recoil_element),
                self.current_element_simulation.get_ys(
                    self.current_recoil_element),
                color="blue")

            self.markers, = self.axes.plot(
                self.current_element_simulation.get_xs(
                    self.current_recoil_element),
                self.current_element_simulation.get_ys(
                    self.current_recoil_element),
                color="blue", marker="o",
                markersize=10, linestyle="None")

            self.markers_selected, = self.axes.plot(0, 0, marker="o",
                                                    markersize=10,
                                                    linestyle="None",
                                                    color='yellow',
                                                    visible=False)
        else:
            self.lines, = self.axes.plot(0, 0, color="blue", visible=False)
            self.markers, = self.axes.plot(0, 0, color="blue", marker="o",
                                           markersize=10, linestyle="None",
                                           visible=False)
            self.markers_selected, = self.axes.plot(0, 0, marker="o",
                                                    markersize=10,
                                                    linestyle="None",
                                                    color='yellow',
                                                    visible=False)

        self.axes.set_xlim(-1, 40)
        self.axes.set_ylim(-0.1, 2)

        # Remove axis ticks and draw
        self.remove_axes_ticks()
        self.canvas.draw()

    def __toggle_tool_drag(self):
        """
        Toggle drag tool.
        """
        if self.__button_drag.isChecked():
            self.mpl_toolbar.mode_tool = 1
        else:
            self.mpl_toolbar.mode_tool = 0
        self.canvas.draw_idle()

    def __toggle_tool_zoom(self):
        """
        Toggle zoom tool.
        """
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.mode_tool = 2
        else:
            self.mpl_toolbar.mode_tool = 0
        self.canvas.draw_idle()

    def __toggle_drag_zoom(self):
        """
        Toggle drag zoom.
        """
        self.__tool_label.setText("")
        if self.__button_drag.isChecked():
            self.mpl_toolbar.pan()
        if self.__button_zoom.isChecked():
            self.mpl_toolbar.zoom()
        self.__button_drag.setChecked(False)
        self.__button_zoom.setChecked(False)

    def __fork_toolbar_buttons(self):
        """
        Fork navigation tool bar button into custom ones.
        """
        super().fork_toolbar_buttons()
        self.mpl_toolbar.mode_tool = 0
        self.__tool_label = self.mpl_toolbar.children()[24]
        self.__button_drag = self.mpl_toolbar.children()[12]
        self.__button_zoom = self.mpl_toolbar.children()[14]
        self.__button_drag.clicked.connect(self.__toggle_tool_drag)
        self.__button_zoom.clicked.connect(self.__toggle_tool_zoom)

        # Make own buttons
        self.mpl_toolbar.addSeparator()

        # Point x coordinate spinbox
        self.x_coordinate_box = QtWidgets.QDoubleSpinBox(self)
        # Set decimal pointer to .
        self.x_coordinate_box.setLocale(self.locale)
        self.x_coordinate_box.setToolTip("X coordinate of selected point")
        self.x_coordinate_box.setSingleStep(0.1)
        self.x_coordinate_box.setDecimals(2)
        self.x_coordinate_box.setMinimum(0)
        self.x_coordinate_box.setMaximum(1000000000000)
        self.x_coordinate_box.setMaximumWidth(62)
        self.x_coordinate_box.setKeyboardTracking(False)
        self.x_coordinate_box.valueChanged.connect(self.set_selected_point_x)
        self.x_coordinate_box.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.actionXMultiply = QtWidgets.QAction(self)
        self.actionXMultiply.setText("Multiply with value in clipboard\n(" +
                                     self.ratio_str + ")")
        self.actionXMultiply.triggered.connect(
            lambda: self.__multiply_coordinate(self.x_coordinate_box))
        self.x_coordinate_box.addAction(self.actionXMultiply)

        self.actionXUndo = QtWidgets.QAction(self)
        self.actionXUndo.setText("Undo multipy")
        self.actionXUndo.triggered.connect(
            lambda: self.undo(self.x_coordinate_box))
        self.actionXUndo.setEnabled(False)
        self.x_coordinate_box.addAction(self.actionXUndo)

        self.mpl_toolbar.addWidget(self.x_coordinate_box)
        self.x_coordinate_box.setEnabled(False)

        # Point y coordinate spinbox
        self.y_coordinate_box = QtWidgets.QDoubleSpinBox(self)
        # Set decimal pointer to .
        self.y_coordinate_box.setLocale(self.locale)
        self.y_coordinate_box.setToolTip("Y coordinate of selected point")
        self.y_coordinate_box.setSingleStep(0.1)
        self.y_coordinate_box.setDecimals(4)
        self.y_coordinate_box.setMaximum(1000000000000)
        self.y_coordinate_box.setMaximumWidth(62)
        self.y_coordinate_box.setMinimum(self.y_min)
        self.y_coordinate_box.setKeyboardTracking(False)
        self.y_coordinate_box.valueChanged.connect(self.set_selected_point_y)
        self.y_coordinate_box.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.actionYMultiply = QtWidgets.QAction(self)
        self.actionYMultiply.setText("Multiply with value in clipboard\n(" +
                                     self.ratio_str + ")")
        self.actionYMultiply.triggered.connect(
            lambda: self.__multiply_coordinate(self.y_coordinate_box))
        self.y_coordinate_box.addAction(self.actionYMultiply)

        self.actionYUndo = QtWidgets.QAction(self)
        self.actionYUndo.setText("Undo multiply")
        self.actionYUndo.triggered.connect(
            lambda: self.undo(self.y_coordinate_box))
        self.actionYUndo.setEnabled(False)
        self.y_coordinate_box.addAction((self.actionYUndo))

        self.mpl_toolbar.addWidget(self.y_coordinate_box)
        self.y_coordinate_box.setEnabled(False)

        # Point removal
        point_remove_action = QtWidgets.QAction("Remove point", self)
        point_remove_action.triggered.connect(self.remove_points)
        point_remove_action.setToolTip("Remove selected points")
        # TODO: Temporary icon
        self.__icon_manager.set_icon(point_remove_action, "del.png")
        self.mpl_toolbar.addAction(point_remove_action)

    def undo(self, spinbox):
        """
        Undo change to spinbox value.
        """
        if spinbox == self.x_coordinate_box:
            old_value = self.selected_points[0].previous_x.pop()
            if not self.selected_points[0].previous_x:
                self.actionXUndo.setEnabled(False)
        else:
            old_value = self.selected_points[0].previous_y.pop()
            if not self.selected_points[0].previous_y:
                self.actionYUndo.setEnabled(False)
        spinbox.setValue(old_value)

    def __update_multiply_action(self):
        self.ratio_str = self.clipboard.text()
        self.actionXMultiply.setText("Multiply with value in clipboard\n(" +
                                     self.ratio_str + ")")
        self.actionYMultiply.setText("Multiply with value in clipboard\n(" +
                                     self.ratio_str + ")")

    def __multiply_coordinate(self, spinbox):
        """
        Multiply the spinbox's value with the value in clipboard.

        Args:
            spinbox: Spinbox whose value is multiplied.
        """
        try:
            ratio = float(self.ratio_str)
            coord = spinbox.value()
            new_coord = round(ratio * coord, 3)
            if spinbox == self.x_coordinate_box:
                self.selected_points[0].previous_x.append(
                    self.selected_points[0].get_x())
                self.actionXUndo.setEnabled(True)
            else:
                self.selected_points[0].previous_y.append(
                    self.selected_points[0].get_y())
                self.actionYUndo.setEnabled(True)
            spinbox.setValue(new_coord)
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Error",
                                           "Value '" + self.ratio_str +
                                           "' is not suitable for "
                                           "multiplying.\n\nPlease copy a "
                                           "suitable value to clipboard.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)

    def set_selected_point_x(self):
        """Sets the selected point's x coordinate
        to the value of the x spinbox.
        """
        x = self.x_coordinate_box.value()
        leftmost_sel_point = self.selected_points[0]
        left_neighbor = self.current_element_simulation.get_left_neighbor(
            self.current_recoil_element,
            leftmost_sel_point)
        right_neighbor = self.current_element_simulation.get_right_neighbor(
            self.current_recoil_element,
            leftmost_sel_point)

        # Can't move past neighbors. If tried, sets x coordinate to
        # distance x_res from neighbor's x coordinate.
        if left_neighbor is None:
            if x < right_neighbor.get_x():
                leftmost_sel_point.set_x(x)
            else:
                leftmost_sel_point.set_x(right_neighbor.get_x() - self.x_res)
        elif right_neighbor is None:
            if x > left_neighbor.get_x():
                leftmost_sel_point.set_x(x)
            else:
                leftmost_sel_point.set_x(left_neighbor.get_x() + self.x_res)
        elif left_neighbor.get_x() < x < right_neighbor.get_x():
            leftmost_sel_point.set_x(x)
        elif left_neighbor.get_x() >= x:
            leftmost_sel_point.set_x(left_neighbor.get_x() + self.x_res)
        elif right_neighbor.get_x() <= x:
            leftmost_sel_point.set_x(right_neighbor.get_x() - self.x_res)
        self.update_plot()

    def set_selected_point_y(self):
        """Sets the selected point's y coordinate
        to the value of the y spinbox.
        """
        y = self.y_coordinate_box.value()
        leftmost_sel_point = self.selected_points[0]
        leftmost_sel_point.set_y(y)
        self.update_plot()

    def on_click(self, event):
        """ On click event above graph.

        Args:
            event: A MPL MouseEvent
        """
        if not self.current_element_simulation:
            return
        # Don't do anything if drag tool or zoom tool is active.
        if self.__button_drag.isChecked() or self.__button_zoom.isChecked():
            return
        # Only inside the actual graph axes, else do nothing.
        if event.inaxes != self.axes:
            return
        if event.button == 1:  # Left click
            marker_contains, marker_info = self.markers.contains(event)
            if marker_contains:  # If clicked a point
                i = marker_info['ind'][0]  # The clicked point's index
                clicked_point = \
                    self.current_element_simulation.get_point_by_i(
                        self.current_recoil_element, i)
                if clicked_point not in self.selected_points:
                    self.selected_points = [clicked_point]
                self.dragged_points.extend(self.selected_points)

                self.set_on_click_attributes(event)

                self.update_plot()
            else:
                # Ctrl-click to add a point
                modifiers = QtGui.QGuiApplication.queryKeyboardModifiers()
                if modifiers == QtCore.Qt.ControlModifier:
                    self.selected_points.clear()
                    self.update_plot()
                    line_contains, line_info = self.lines.contains(event)
                    if line_contains:  # If clicked a line
                        x = event.xdata
                        y = event.ydata
                        new_point = self.add_point((x, y))
                        if new_point:
                            self.selected_points = [new_point]
                            self.dragged_points = [new_point]
                            self.set_on_click_attributes(event)
                            self.update_plot()

    def set_on_click_attributes(self, event):
        """Sets the attributes needed for dragging points."""
        locations = []
        for point in self.dragged_points:
            x0, y0 = point.get_coordinates()
            locations.append((x0, y0, event.xdata, event.ydata))
        self.click_locations = locations

        self.x_dist_left = [self.dragged_points[i].get_x()
                            - self.dragged_points[0].get_x()
                            for i in range(1, len(self.dragged_points))]
        self.x_dist_right = [self.dragged_points[-1].get_x()
                             - self.dragged_points[i].get_x()
                             for i in range(0, len(self.dragged_points) - 1)]
        self.lowest_dr_p_i = 0
        for i in range(1, len(self.dragged_points)):
            if self.dragged_points[i].get_y() \
                    < self.dragged_points[self.lowest_dr_p_i].get_y():
                self.lowest_dr_p_i = i
        self.y_dist_lowest = [self.dragged_points[i].get_y()
                              - self.dragged_points[self.lowest_dr_p_i].get_y()
                              for i in range(len(self.dragged_points))]

    def add_point(self, coords):
        """Adds a point if there is space for it.
        Returns the point if a point was added, None if not.
        """
        if not self.current_element_simulation:
            return
        new_point = Point(coords)
        self.current_element_simulation.add_point(
            self.current_recoil_element, new_point)
        left_neighbor_x = self.current_element_simulation.get_left_neighbor(
            self.current_recoil_element, new_point).get_x()
        right_neighbor_x = self.current_element_simulation.get_right_neighbor(
            self.current_recoil_element, new_point).get_x()

        error = False

        # If too close to left
        if new_point.get_x() - left_neighbor_x < self.x_res:
            # Need space to insert the new point
            if right_neighbor_x - new_point.get_x() < 2 * self.x_res:
                error = True
            else:
                # Insert the new point as close to its left neighbor as possible
                new_point.set_x(left_neighbor_x + self.x_res)
        elif right_neighbor_x - new_point.get_x() < self.x_res:
            if new_point.get_x() - left_neighbor_x < 2 * self.x_res:
                error = True
            else:
                new_point.set_x(right_neighbor_x - self.x_res)

        if error:
            self.current_element_simulation.remove_point(
                self.current_recoil_element, new_point)
            # TODO: Add an error message text label
            QtWidgets.QMessageBox.critical(self, "Error",
                                           "Can't add a point here.\nThere is "
                                           "no space for it.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
            return None
        else:
            return new_point

    def update_plot(self):
        """ Updates marker and line data and redraws the plot. """
        if not self.current_element_simulation:
            self.markers.set_visible(False)
            self.lines.set_visible(False)
            self.markers_selected.set_visible(False)
            self.fig.canvas.draw_idle()
            return

        self.markers.set_data(self.current_element_simulation.get_xs(
            self.current_recoil_element),
            self.current_element_simulation.get_ys(
                self.current_recoil_element))
        self.lines.set_data(self.current_element_simulation.get_xs(
            self.current_recoil_element),
            self.current_element_simulation.get_ys(
                self.current_recoil_element))

        self.markers.set_visible(True)
        self.lines.set_visible(True)

        if self.selected_points:  # If there are selected points
            self.markers_selected.set_visible(True)
            selected_xs = []
            selected_ys = []
            for point in self.selected_points:
                selected_xs.append(point.get_x())
                selected_ys.append(point.get_y())
            self.markers_selected.set_data(selected_xs, selected_ys)
            if self.selected_points[0] == \
                    self.current_recoil_element.get_points()[-1] \
                    and self.edit_lock_on:
                self.x_coordinate_box.setEnabled(False)
            else:
                self.x_coordinate_box.setEnabled(True)
            self.x_coordinate_box.setValue(self.selected_points[0].get_x())
            self.y_coordinate_box.setEnabled(True)
            self.y_coordinate_box.setValue(self.selected_points[0].get_y())
            # self.text.set_text('selected: %d %d' %
            # (self.selected_points[0].get_coordinates()[0],
            # self.selected_points[0].get_coordinates()[1]))
        else:
            self.markers_selected.set_data(
                self.current_element_simulation.get_xs(
                    self.current_recoil_element),
                self.current_element_simulation.get_ys(
                    self.current_recoil_element))
            self.markers_selected.set_visible(False)
            self.x_coordinate_box.setEnabled(False)
            self.y_coordinate_box.setEnabled(False)

        self.fig.canvas.draw_idle()

    def update_layer_borders(self):
        """
        Update layer borders.
        """
        for annotation in self.annotations:
            annotation.set_visible(False)
        self.annotations = []
        last_layer_thickness = 0

        y = 0.95
        next_layer_position = 0
        for idx, layer in enumerate(self.target.layers):
            self.axes.axvspan(
                next_layer_position, next_layer_position + layer.thickness,
                facecolor=self.layer_colors[idx % 2]
            )

            # Put annotation in the middle of the rectangular patch.
            annotation = self.axes.text(layer.start_depth, y,
                                        layer.name,
                                        transform=self.trans,
                                        fontsize=10,
                                        ha="left")
            y = y - 0.05
            if y <= 0.1:
                y = 0.95
            self.annotations.append(annotation)
            last_layer_thickness = layer.thickness

            # Move the position where the next layer starts.
            next_layer_position += layer.thickness

        if self.original_x_limits:
            start = self.original_x_limits[0]
            end = self.original_x_limits[1]
        else:
            end = next_layer_position - last_layer_thickness * 0.7
            start = 0 - end * 0.05

        self.axes.set_xlim(start, end)
        self.fig.canvas.draw_idle()

    def on_motion(self, event):
        """Callback method for mouse motion event. Moves points that are being
        dragged.

        Args:
            event: A MPL MouseEvent
        """
        if not self.current_element_simulation:
            return
        # Don't do anything if drag tool or zoom tool is active.
        if self.__button_drag.isChecked() or self.__button_zoom.isChecked():
            return
        # Only inside the actual graph axes, else do nothing.
        if event.inaxes != self.axes:
            return
        # Only if there are points being dragged.
        if not self.dragged_points:
            return
        if not self.click_locations:
            return

        dr_ps = self.dragged_points

        new_coords = self.get_new_checked_coordinates(event)

        for i in range(0, len(dr_ps)):
            if dr_ps[i] == self.current_recoil_element.get_points()[-1] \
                    and self.edit_lock_on:
                dr_ps[i].set_y(new_coords[i][1])
            else:
                dr_ps[i].set_coordinates(new_coords[i])

        self.update_plot()

    def get_new_checked_coordinates(self, event):
        """Returns checked new coordinates for dragged points.
        They have been checked for neighbor or axis limit collisions.
        """
        dr_ps = self.dragged_points

        leftmost_dr_p = dr_ps[0]
        rightmost_dr_p = dr_ps[-1]
        left_neighbor = self.current_element_simulation.get_left_neighbor(
            self.current_recoil_element, leftmost_dr_p)
        right_neighbor = self.current_element_simulation.get_right_neighbor(
            self.current_recoil_element, rightmost_dr_p)

        new_coords = self.get_new_unchecked_coordinates(event)

        if left_neighbor is None and right_neighbor is None:
            pass  # No neighbors to limit movement
        # Check for neighbor collisions:
        elif left_neighbor is None and right_neighbor is not None:
            if new_coords[-1][0] >= right_neighbor.get_x() - self.x_res:
                new_coords[-1][0] = right_neighbor.get_x() - self.x_res
                for i in range(0, len(dr_ps) - 1):
                    new_coords[i][0] = right_neighbor.get_x() \
                                       - self.x_res - self.x_dist_right[i]
        elif right_neighbor is None and left_neighbor is not None:
            if new_coords[0][0] <= left_neighbor.get_x() + self.x_res:
                new_coords[0][0] = left_neighbor.get_x() + self.x_res
                for i in range(1, len(dr_ps)):
                    new_coords[i][0] = left_neighbor.get_x() + self.x_res \
                                       + self.x_dist_left[i - 1]
        elif left_neighbor.get_x() + self.x_res >= new_coords[0][0]:
            new_coords[0][0] = left_neighbor.get_x() + self.x_res
            for i in range(1, len(dr_ps)):
                new_coords[i][0] = left_neighbor.get_x() + self.x_res \
                                   + self.x_dist_left[i - 1]
        elif right_neighbor.get_x() - self.x_res <= new_coords[-1][0]:
            new_coords[-1][0] = right_neighbor.get_x() - self.x_res
            for i in range(0, len(dr_ps) - 1):
                new_coords[i][0] = right_neighbor.get_x() - self.x_res \
                                   - self.x_dist_right[i]

        # Check for axis limit collisions:
        if new_coords[0][0] < 0:
            new_coords[0][0] = 0
            for i in range(1, len(dr_ps)):
                new_coords[i][0] = self.x_dist_left[i - 1]

        if new_coords[self.lowest_dr_p_i][1] < self.y_min:
            new_coords[self.lowest_dr_p_i][1] = self.y_min
            for i in range(0, len(dr_ps)):
                new_coords[i][1] = self.y_min + self.y_dist_lowest[i]

        return new_coords

    def get_new_unchecked_coordinates(self, event):
        """Returns new coordinates for dragged points.
        These coordinates come from mouse movement and they haven't been checked
        for neighbor or axis limit collisions.
        """
        new_unchecked_coords = []
        for i, point in enumerate(self.dragged_points):
            x0, y0, xclick, yclick = self.click_locations[i]
            dx = event.xdata - xclick
            dy = event.ydata - yclick
            new_x = x0 + dx
            new_y = y0 + dy
            new_unchecked_coords.append([new_x, new_y])
        return new_unchecked_coords

    def update_location(self, event):
        """Updates the location of points that are being dragged."""
        for point in self.dragged_points:
            point.set_coordinates((event.xdata, event.ydata))
        self.update_plot()

    def remove_points(self):
        """Removes all selected points, but not if there would be
        less than two points left.
        """
        if not self.current_element_simulation:
            return
        if len(self.current_recoil_element.get_points()) - \
                len(self.selected_points) < 2:
            QtWidgets.QMessageBox.critical(self, "Error",
                                           "There must always be at least two"
                                           " points.",
                                           QtWidgets.QMessageBox.Ok,
                                           QtWidgets.QMessageBox.Ok)
        else:
            for sel_point in self.selected_points:
                self.current_element_simulation.remove_point(
                    self.current_recoil_element, sel_point)
            self.selected_points.clear()
            self.update_plot()

    def on_release(self, event):
        """Callback method for mouse release event. Stops dragging.

        Args:
            event: A MPL MouseEvent
        """
        if not self.current_element_simulation:
            return
        # Don't do anything if drag tool or zoom tool is active.
        if self.__button_drag.isChecked() or self.__button_zoom.isChecked():
            return
        if event.button == 1:
            self.dragged_points.clear()
            self.update_plot()

    def on_span_select(self, xmin, xmax):
        """
        Select multiple points.

        Args:
            xmin: Area start.
            xmax: Area end.
        """
        if not self.current_element_simulation:
            return
        sel_points = []
        for point in self.current_recoil_element.get_points():
            if xmin <= point.get_x() <= xmax:
                sel_points.append(point)
        self.selected_points = sel_points
        self.update_plot()
