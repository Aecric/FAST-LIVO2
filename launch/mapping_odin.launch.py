#!/usr/bin/python3

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share_dir = get_package_share_directory("fast_livo")
    default_params = os.path.join(share_dir, "config", "odin.yaml")
    default_camera = os.path.join(share_dir, "config", "camera_odin.yaml")
    rviz_config = os.path.join(share_dir, "rviz_cfg", "fast_livo2.rviz")

    params_arg = DeclareLaunchArgument(
        "params_file", default_value=default_params,
        description="FAST-LIVO2 Odin parameter file")
    camera_arg = DeclareLaunchArgument(
        "camera_params_file", default_value=default_camera,
        description="Odin camera parameter file")
    rviz_arg = DeclareLaunchArgument(
        "use_rviz", default_value="False",
        description="Launch RViz2")
    return LaunchDescription([
        params_arg,
        camera_arg,
        rviz_arg,
        Node(
            package="fast_livo",
            executable="fastlivo_mapping",
            name="laserMapping",
            parameters=[
                LaunchConfiguration("params_file"),
                LaunchConfiguration("camera_params_file"),
            ],
            output="screen",
        ),
        Node(
            condition=IfCondition(LaunchConfiguration("use_rviz")),
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            arguments=["-d", rviz_config],
            output="screen",
        ),
    ])
