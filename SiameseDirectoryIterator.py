from keras import backend as K
from keras.preprocessing import image
from random import shuffle
import numpy as np
import numpy.random as rng
import os


class SiameseDirectoryIterator(image.DirectoryIterator):
    def __init__(self, directory, image_data_generator,
                 bounding_boxes: dict = None, landmark_info: dict = None, attr_info: dict = None,
                 num_landmarks=26, num_attrs=463,
                 target_size=(256, 256), color_mode: str = 'rgb',
                 classes=None, class_mode: str = 'categorical',
                 batch_size: int = 32, shuffle: bool = True, seed=None, data_format=None,
                 follow_links: bool = False):
        super().__init__(directory, image_data_generator, target_size, color_mode, classes, class_mode, batch_size,
                         shuffle, seed, data_format, follow_links)
        self.bounding_boxes = bounding_boxes
        self.landmark_info = landmark_info
        self.attr_info = attr_info
        self.num_landmarks = num_landmarks
        self.num_attrs = num_attrs
        self.num_bbox = 4

    def next(self):
        """
        # Returns
            The next batch.
        """

        batch_x = np.zeros((self.batch_size,) + self.image_shape, dtype=K.floatx())
        locations = np.zeros((len(batch_x),) + (self.num_bbox,), dtype=K.floatx())
        landmarks = np.zeros((len(batch_x),) + (self.num_landmarks,), dtype=K.floatx())
        attributes = np.zeros((len(batch_x),) + (self.num_attrs,), dtype=K.floatx())

        # initialize 2 empty arrays for the input image batch
        pairs = [np.zeros((self.batch_size, self.target_size[0], self.target_size[1], 3)) for _ in range(3)]
        # For dummy purposes!
        targets = np.zeros((self.batch_size,))

        for i in range(self.batch_size):
            # Pick anchor image
            # print("Anchor image")
            idx_1 = rng.randint(0, self.samples)
            pairs[0][i, :, :, :] = self.get_image(idx_1)

            # pick positive and negative samples to anchor image.
            # print("Positive image")
            idx_2 = rng.randint(0, self.samples)
            while self.classes[idx_2] != self.classes[idx_1]:
                idx_2 = rng.randint(0, self.samples)

            pairs[1][i, :, :, :] = self.get_image(idx_2)

            # print("Negative image")
            idx_3 = rng.randint(0, self.samples)
            while self.classes[idx_3] == self.classes[idx_1]:
                idx_3 = rng.randint(0, self.samples)

            pairs[2][i, :, :, :] = self.get_image(idx_3)

            if self.bounding_boxes is not None:
                locations[i] = (self.get_bbox(self.filenames[idx_1]),
                                self.get_bbox(self.filenames[idx_2]),
                                self.get_bbox(self.filenames[idx_3]))

            if self.landmark_info is not None:
                landmarks[i] = (self.get_landmark_info(self.filenames[idx_1]),
                                self.get_landmark_info(self.filenames[idx_2]),
                                self.get_landmark_info(self.filenames[idx_3]))

            if self.attr_info is not None:
                attr_info_lst_1 = self.attr_info[self.filenames[idx_1]]
                attr_info_lst_2 = self.attr_info[self.filenames[idx_2]]
                attr_info_lst_3 = self.attr_info[self.filenames[idx_3]]
                attributes[i] = (np.asarray(attr_info_lst_1), np.asarray(attr_info_lst_2), np.asarray(attr_info_lst_3))

        y = [targets, locations, landmarks, attributes]
        statements = [True, self.bounding_boxes is not None,
                      self.landmark_info is not None, self.attr_info is not None]

        y = np.asarray([x for x, y in zip(y, statements) if y], dtype=K.floatx()).reshape((self.batch_size,))

        if self.shuffle:
            anchor_img = pairs[0]
            positive_img = pairs[1]
            negative_img = pairs[2]
            tmp = list(zip(anchor_img, positive_img, negative_img))
            shuffle(tmp)
            anchor_img, positive_img, negative_img = zip(*tmp)

            pairs[0] = np.asarray(anchor_img)
            pairs[1] = np.asarray(positive_img)
            pairs[2] = np.asarray(negative_img)

        return np.asarray(pairs), np.asarray(y)

    def get_image(self, idx):
        fname = self.filenames[idx]
        # print("Category: " + str(self.classes[idx_2]) + ", Filename: " + str(fname_2) + "\n")
        img = image.load_img(os.path.join(self.directory, fname),
                             grayscale=self.color_mode == 'grayscale',
                             target_size=self.target_size)
        img = image.img_to_array(img, data_format=self.data_format)
        img = self.image_data_generator.random_transform(img)
        img = self.image_data_generator.standardize(img)
        return img

    def get_bbox(self, fname):
        bbox = self.bounding_boxes[fname]
        return np.asarray([bbox['origin']['x'], bbox['origin']['y'], bbox['width'], bbox['height']], dtype=K.floatx())

    def get_landmark_info(self, fname):
        landmark_info = self.landmark_info[fname]
        return np.asarray([landmark_info["clothes_type"], landmark_info["variation_type"],
                           landmark_info['1']['visibility'], landmark_info['1']['x'],
                           landmark_info['1']['y'],
                           landmark_info['2']['visibility'], landmark_info['2']['x'],
                           landmark_info['2']['y'],
                           landmark_info['3']['visibility'], landmark_info['3']['x'],
                           landmark_info['3']['y'],
                           landmark_info['4']['visibility'], landmark_info['4']['x'],
                           landmark_info['4']['y'],
                           landmark_info['5']['visibility'], landmark_info['5']['x'],
                           landmark_info['5']['y'],
                           landmark_info['6']['visibility'], landmark_info['6']['x'],
                           landmark_info['6']['y'],
                           landmark_info['7']['visibility'], landmark_info['7']['x'],
                           landmark_info['7']['y'],
                           landmark_info['8']['visibility'], landmark_info['8']['x'],
                           landmark_info['8']['y']], dtype=K.floatx())

