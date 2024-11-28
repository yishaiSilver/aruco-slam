"""
The main script to run the SLAM system. 
Reads the video file, 
processes each frame, 
and displays the results in 2D and 3D.
"""
import os
import cv2
import numpy as np
import tqdm

from aruco_slam import ArucoSlam
import viewer_3d as v3d
import viewer_2d as v2d

DISPLAY_3D = True
DISPLAY_2D = True

CALIB_MTX_FILE = 'calibration/camera_matrix.npy'
DIST_COEFFS_FILE = 'calibration/dist_coeffs.npy'

VIDEO_FILE = 'video_scaled.mp4'

IMAGE_SIZE = 1920, 1080
DISPLAY_SIZE = 960, 540

# set numpy to print only 3 decimal places
np.set_printoptions(precision=3)

# set numpy to print in scientific notation only if the number is very large
np.set_printoptions(suppress=True)

def load_matrices():
    # assert that the camera matrix and distortion coefficients are saved
    assert os.path.exists(CALIB_MTX_FILE), \
        'Camera matrix not found. Run calibration.py first.'
    assert os.path.exists(DIST_COEFFS_FILE), \
        'Distortion coefficients not found. Run calibration.py first.'
    
    calib_matrix = np.load(CALIB_MTX_FILE)
    dist_coeffs = np.load(DIST_COEFFS_FILE)

    return calib_matrix, dist_coeffs

def correct_rotation(image):
    h, w, _ = image.shape
    if h > w:
        image = cv2.transpose(image)
        image = cv2.flip(image, 1)
    return image

def main():
    calib_matrix, dist_coeffs = load_matrices()

    # load the camera matrix and distortion coefficients, initialize the tracker
    initial_pose = np.array([0, 0, 0, 0, 0, 0]) # x, y, z, roll, pitch, yaw
    tracker = ArucoSlam(initial_pose, calib_matrix, dist_coeffs)

    # use the camera
    cap = cv2.VideoCapture(VIDEO_FILE)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
    
    tracked_positions = []
    tracked_markers = []
    camera_markers = []

    if DISPLAY_3D:
        camera_viewer_3d = v3d.Viewer3D(IMAGE_SIZE)
    if DISPLAY_2D:
        image_viewer_2d = v2d.Viewer2D(calib_matrix, dist_coeffs)

    # number of frames
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    iterator = tqdm.tqdm(range(frames), desc='Processing frames', unit='frames')

    i = 0
    while True:
        i += 1

        iterator.update(1)
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, IMAGE_SIZE)

        # find markers, update system state
        frame, camera_pose, marker_poses, detected_poses = \
            tracker.process_frame(frame)

        if DISPLAY_3D:
            camera_viewer_3d.view(
                camera_pose,
                marker_poses,
                detected_poses
            )
        if DISPLAY_2D:
            frame = image_viewer_2d.view(
                frame,
                camera_pose,
                marker_poses,
                detected_poses
            )
            frame = cv2.resize(frame, DISPLAY_SIZE)
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break   

    cap.release()
    cv2.destroyAllWindows()

    return tracked_positions, tracked_markers, camera_markers

if __name__ == '__main__':
    positions, markers, camera_markers = main()