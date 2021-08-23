"""
Types and constants.

Note: it is not advisable to change either the IntDType or the FloatDType.

In case of the floats, 64-bit has much higher precision, which may be quite
relevant for geometry: more precision for edge cases, etc.

In case of the integers, Python has surprisingly (ambiguous) behavior. Since
numba requires static types, they've chosen to default to ``np.intp``:

See:

https://numba.pydata.org/numba-doc/latest/proposals/integer-typing.html

This means that setting IntDType to np.int32 on a 64-bit system will break
compilation: within this code, the size of an array (via ``.size``) will have
an integer type of ``np.intp``. If IntDType == np.int32, the BucketDType array
will expect a 32-bit integer for its index and size fields, yet receive a
64-bit integer (intp), and error during type inferencing.
"""
import math
from typing import NamedTuple

import numba as nb
import numba.types as nbtypes
import numpy as np

IntDType = np.intp
FloatDType = np.float64
IntArray = np.ndarray
FloatArray = np.ndarray
BucketArray = np.ndarray
NodeArray = np.ndarray


class Point(NamedTuple):
    x: FloatDType
    y: FloatDType


class Vector(NamedTuple):
    x: FloatDType
    y: FloatDType


class Node(NamedTuple):
    child: IntDType
    Lmax: FloatDType
    Rmin: FloatDType
    ptr: IntDType
    size: IntDType
    dim: bool


class Bucket(NamedTuple):
    Max: FloatDType
    Min: FloatDType
    Rmin: FloatDType
    Lmax: FloatDType
    index: IntDType
    size: IntDType


class CellTreeData(NamedTuple):
    faces: IntArray
    vertices: FloatArray
    nodes: NodeArray
    bb_indices: IntArray
    cells_per_leaf: int


NodeDType = np.dtype(
    [
        # Index of left child. Right child is child + 1.
        ("child", IntDType),
        # Range of the bounding boxes inside of the node.
        ("Lmax", FloatDType),
        ("Rmin", FloatDType),
        # Index into the bounding box index array, bb_indices.
        ("ptr", IntDType),
        # Number of bounding boxes in this node.
        ("size", IntDType),
        # False = 0 = x, True = 1 = y.
        ("dim", bool),
    ]
)


BucketDType = np.dtype(
    [
        # Range of the bucket.
        ("Max", FloatDType),
        ("Min", FloatDType),
        # Range of the bounding boxes inside the bucket.
        ("Rmin", FloatDType),
        ("Lmax", FloatDType),
        # Index into the bounding box index array, bb_indices.
        ("index", IntDType),
        # Number of bounding boxes in this bucket.
        ("size", IntDType),
    ]
)

PARALLEL = True
# 2D is still rather hard-baked in, so changing this alone to 3 will NOT
# suffice to generalize it to a 3D CellTree.
NDIM = 2
FILL_VALUE = -1
# Recursion in numba is somewhat slow (in case of querying), or unsupported for
# AOT-compilation when creating. We can avoid recursing by manually maintaining
# a stack, and pushing and popping. To estimate worst case, let's assume every
# leaf (node) of the tree contains only a single cell. Then the number of cells
# that can be included is given by 2 ** (depth of stack - 1).
MAX_N_FACE = 2e9  # 2e9 results in a depth of 32
MAX_TREE_DEPTH = int(math.ceil(math.log(MAX_N_FACE, 2))) + 1

# Derived types & constants
NumbaFloatDType = nb.from_dtype(FloatDType)
NumbaIntDType = nb.from_dtype(IntDType)
NumbaNodeDType = nb.from_dtype(NodeDType)
NumbaBucketDType = nb.from_dtype(BucketDType)

NumbaCellTreeData = nbtypes.NamedTuple(
    (
        NumbaIntDType[:, :],  # faces
        NumbaFloatDType[:, :],  # vertices
        NumbaNodeDType[:],  # nodes
        NumbaIntDType[:],  # bb_indices
        NumbaIntDType,  # cells_per_leaf
    ),
    CellTreeData,
)

FLOAT_MIN = np.finfo(FloatDType).min
FLOAT_MAX = np.finfo(FloatDType).max
INT_MAX = np.iinfo(IntDType).max