__author__ = 'victor'
import numpy as np


class Trigger(object):
    """
    A generic Trigger object that performs some action on some event
    """
    pass


class StatefulTriggerMixin(object):
    """
    A mix-in denoting triggers with memory
    """

    def reset(self):
        """
        reset the Trigger to its initial state (eg. by clear its memory)
        """
        raise NotImplementedError()


class EarlyStopping(Trigger):
    """
    Indicates that the training should stop once some condition is reached by some variable.
    Usually the variable is some evaluation metric on the development set.
    """

    def should_stop(self, new_value):
        """
        new_value: value of the variable corresponding to this time step

        returns True iff the early stopping criteria has been met
        """
        raise NotImplementedError()


class ThresholdEarlyStopping(EarlyStopping):
    """
    Triggers early stopping when the variable crosses the min threshold or the max threshold.
    """

    def __init__(self, min_threshold=-float('inf'), max_threshold=float('inf')):
        super(ThresholdEarlyStopping, self).__init__()
        self.min = min_threshold
        self.max = max_threshold

    def should_stop(self, new_value):
        return new_value > self.max or new_value < self.min


class PatienceEarlyStopping(EarlyStopping, StatefulTriggerMixin):
    """
    Triggers early stopping when N time steps has elapsed since the best value
    for the variable was encountered. N is denoted by the patience parameter.
    """

    def __init__(self, patience):
        super(PatienceEarlyStopping, self).__init__()
        self.patience = patience
        self.best_so_far = -float('inf')
        self.time_since_best = 0

    def should_stop(self, new_value):
        if new_value > self.best_so_far:
            self.best_so_far = new_value
            self.time_since_best = 0
            return False
        self.time_since_best += 1
        return self.time_since_best > self.patience

    def reset(self):
        self.best_so_far = -float('inf')
        self.time_since_best = 0


class SlopeThresholdEarlyStopping(EarlyStopping, StatefulTriggerMixin):
    """
    Triggers early stopping when the slope of the value in the most recent time window
    exceeds the min threshold or the max threshold. The width of the window is denoted
    by the time parameter. The slope is approximated via a least squares fit on the
    data points in the window.
    """

    def __init__(self, min_thresh=-float('inf'), max_thresh=float('inf'), time=5):
        super(SlopeThresholdEarlyStopping, self).__init__()
        self.min = min_thresh
        self.max = max_thresh
        self.points_seen = 0
        self.time = time
        self.x = np.array(range(time))
        self.y = np.zeros(time)
        # this is for framing the slope interpolation as least squares regression
        self.A = np.vstack([self.x, np.ones(len(self.x))]).T

    def should_stop(self, new_value):
        # shift time by 1
        self.y[:-1] = self.y[1:]
        self.y[-1] = new_value

        if self.points_seen < self.time-1:
            self.points_seen += 1
            return False # not enough data points to interpolate

        # x is time, y is values. We interpolate the m and c in y = mx + c
        m, c = np.linalg.lstsq(self.A, self.y)[0]
        return m < self.min or m > self.max

    def reset(self):
        self.points_seen = 0
        self.y.fill(0)
