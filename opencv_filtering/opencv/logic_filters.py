# -*- coding: utf-8 -*-
import cv2  # import OpenCV 3 with *CONTRIBUTIONS*
# import random
import numpy as np

from .logic_logger import logging


class Filters:
    """ OpenCV filters """
    def __init__(self, master, filter_num=0):
        """ Initialize filters """
        self.current_filter = filter_num  # current OpenCV filter_num
        self.master = master  # link to the main GUI window
        self.frame = None  # current frame
        self.previous = None  # previous frame (gray or color)
        self.background_subtractor = None
        self.opt_flow = {  # container for Optical Flow algorithm
            # Parameters for Shi Tomasi corner detection
            'feature_params': dict(maxCorners=100,
                                   qualityLevel=0.3,
                                   minDistance=7,
                                   blockSize=7),
            # Parameters for Lucas Kanade optical flow
            'lk_params': dict(winSize=(15, 15),
                              maxLevel=2,
                              criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)),
            # Create some random colors
            'color': np.random.randint(0, 255, (100, 3)),
            # Container for corner points of the previous frame
            'points': None,
            # Container for image mask
            'mask': None,
        }
        # List of filters in the following format: [name, function, description]
        # Filter functions take frame, convert it and return converted image
        self.container = [
            ['Unchanged', self.filter_unchanged, 'Unchanged original image'],
            ['Canny', self.filter_canny, 'Canny edge detection'],
            ['Threshold', self.filter_threshold, 'Adaptive Gaussian threshold'],
            ['Harris', self.filter_harris, 'Harris corner detection'],
            ['SIFT', self.filter_sift, 'Scale-Invariant Feature Transform (SIFT), patented'],
            ['SURF', self.filter_surf, 'Speeded-Up Robust Features (SURF), patented'],
            ['ORB', self.filter_orb, 'Oriented FAST and Rotated BRIEF (ORB), free'],
            ['BRIEF', self.filter_brief, 'BRIEF descriptors with the help of CenSurE (STAR) detector'],
            ['Contours', self.filter_contours, 'Draw contours with mean colors inside them'],
            ['Blur', self.filter_blur, 'Blur (Gaussian, median, bilateral or classic)'],
            ['Motion', self.filter_motion, 'Motion detection'],
            ['Background', self.filter_background, 'Background subtractor (KNN, MOG2, MOG or GMG)'],
            ['Skin', self.filter_skin, 'Skin tones detection'],
            ['Optical Flow', self.filter_optflow, 'Lucas Kanade optical flow'],
        ]
        self.master.title(f'OpenCV Filtering - {self.container[self.current_filter][2]}')

    def get_filter(self):
        """ Get filter name """
        return self.container[self.current_filter][0]

    def set_filter(self, current):
        """ Set current filter """
        self.previous = None
        self.current_filter = current
        logging.info(f'Set filter to {self.get_filter()}')
        self.master.title('OpenCV Filtering - ' + self.container[self.current_filter][2])

    def next_filter(self):
        """ Set next OpenCV filter to the video loop """
        current = (self.current_filter + 1) % len(self.container)
        self.set_filter(current)

    def last_filter(self):
        """ Set last OpenCV filter to the video loop """
        current = (self.current_filter - 1) % len(self.container)
        self.set_filter(current)

    def get_names(self):
        """ Get list of filter names """
        return [name[0] for name in self.container]

    def convert(self, frame):
        """ Convert frame using current filter function """
        self.frame = frame
        return self.container[self.current_filter][1]()

    def filter_unchanged(self):
        """ Show unchanged frames """
        return self.frame

    def filter_canny(self):
        """ Canny edge detection """
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)  # convert to gray scale
        return cv2.Canny(gray, 100, 200)  # Canny edge detection

    def filter_threshold(self):
        """ Adaptive Gaussian threshold """
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)  # convert to gray scale
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    def filter_harris(self):
        """ Harris corner detection """
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)  # convert to gray scale
        gray = np.float32(gray)  # convert to NumPy array
        # k-size parameter is odd and must be [3, 31]
        dest = cv2.cornerHarris(src=gray, blockSize=2, ksize=5, k=0.07)
        dest = cv2.dilate(dest, None)  # dilate corners for result, not important
        self.frame[dest > 0.01 * dest.max()] = [0, 0, 255]
        return self.frame

    def get_features(self, xfeatures):
        """ Keypoints / features for SIFT, SURF and ORB filters """
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)  # convert to gray scale
        keypoints, descriptor = xfeatures.detectAndCompute(gray, None)
        return cv2.drawKeypoints(image=self.frame, outImage=self.frame, keypoints=keypoints,
                                 flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS, color=(51, 163, 236))

    def filter_sift(self):
        """ Scale-Invariant Feature Transform (SIFT). It is patented and not totally free """
        try:
            return self.get_features(cv2.xfeatures2d.SIFT_create())
        except cv2.error:
            return self.frame  # return unchanged frame

    def filter_surf(self):
        """ Speeded-Up Robust Features (SURF). It is patented and not totally free """
        try:
            return self.get_features(cv2.xfeatures2d.SURF_create(4000))
        except cv2.error:
            return self.frame  # return unchanged frame

    def filter_orb(self):
        """ Oriented FAST and Rotated BRIEF (ORB). It is not patented and totally free """
        return self.get_features(cv2.ORB_create())

    def filter_brief(self):
        """ BRIEF descriptors with the help of CenSurE (STAR) detector """
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)  # convert to gray scale
        keypoints = cv2.xfeatures2d.StarDetector_create().detect(gray, None)
        keypoints, descriptor = cv2.xfeatures2d.BriefDescriptorExtractor_create().compute(gray, keypoints)
        return cv2.drawKeypoints(image=self.frame, outImage=self.frame, keypoints=keypoints,
                                 flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS, color=(51, 163, 236))

    def filter_contours(self):
        """ Draw contours with mean colors inside them """
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)  # convert to gray scale
        frame2 = self.frame.copy()  # make a copy
        for threshold in [15, 50, 100, 240]:  # use various thresholds
            ret, thresh = cv2.threshold(gray, threshold, 255, 0)
            image, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                mask = np.zeros(gray.shape, np.uint8)  # create empty mask
                cv2.drawContours(mask, [contour], 0, 255, -1)  # fill mask with white color
                mean = cv2.mean(self.frame, mask=mask)  # find mean color inside mask
                cv2.drawContours(frame2, [contour], 0, mean, -1)  # draw frame with masked mean color
            cv2.drawContours(frame2, contours, -1, (0, 0, 0), 1)  # draw contours with black color
        return frame2

    def filter_blur(self):
        """ Blur (Gaussian, median, bilateral or classic) """
        # return cv2.GaussianBlur(self.frame, (29, 29), 0)  # Gaussian blur
        # return cv2.medianBlur(self.frame, 29)  # Median blur
        # return cv2.bilateralFilter(self.frame, 11, 80, 80)  # Bilateral filter preserves the edges
        return cv2.blur(self.frame, (29, 29))  # Blur classic

    def filter_motion(self):
        """ Motion detection """
        if self.previous is None or self.previous.shape != self.frame.shape:
            self.previous = self.frame.copy()  # remember previous frame
            return self.frame  # return unchanged frame
        gray1 = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)  # convert to grayscale
        gray2 = cv2.cvtColor(self.previous, cv2.COLOR_BGR2GRAY)
        self.previous = self.frame.copy()  # remember previous frame
        return cv2.absdiff(gray1, gray2)  # get absolute difference between two frames

    def filter_background(self):
        """ Background subtractor (KNN, MOG2, MOG or GMG) """
        if self.background_subtractor is None:
            # self.background_subtractor = cv2.createBackgroundSubtractorKNN(detectShadows=True)
            self.background_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
            # self.background_subtractor = cv2.bgsegm.createBackgroundSubtractorGMG()
            # self.background_subtractor = cv2.bgsegm.createBackgroundSubtractorMOG()
        fgmask = self.background_subtractor.apply(self.frame)
        return self.frame & cv2.cvtColor(fgmask, cv2.COLOR_GRAY2BGR)

    def filter_skin(self):
        """ Skin tones detection"""
        # Determine upper and lower HSV limits for skin tones
        lower = np.array([0, 100, 0], dtype='uint8')
        upper = np.array([50, 255, 255], dtype='uint8')
        # Switch to HSV
        hsv = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        # Find mask of pixels within HSV range
        skin_mask = cv2.inRange(hsv, lower, upper)
        skin_mask = cv2.GaussianBlur(skin_mask, (9, 9), 0)  # noise suppression
        # Kernel for morphology operation
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))
        # CLOSE (dilate / erode)
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        skin_mask = cv2.GaussianBlur(skin_mask, (9, 9), 0)  # noise suppression
        # Display only the masked pixels
        return cv2.bitwise_and(self.frame, self.frame, mask=skin_mask)

    def filter_optflow(self):
        """ Lucas Kanade optical flow """
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        frame = self.frame.copy()  # copy the frame
        if self.previous is None or self.previous.shape != gray.shape:
            self.previous = gray.copy()  # save previous gray frame
            # Find new corner points of the frame
            self.opt_flow['points'] = cv2.goodFeaturesToTrack(
                gray, mask=None,
                **self.opt_flow['feature_params'])
            # Create a new mask image for drawing purposes
            self.opt_flow['mask'] = np.zeros_like(self.frame.copy())
        #
        # If motion is large this method will fail. Ignore exceptions
        try:
            # Calculate optical flow. cv2.error could happen here.
            points, st, err = cv2.calcOpticalFlowPyrLK(
                self.previous, gray,
                self.opt_flow['points'], None, **self.opt_flow['lk_params'])
            # Select good points
            good_new = points[st == 1]  # TypeError 'NoneType' could happen here
            good_old = self.opt_flow['points'][st == 1]
            # Draw the tracks
            for i, (new, old) in enumerate(zip(good_new, good_old)):
                a, b = new.ravel()
                c, d = old.ravel()
                # Draw lines in the mask
                self.opt_flow['mask'] = cv2.line(self.opt_flow['mask'], (a, b), (c, d),
                                                 self.opt_flow['color'][i].tolist(), 2)
                # Draw circles in the frame
                frame = cv2.circle(frame, (a, b), 5, self.opt_flow['color'][i].tolist(), -1)
            # Update the previous frame and previous points
            self.previous = gray.copy()
            self.opt_flow['points'] = good_new.reshape(-1, 1, 2)
            return cv2.add(frame, self.opt_flow['mask'])  # concatenate frame and mask images
        except (TypeError, cv2.error):
            self.previous = None  # set optical flow to None if exception occurred
            return self.frame  # return unchanged frame when error



