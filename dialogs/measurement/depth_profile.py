# coding=utf-8
"""
Created on 5.4.2013
Updated on 4.12.2018

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import logging

import dialogs.dialog_functions as df
import widgets.gui_utils as gutils
import widgets.binding as bnd
import modules.depth_files as depth_files
import modules.cut_file as cut_file

from pathlib import Path
from typing import List
from typing import Optional

from widgets.gui_utils import StatusBarHandler
from widgets.base_tab import BaseTab
from modules.element import Element
from modules.measurement import Measurement
from modules.global_settings import GlobalSettings
from modules.observing import ProgressReporter

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale

from widgets.matplotlib.measurement.depth_profile import \
    MatplotlibDepthProfileWidget


class DepthProfileDialog(QtWidgets.QDialog):
    """
    Dialog for making a depth profile.
    """
    # TODO replace these global variables with PropertySavingWidget
    checked_cuts = {}
    x_unit = "1e15 at./cm²"     # TODO make this an enum
    line_zero = False
    line_scale = False
    systerr = 0.0

    status_msg = bnd.bind("label_status")
    used_cuts = bnd.bind("treeWidget")
    
    def __init__(self, parent: BaseTab, measurement: Measurement,
                 global_settings: GlobalSettings, statusbar:
                 Optional[QtWidgets.QStatusBar] = None):
        """Inits depth profile dialog.
        
        Args:
            parent: a MeasurementTabWidget.
            measurement: a Measurement object
            global_settings: a GlobalSettings object
            statusbar: a QStatusBar object
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_depth_profile_params.ui", self)

        self.parent = parent
        self.measurement = measurement
        self.__global_settings = global_settings
        self.statusbar = statusbar
        
        # Connect buttons
        self.OKButton.clicked.connect(self.__accept_params)
        self.cancelButton.clicked.connect(self.close)

        self.__reference_density_label = None
        self.__reference_density_spinbox = None

        self.locale = QLocale.c()

        self.spin_systerr.setLocale(self.locale)

        self.radioButtonNm.clicked.connect(self.__add_reference_density)
        self.radioButtonAtPerCm2.clicked.connect(
            self.__remove_reference_density)

        m_name = self.measurement.name
        if m_name not in DepthProfileDialog.checked_cuts:
            DepthProfileDialog.checked_cuts[m_name] = set()

        gutils.fill_cuts_treewidget(
            self.measurement, self.treeWidget.invisibleRootItem(),
            use_elemloss=True)
        self.used_cuts = DepthProfileDialog.checked_cuts[m_name]
        
        x_unit = DepthProfileDialog.x_unit
        radio_buttons = self.findChildren(QtWidgets.QRadioButton)
        for radio_button in radio_buttons:
            radio_button.setChecked(radio_button.text() == x_unit)

        if x_unit == "nm":
            self.__add_reference_density()
        
        self.check_0line.setChecked(DepthProfileDialog.line_zero)
        self.check_scaleline.setChecked(DepthProfileDialog.line_scale)
        
        self.label_cross.setText(str(
            self.__global_settings.get_cross_sections()
        ))
        self.spin_systerr.setValue(DepthProfileDialog.systerr)

        self.__show_important_settings()
        self.exec_()

    @gutils.disable_widget
    def __accept_params(self, *_):
        """Accept given parameters.

        Args:
            *_: unused event args
        """
        self.status_msg = ""
        sbh = StatusBarHandler(self.statusbar)
        sbh.reporter.report(10)

        try:
            output_dir = self.measurement.get_depth_profile_dir()
            
            # Get the filepaths of the selected items
            used_cuts = self.used_cuts
            DepthProfileDialog.checked_cuts[self.measurement.name] = \
                set(used_cuts)
            # TODO could take care of RBS selection here
            elements = [
                Element.from_string(fp.name.split(".")[1])
                for fp in used_cuts
            ]

            # Get the x-axis unit to be used from the radio buttons
            x_unit = DepthProfileDialog.x_unit
            radio_buttons = self.findChildren(QtWidgets.QRadioButton)
            for radio_button in radio_buttons:
                if radio_button.isChecked():
                    x_unit = radio_button.text()
            DepthProfileDialog.x_unit = x_unit
            
            DepthProfileDialog.line_zero = self.check_0line.isChecked()
            DepthProfileDialog.line_scale = self.check_scaleline.isChecked()
            DepthProfileDialog.systerr = self.spin_systerr.value()

            sbh.reporter.report(20)

            # If items are selected, proceed to generating the depth profile
            if used_cuts:
                self.status_msg = "Please wait. Creating depth profile."
                if self.parent.depth_profile_widget:
                    self.parent.del_widget(self.parent.depth_profile_widget)

                # If reference density changed, update value to measurement
                if self.__reference_density_spinbox is not None:
                    if self.measurement.reference_density != \
                            self.__reference_density_spinbox.value():
                        self.measurement.reference_density = \
                            self.__reference_density_spinbox.value()
                        self.measurement.to_file()
                
                self.parent.depth_profile_widget = DepthProfileWidget(
                    self.parent, output_dir, used_cuts, elements, x_unit,
                    DepthProfileDialog.line_zero, DepthProfileDialog.line_scale,
                    DepthProfileDialog.systerr,
                    progress=sbh.reporter.get_sub_reporter(
                        lambda x: 30 + 0.6 * x
                    ))

                sbh.reporter.report(90)
                
                icon = self.parent.icon_manager.get_icon(
                    "depth_profile_icon_2_16.png")
                self.parent.add_widget(
                    self.parent.depth_profile_widget, icon=icon)
                self.close()
            else:
                self.status_msg = "Please select .cut file[s] to create " \
                                  "depth profiles."
        except Exception as e:
            error_log = f"Exception occurred when trying to create depth " \
                        f"profiles: {e}"
            logging.getLogger(self.measurement.name).error(error_log)
        finally:
            sbh.reporter.report(100)

    def __add_reference_density(self):
        """
        Add a filed for modifying the reference density.
        """
        layout = self.horizontalAxisUnitsLayout

        ref_density_label = QtWidgets.QLabel(
            '<html><head/><body><p>Reference density [g/cm<span '
            'style=" vertical-align:super;">3</span>]:</p></body></html>')

        ref_density_spin_box = QtWidgets.QDoubleSpinBox()
        ref_density_spin_box.setMaximum(9999.00)
        ref_density_spin_box.setDecimals(2)
        ref_density_spin_box.setEnabled(True)
        ref_density_spin_box.setLocale(self.locale)

        ref_density_spin_box.setValue(self.measurement.reference_density)

        layout.insertWidget(3, ref_density_label)
        layout.insertWidget(4, ref_density_spin_box)

        self.__reference_density_label = ref_density_label
        self.__reference_density_spinbox = ref_density_spin_box

    def __remove_reference_density(self):
        """
        Remove reference density form dialog if it is there.
        """
        if self.__reference_density_spinbox and self.__reference_density_label:
            layout = self.horizontalAxisUnitsLayout

            layout.removeWidget(self.__reference_density_label)
            self.__reference_density_label.deleteLater()

            layout.removeWidget(self.__reference_density_spinbox)
            self.__reference_density_spinbox.deleteLater()

            self.__reference_density_spinbox = None
            self.__reference_density_label = None

    def __update_eff_files(self):
        """Update efficiency files to UI which are used.
        """
        detector = self.measurement.get_detector_or_default()
        self.label_efficiency_files.setText(
            df.get_efficiency_text(self.treeWidget, detector))

    def __show_important_settings(self):
        """Show some important setting values in the depth profile parameter
        dialog for the user.
        """
        detector = self.measurement.get_detector_or_default()

        if self.measurement.use_request_settings:
            depth_step_for_stopping = \
                self.measurement.request.default_measurement\
                    .profile.depth_step_for_stopping
            number_of_depth_steps = \
                self.measurement.request.default_measurement\
                    .profile.number_of_depth_steps
            depth_step_for_output = \
                self.measurement.request.default_measurement\
                    .profile.depth_step_for_output
            depth_for_concentration_from = \
                self.measurement.request.default_measurement\
                    .profile.depth_for_concentration_from
            depth_for_concentration_to = \
                self.measurement.request.default_measurement\
                    .profile.depth_for_concentration_to
        else:
            depth_step_for_stopping = self.measurement.\
                profile.depth_step_for_stopping
            number_of_depth_steps = self.measurement.\
                profile.number_of_depth_steps
            depth_step_for_output = self.measurement.\
                profile.depth_step_for_output
            depth_for_concentration_from = self.measurement\
                .profile.depth_for_concentration_from
            depth_for_concentration_to = self.measurement\
                .profile.depth_for_concentration_to

        self.label_calibslope.setText(str(detector.tof_slope))
        self.label_caliboffset.setText(str(detector.tof_offset))
        self.label_depthstop.setText(str(depth_step_for_stopping))
        self.label_depthnumber.setText(str(number_of_depth_steps))
        self.label_depthbin.setText(str(depth_step_for_output))
        self.label_depthscale.setText("{0} - {1}".format(
            depth_for_concentration_from,
            depth_for_concentration_to))

        self.__update_eff_files()
        

