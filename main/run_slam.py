"""The main script to run the SLAM system.

Reads the video file,
processes each frame,
and displays the results in 2D and 3D.
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
import tqdm

import viewers.viewer_2d as v2d
import viewers.viewer_3d as v3d
from filters.base_filter import BaseFilter
from filters.ekf_with_rotations import EKF_Rotations
from filters.extended_kalman_filter import EKF
from filters.factor_graph import FactorGraph
from outputs.trajectory_writer import TrajectoryWriter

# calibration files
CALIB_MTX_FILE = "calibration/camera_matrix.npy"
DIST_COEFFS_FILE = "calibration/dist_coeffs.npy"

# output files
TRAJECTORY_TEXT_FILE = "outputs/trajectory.txt"

# map
LOAD_MAP = False
MAP_FILE = "outputs/map.txt"

# display flags
DISPLAY_3D = True
DISPLAY_2D = True

# contingent on the display flags
SAVE_2D = True
SAVE_3D = True

# image and display sizes
IMAGE_SIZE = 1920, 1080
DISPLAY_SIZE = 960, 540

# set numpy to print only 3 decimal places
np.set_printoptions(precision=7)

# set numpy to print in scientific notation only if the number is very large
np.set_printoptions(suppress=True)


def load_matrices() -> tuple[np.ndarray, np.ndarray]:
    """Load camera calibration matrices."""
    # assert that the camera matrix and distortion coefficients are saved
    if not Path(CALIB_MTX_FILE).exists():
        msg = "Camera matrix not found. Run calibration.py first."
        raise FileNotFoundError(msg)
    if not Path(DIST_COEFFS_FILE).exists():
        msg = "Distortion coefficients not found. Run calibration.py first."
        raise FileNotFoundError(msg)

    calib_matrix = np.load(CALIB_MTX_FILE)
    dist_coeffs = np.load(DIST_COEFFS_FILE)

    return calib_matrix, dist_coeffs


def init_tracker(filter_type: str, initial_pose: np.ndarray) -> BaseFilter:
    """Initialize the tracker based on the filter type."""
    if filter_type == "ekf":
        return EKF(initial_pose)
    if filter_type == "ekf_rotations":
        return EKF_Rotations(initial_pose)
    if filter_type == "factorgraph":
        return FactorGraph(initial_pose)

    msg = f"Unknown filter type: {filter_type}"
    raise ValueError(msg)


def main(cmdline_args: argparse.Namespace) -> None:
    """Run main thread."""
    # load the camera matrix and distortion coefficients, initialize the tracker
    initial_pose = np.array(
        # x, y, z, qw, qx, qy, qz, ex, ey, ez
        [0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    )

    tracker = init_tracker(
        cmdline_args.filter,
        initial_pose,
    )

    # use the camera
    cap = cv2.VideoCapture(cmdline_args.video)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)

    if DISPLAY_3D:
        camera_viewer_3d = v3d.Viewer3D(export_video=SAVE_3D)
    if DISPLAY_2D:
        image_viewer_2d = v2d.Viewer2D(export_video=SAVE_2D)

    iterator = tqdm.tqdm(
        range(int(cap.get(cv2.CAP_PROP_FRAME_COUNT))),  # total number of frames
        desc="Processing frames",
        unit="frames",
    )

    with TrajectoryWriter(TRAJECTORY_TEXT_FILE) as cam_traj_writer:
        for _ in iterator:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, IMAGE_SIZE)

            # find markers, update system state
            frame, camera_pose, marker_poses, detected_poses = (
                tracker.process_frame(frame)
            )

            # save txt file
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
            cam_traj_writer.write(timestamp, camera_pose)

            if DISPLAY_3D:
                camera_viewer_3d.view(
                    camera_pose,
                    marker_poses,
                    detected_poses,
                )
            if DISPLAY_2D:
                q = image_viewer_2d.view(
                    frame,
                    camera_pose,
                    marker_poses,
                    detected_poses,
                )
                if q:
                    break

    tracker.save_map("outputs/map.txt")

    if DISPLAY_3D:
        camera_viewer_3d.close()
    if DISPLAY_2D:
        image_viewer_2d.close()

    cap.release()


if __name__ == "__main__":
    # get arguments
    parser = argparse.ArgumentParser(description="Run the SLAM system")
    parser.add_argument(
        "--video",
        type=str,
        help="Path to video file",
        default="input_video.mp4",
    )
    parser.add_argument(
        "--filter",
        type=str,
        help="Filter to use (ekf, factorgraph)",
        default="ekf",
    )

    args = parser.parse_args()

    video_file = args.video

    main(args)
