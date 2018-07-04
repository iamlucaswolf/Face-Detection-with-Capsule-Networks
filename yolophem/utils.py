import tensorflow as tf
import numpy as np

def center(boxes, name=None):
    with tf.variable_scope(name, default_name='center'):
        coords, extents = tf.split(boxes, 2, axis=-1)

        centers = coords + extents // 2

        boxes_centered = tf.concat(
            [centers, extents], 
            axis=-1, 
            name='boxes_centered'
        )

    return boxes_centered


def uncenter(boxes, name=None):
    with tf.variable_scope(name, default_name='uncenter'):
        centers, extents = tf.split(boxes, 2, axis=-1)

        starts = centers - extents // 2

        boxes_uncentered = tf.concat(
            [starts, extents],
            axis=-1,
            name='boxes_uncenterd'
        )

    return boxes_uncentered


# Assumes boxes to be centered!
# For now, assumes square images and square grid cells
def localize(boxes, image_extent, grid_resolution, name=None):
    with tf.variable_scope(name, default_name='localize'):
        centers, extents = tf.split(boxes, 2, axis=-1)

        # Compute the extent of one grid cell. Note that rounding up may lead
        # to the last cell(s) being smaller than the rest
        cell_extent = np.ceil(image_extent / grid_resolution)
        
        # Compute the cell indices of each box
        cell_idx = tf.floor_div(centers, cell_extent, name='cell_idx')

        # Localize box centers relative to their containig cells and box extents
        # relative to the entire image
        centers_localized = tf.divide(
            tf.cast(centers - (cell_idx * cell_extent), dtype=tf.float32),
            tf.cast(cell_extent, dtype=tf.float32),
            name='centers_localized'
        )

        extents_localized = tf.divide(
            tf.cast(extents, dtype=tf.float32), 
            tf.cast(image_extent, dtype=tf.float32), 
            name='extents_localized'
        )

        boxes_localized = tf.concat(
            [centers_localized, extents_localized], 
            axis=-1, 
            name='boxes_localized'
        )

    return boxes_localized, cell_idx


# Assumes centered boxes
def intersection_over_union(boxes_a, boxes_b, epsilon=1e-7, name=None):
    with tf.variable_scope(name, default_name='IoU'):

        start_a, extent_a = tf.split(uncenter(boxes_a), 2, axis=-1)
        start_b, extent_b = tf.split(uncenter(boxes_b), 2, axis=-1)

        # Prevent negative box areas
        extent_a = tf.maximum(extent_a, 0, name='extent_a')
        extent_b = tf.maximum(extent_b, 0, name='extent_b')

        end_a = start_a + extent_a
        end_b = start_b + extent_b

        # Calculate intersection points
        start_cut = tf.maximum(start_a, start_b, name='start_cut')
        end_cut = tf.minimum(end_a, end_b, name='end_cut')

        # Calculate area of intersection
        extent_cut = tf.maximum(end_cut - start_cut, 0, name='extent_cut')
        area_cut = tf.reduce_prod(extent_cut, axis=-1, name='area_cut')

        # Calculate area if union
        area_a = tf.reduce_prod(extent_a, axis=-1, name='area_a')
        area_b = tf.reduce_prod(extent_b, axis=-1, name='area_b')

        area_union = area_a + area_b - area_cut

        iou = tf.divide(
            tf.cast(area_cut, dtype=tf.float32),
            tf.cast(area_union, dtype=tf.float32) + epsilon,
            name='iou'
        )

    return iou