class DepthProfileWidget(QtWidgets.QWidget):
    """Depth Profile widget which is added to measurement tab.
    """
    save_file = "widget_depth_profile.save"
    
    def __init__(self, parent: BaseTab, output_dir: Path, use_cuts: List[Path],
                 elements: List[Element], x_units: str, line_zero: bool,
                 line_scale: bool, systematic_error: float,
                 progress: Optional[ProgressReporter] = None):
        """Inits widget.
        
        Args:
            parent: a MeasurementTabWidget.
            output_dir: full path to depth file location
            use_cuts: A string list representing Cut files.
            elements: A list of Element objects that are used in depth profile.
            x_units: Units to be used for x-axis of depth profile.
            line_zero: A boolean representing if vertical line is drawn at zero.
            line_scale: A boolean representing if horizontal line is drawn at 
                        the defined depth scale.
            systematic_error: A double representing systematic error.
        """
        try:
            super().__init__()
            uic.loadUi(gutils.get_ui_dir() / "ui_depth_profile.ui", self)

            self.parent = parent
            self.icon_manager = parent.icon_manager
            self.measurement: Measurement = parent.obj
            self.output_dir = output_dir
            self.elements = elements
            self.x_units = x_units
            self.use_cuts = use_cuts
            self.__line_zero = line_zero
            self.__line_scale = line_scale
            self.__systerr = systematic_error

            if progress is not None:
                sub_progress = progress.get_sub_reporter(
                    lambda x: 0.5 * x
                )
            else:
                sub_progress = None

            # TODO do this in thread
            depth_files.generate_depth_files(
                self.use_cuts, self.output_dir, self.measurement,
                progress=sub_progress
            )

            if progress is not None:
                progress.report(50)
            
            # Check for RBS selections.
            rbs_list = cut_file.get_rbs_selections(self.use_cuts)

            for rbs in rbs_list:
                # Search and replace instances of Beam element with scatter
                # elements.
                # When loading request, the scatter element is already
                # replaced. This is essentially done only when creating
                # a new Depth Profile graph.
                # TODO seems overly complicated. This stuff should be sorted
                #  before initializing the widget
                element = Element.from_string(rbs.split(".")[0])
                for i, elem in enumerate(elements):
                    if elem == element:
                        elements[i] = rbs_list[rbs]

            if self.__line_scale:
                depth_scale = \
                    self.measurement.profile.depth_for_concentration_from, \
                    self.measurement.profile.depth_for_concentration_to
            else:
                depth_scale = None

            if progress is not None:
                sub_progress = progress.get_sub_reporter(
                    lambda x: 50 + 0.5 * x)
            else:
                sub_progress = None

            self.matplotlib = MatplotlibDepthProfileWidget(
                self, self.output_dir, self.elements, rbs_list,
                depth_scale=depth_scale, x_units=self.x_units,
                add_legend=True, add_line_zero=self.__line_zero,
                systematic_error=self.__systerr, progress=sub_progress)
        except Exception as e:
            msg = f"Could not create Depth Profile graph: {e}"
            logging.getLogger(self.measurement.name).error(msg)
            if hasattr(self, "matplotlib"):
                self.matplotlib.delete()
        finally:
            if progress is not None:
                progress.report(100)

    def delete(self):
        """Delete variables and do clean up.
        """
        self.matplotlib.delete()
        self.matplotlib = None
        self.close()

    def closeEvent(self, evnt):
        """Reimplemented method when closing widget.
        """
        self.parent.depth_profile_widget = None
        file = Path(self.measurement.directory, self.save_file)
        try:
            file.unlink()
        except OSError:
            pass
        super().closeEvent(evnt)

    def save_to_file(self):
        """Save object information to file.
        """
        output_dir = Path.relative_to(
            self.output_dir, self.measurement.directory)

        file = Path(self.measurement.get_depth_profile_dir(), self.save_file)

        with file.open("w") as fh:
            fh.write("{0}\n".format(str(output_dir)))
            fh.write("{0}\n".format("\t".join([
                str(element) for element in self.elements])))
            fh.write("{0}\n".format("\t".join([
                str(cut) for cut in self.use_cuts])))
            fh.write("{0}\n".format(self.x_units))
            fh.write("{0}\n".format(self.__line_zero))
            fh.write("{0}\n".format(self.__line_scale))
            fh.write("{0}".format(self.__systerr))

    def update_use_cuts(self):
        """
        Update used cuts list with new Measurement cuts.
        """
        changes_dir = self.measurement.get_changes_dir()
        df.update_cuts(
            self.use_cuts, self.measurement.get_cuts_dir(), changes_dir)

        self.output_dir = self.measurement.get_depth_profile_dir()
