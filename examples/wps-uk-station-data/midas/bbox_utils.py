#!/usr/bin/env python

"""
bbox_utils.py
=============

A set of utilities for bounding box lookups.

"""

import os
import sys
import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def isInRange(i, start, end):
    "Returns a boolean. True if i is inside (or equal to either) start -> end."
    if i >= start and i <= end:
        return True

    return False


def isInBBox(lat, lon, n, w, s, e):
    """
    Returns a boolean. True if (lat, lon) point is in bounding box (n, w, s, e).

    It handles the various longitude bounding box cases:

     (1) x1 is +ve, x2 is -ve : raises an Exception
     (2) x1 is -ve, x2 is -ve
     (3) x1 is -ve, x2 is +ve
     (4) x1 is +ve, x2 is +ve

    """
    # Check order of s-to-n and w-to-e are correct
    if s > n:
        raise ValueError(
            "South cannot be greater than north in bounding box specification: south = %s; north = %s" % (s, n))

    if w > e:
        # This also handles case (1) above
        raise ValueError(
            "West cannot be greater than east in bounding box specification: west = %s; east = %s" % (w, e))

    # Check ranges are valid
    allowed_ranges = [("North", n, -90, 90),
                      ("South", s, -90, 90),
                      ("West", w, -360, 360),
                      ("East", e, -360, 360)]

    for (name, v, start, end) in allowed_ranges:
        if not isInRange(v, start, end):
            raise ValueError(
                "%s cannot be out of range %s - %s but is: %s" % (name, start, end, v))

    # Check lat is in south-north range
    if not isInRange(lat, s, n):
        return False

    # Now check case (2)
    if w < 0 and e < 0:
        if lon > 0:
            lon -= 360

        return isInRange(lon, w, e)

    # Now check case (4)
    elif w >= 0 and e >= 0:
        if lon < 0:
            lon += 360

        return isInRange(lon, w, e)

    # Now check case (3): which we do by checking two ranges as follows:
    #   (w --> 0)   and   (0 --> e)
    # This is done because this case crosses the Greenwich Meridian
    else:
        lon_check1 = lon
        lon_check2 = lon

        if lon >= 0:
            lon_check1 -= 360
        if lon < 0:
            lon_check2 += 360

        if isInRange(lon_check1, w, 0) or isInRange(lon_check2, 0, e):
            return True
        else:
            return False


if __name__ == "__main__":

    lons = (-270, -170, -5, 5, 150, 350)
    bboxes = [(50, -200, 20, -150),
              (-30, -10, -60, 15),
              (-30, 45, -80, 160)]

    for lat in range(-90, 91, 45):
        for lon in lons:
            for bbox in bboxes:
                print "Testing:", lat, lon, "in:", bbox, ":", isInBBox(
                    lat, lon, bbox[0], bbox[1], bbox[2], bbox[3])