"""
modes = {
    'e': 'Affine1',     # Affine random rotation and shift
    'f': 'Affine2',     # Affine random transformations
    'g': 'Perspective', # Perspective random transformations
    'h': 'Equalize',    # Histogram Equalization
    'i': 'CLAHE',       # CLAHE Contrast Limited Adaptive Histogram Equalization
    'j': 'LAB',         # Increase the contrast of an image (LAB color space + CLAHE)
    'k': 'Pyramid',     # Image pyramid
    'l': 'Laplacian',   # Laplacian gradient filter
    'm': 'Sobel X',     # Sobel / Scharr vertical gradient filter
    'n': 'Sobel Y',     # Sobel / Scharr horizontal gradient filter
    'o': 'Blobs',       # Blob detection
}
mode_affine1     = modes['e']
mode_affine2     = modes['f']
mode_perspective = modes['g']
mode_equalize    = modes['h']
mode_clahe       = modes['i']
mode_lab         = modes['j']
mode_pyramid     = modes['k']
mode_laplacian   = modes['l']
mode_sobelx      = modes['m']
mode_sobely      = modes['n']
mode_blobs       = modes['o']

rotation = 0
shift = [0, 0]
ptrs1 = np.float32([[0,0],[400,0],[0,400]])
ptrs2 = np.copy(ptrs1)
ptrs3 = np.float32([[0,0],[400,0],[0,400],[400,400]])
ptrs4 = np.copy(ptrs3)
detector1 = None

while True:
    if mode == mode_affine1:
        rotation += random.choice([-1, 1])  # random rotation anticlockwise/clockwise
        shift[0] += random.choice([-1, 1])  # random shift left/right on 1 pixel
        shift[1] += random.choice([-1, 1])  # random shift up/bottom on 1 pixel
        rows, cols = frame.shape[:2]
        m = cv2.getRotationMatrix2D((cols/2, rows/2), rotation, 1)  # rotation matrix
        frame = cv2.warpAffine(frame, m, (cols, rows))
        m = np.float32([[1, 0, shift[0]], [0, 1, shift[1]]])  # translation matrix
        frame = cv2.warpAffine(frame, m, (cols, rows))
    if mode == mode_affine2:
        for ptr in np.nditer(ptrs2, op_flags=['readwrite']):
            ptr += random.choice([-1, 1])  # apply random shift on 1 pixel foreach element
        rows, cols = frame.shape[:2]
        m = cv2.getAffineTransform(ptrs1, ptrs2)
        frame = cv2.warpAffine(frame, m, (cols, rows))
    if mode == mode_perspective:
        for ptr in np.nditer(ptrs4, op_flags=['readwrite']):
            ptr += random.choice([-1, 1])  # apply random shift on 1 pixel foreach element
        rows, cols = frame.shape[:2]
        m = cv2.getPerspectiveTransform(ptrs3, ptrs4)
        frame = cv2.warpPerspective(frame, m, (cols, rows))
    if mode == mode_equalize:
        b, g, r = cv2.split(frame)  # split on blue, green and red channels
        b2 = cv2.equalizeHist(b)  # apply Histogram Equalization to each channel
        g2 = cv2.equalizeHist(g)
        r2 = cv2.equalizeHist(r)
        frame = cv2.merge((b2,g2,r2))  # merge changed channels to the current frame
    if mode == mode_clahe:
        # clipLimit is 40 by default; tileSize is 8x8 by default
        clahe = cv2.createCLAHE(clipLimit=10., tileGridSize=(8,8))
        b, g, r = cv2.split(frame)  # split on blue, green and red channels
        b2 = clahe.apply(b)  # apply CLAHE to each channel
        g2 = clahe.apply(g)
        r2 = clahe.apply(r)
        frame = cv2.merge((b2, g2, r2))  # merge changed channels to the current frame
    if mode == mode_lab:
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)  # convert image to LAB color model
        l, a, b = cv2.split(lab)  # split on l, a, b channels
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l2 = clahe.apply(l)  # apply CLAHE to L-channel
        lab = cv2.merge((l2,a,b))  # merge enhanced L-channel with the a and b channels
        frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    if mode == mode_pyramid:
        h, w = frame.shape[:2]
        x, y = 0, int(h+h/2)
        image = np.zeros((y, w, 3), np.uint8)  # empty matrix filled with zeros
        image[:h, :w, :3] = frame
        for i in range(8):
            frame = cv2.pyrDown(frame)
            h, w = frame.shape[:2]
            image[y-h:y, x:x+w] = frame
            x += w
        frame = image
    if mode == mode_laplacian:
        #frame = cv2.Laplacian(gray, cv2.CV_8U)
        frame = np.uint8(np.absolute(cv2.Laplacian(gray, cv2.CV_64F)))
    if mode == mode_sobelx:
        #frame = cv2.Sobel(gray, cv2.CV_8U, 1, 0, ksize=5)
        #frame = np.uint8(np.absolute(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)))
        # If ksize=-1, a 3x3 Scharr filter is used which gives better results than 3x3 Sobel filter
        frame = cv2.Sobel(gray, cv2.CV_8U, 1, 0, ksize=-1)
        #frame = np.uint8(np.absolute(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=-1)))
    if mode == mode_sobely:
        #frame = cv2.Sobel(gray, cv2.CV_8U, 0, 1, ksize=5)
        #frame = np.uint8(np.absolute(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)))
        # If ksize=-1, a 3x3 Scharr filter is used which gives better results than 3x3 Sobel filter
        frame = cv2.Sobel(gray, cv2.CV_8U, 0, 1, ksize=-1)
        #frame = np.uint8(np.absolute(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=-1)))
    if mode == mode_blobs:
        if detector1 is None:
            # Setup SimpleBlobDetector parameters
            params = cv2.SimpleBlobDetector_Params()
            params.filterByColor = True
            params.blobColor = 255  # extract light blobs
            params.filterByArea = True
            params.maxArea = 40000
            params.filterByCircularity = True
            params.minCircularity = 0.7  # circularity of a square is 0.785
            # Set up the detector with default parameters.
            detector1 = cv2.SimpleBlobDetector_create(params)
            params.blobColor = 0  # extract dark blobs
            detector2 = cv2.SimpleBlobDetector_create(params)

        # Detect blobs
        keypoints1 = detector1.detect(frame)
        keypoints2 = detector2.detect(frame)

        # Draw detected blobs as green and blue circles
        # cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS ensures the size of the circle
        # corresponds to the size of a blob
        frame2 = cv2.drawKeypoints(frame, keypoints1, np.array([]), (0, 255, 0),
                                   cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        frame = cv2.drawKeypoints(frame2, keypoints2, np.array([]), (255, 0, 0),
                                  cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    cv2.imshow(window_name, frame)  # show frame
# """
