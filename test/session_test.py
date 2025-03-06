from random import sample
from assets.funcs import ResumeDialog, projectDialog, projectInit, session
from unittest.mock import patch
import os
import json


def test_resumeDialog(qtbot):
    dialog = ResumeDialog()
    dialog.show()

    qtbot.addWidget(dialog)

    assert dialog.isVisible() is True

    dialog.resume.click()

    assert dialog.isVisible() is False

    assert dialog.result() == 1

    dialog.show()

    assert dialog.isVisible() is True

    dialog.new.click()

    assert dialog.isVisible() is False

    assert dialog.result() == 0


def test_projectDialog(qtbot):
    dialog = projectDialog()
    dialog.show()

    qtbot.addWidget(dialog)

    # check if the dialog launches as expected
    assert dialog.isVisible() is True

    # test cancel button
    dialog.cancel.click()

    assert dialog.isVisible() is False

    assert dialog.result() == 0

    dialog.show()

    # test select button

    assert dialog.isVisible() is True

    project_path = "./data/project.json"

    with patch(
        "PyQt5.QtWidgets.QFileDialog.getOpenFileName",
        return_value=(project_path, "JSON (*.json)"),
    ):
        dialog.select.click()

    assert dialog.isVisible() is False

    assert dialog.result() == 1

    assert dialog.project.text() == project_path

    dialog.show()


def test_projectInit(qtbot):
    dialog = projectInit()
    dialog.show()

    qtbot.addWidget(dialog)

    # check if the dialog launches as expected

    assert dialog.isVisible() is True

    # test cancel button
    dialog.cancel.click()

    assert dialog.isVisible() is False

    assert dialog.result() == 0

    dialog.show()

    # test initialise button

    assert dialog.isVisible() is True

    project_name = "Chapter 4"
    project_type = "Plot"
    data_folder = "./data"
    project_path = "./data/videos"
    data_path = "./data/data.json"
    size_path = "./data/sizes.json"
    behaviour_path = "./data/behaviours.json"
    replicates = 5
    plots = 4
    sample_n = 10
    sample_s = 120

    dialog.project_name.setText(project_name)
    dialog.project_type.setCurrentText(project_type)
    dialog.video_folder.setText(project_path)
    dialog.data_file.setText(data_path)
    dialog.data_folder.setText(data_folder)
    dialog.size_file.setText(size_path)
    dialog.behaviour_file.setText(behaviour_path)
    dialog.replicates.setValue(replicates)
    dialog.plots.setValue(plots)
    dialog.sample_n.setValue(sample_n)
    dialog.sample_s.setValue(sample_s)

    with patch(
        "PyQt5.QtWidgets.QFileDialog.getSaveFileName",
        return_value="project.json",
    ):
        dialog.init.click()

    assert dialog.isVisible() is False

    # check if project.json file is created

    assert dialog.result() == 1

    assert dialog.project_info is not None

    assert os.path.exists("project.json") is True


def test_Session_new():
    project_info = None

    with (
        patch.object(ResumeDialog, "exec_"),
        patch.object(ResumeDialog, "result", return_value=0),
    ):
        file, data, start_time = session(project_info)

    assert file is None
    assert isinstance(data, dict)
    assert start_time is None


def test_Session_resume():
    if os.path.exists("project.json") is False:
        test_projectInit()
    else:
        # load project.json
        with open("project.json", "r") as file:
            project_info = json.load(file)

    with (
        patch.object(ResumeDialog, "exec_"),
        patch.object(ResumeDialog, "result", return_value=1),
    ):
        file, data, start_time = session(project_info)

    assert file is not None
    assert isinstance(data, dict)
    assert start_time is not None
