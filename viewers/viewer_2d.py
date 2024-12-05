"""
Module used to display 2D image.
"""

import cv2
import numpy as np

from scipy.spatial.transform import Rotation as R

AXIS_SIZE = 0.25
DISPLAY_SIZE = 960, 540

VIDEO_2D_FNAME = "outputs/output_2d.mp4"

class Viewer2D():
    """
    Class for displaying 2D image.
    """

    def __init__(
            self,
            camera_matrix: np.ndarray,
            dist_coeffs: np.ndarray,
            save_video: bool
            ) -> None:
        """
        Constructor.

        params:
        - camera_matrix: the camera matrix
        - dist_coeffs: the distortion coefficients
        - save_video: whether or not a video should be saved
        """
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs

        self.save_video = save_video
        if save_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'mp4v' for MP4 format
            self.video_writer = cv2.VideoWriter(VIDEO_2D_FNAME, fourcc, 20.0, DISPLAY_SIZE)

    def close(self):
        """
        Shuts down the viewer
        """

        if self.save_video:
            self.video_writer.release()
        cv2.destroyAllWindows()


    def view(
            self,
            frame: np.ndarray,
            camera_position: np.ndarray,
            points: np.ndarray,
            points_detected: np.ndarray
            ) -> bool:
        """
        Display the 2D image on the frame provided.

        params:
        - frame: the frame to display the image on
        - camera_position: the camera position
        - points: the points to display
        - points_detected: the points detected

        return:
        - bool: whether or not the script should terminate
        """

        rot_mc = R.from_euler('xyz', camera_position[3:]).as_matrix()

        ct = camera_position[:3].copy()


        # draw the detected points
        for p in points_detected:
            frame = self.draw_axis(frame, p[3:6], p[:3])

        # draw the points from the filter
        for p_ml in points:
            p_cl = (p_ml - ct) @ rot_mc
            frame = self.draw_point(frame, rot_mc, p_cl)

        frame = cv2.resize(frame, DISPLAY_SIZE)
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return True
        
        if self.save_video:
            self.video_writer.write(frame)

        return False

    def draw_point(
            self,
            frame: np.ndarray,
            rotation_vector: np.ndarray,
            t: np.ndarray
            ) -> np.ndarray:
        """
        Draw the points on the frame.

        params:
        - frame: the frame to draw the points on
        - points: the points to draw

        return:
        - the frame with the points drawn
        """

        # project the points onto the image
        image_points, _ = cv2.projectPoints(
            np.array([0, 0, 0], dtype=np.float64),
            np.array([0, 0, 0], dtype=np.float64),
            t,
            self.camera_matrix,
            self.dist_coeffs
        )

        # convert image points to int
        image_points = image_points.astype(int)

        frame = cv2.circle(
            frame,
            tuple(image_points[0].ravel()),
            10,
            (128, 0, 0),
            -1
        )

        return frame

    def draw_axis(
            self,
            frame: np.ndarray,
            rotation_vector: np.ndarray,
            t: np.ndarray
            ) -> np.ndarray:
        """
        https://stackoverflow.com/questions/30207467/how-to-draw-3d-coordinate-axes-with-opencv-for-face-pose-estimation
        """

        # unit is mm
        # rotV, _ = cv2.Rodrigues(R)

        # 3D points to draw the axis
        axis_points = np.array(
            [[1, 0, 0],
             [0, 1, 0],
             [0, 0, 1],
             [0, 0, 0]],
            dtype=np.float64
        ).reshape(-1, 3)
        axis_points *= AXIS_SIZE

        # projected onto the image
        axis_image_points, _ = cv2.projectPoints(
            axis_points,
            rotation_vector,
            t,
            self.camera_matrix,
            self.dist_coeffs
        )

        point0 = tuple(axis_image_points[0].ravel())
        point1 = tuple(axis_image_points[1].ravel())
        point2 = tuple(axis_image_points[2].ravel())
        point3 = tuple(axis_image_points[3].ravel())

        # convert to ints
        point0 = (int(point0[0]), int(point0[1]))
        point1 = (int(point1[0]), int(point1[1]))
        point2 = (int(point2[0]), int(point2[1]))
        point3 = (int(point3[0]), int(point3[1]))

        # draw the lines
        thickness = 8
        frame = cv2.line(frame, point3, point0, (255,0,0), thickness)
        frame = cv2.line(frame, point3, point1, (0,255,0), thickness)
        frame = cv2.line(frame, point3, point2, (0,0,255), thickness)

        return frame