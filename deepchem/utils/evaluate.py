"""
Utility functions to evaluate models on datasets.
"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import numpy as np
import warnings
from deepchem.utils.save import log
import pandas as pd

__author__ = "Bharath Ramsundar"
__copyright__ = "Copyright 2015, Stanford University"
__license__ = "LGPL"

def to_one_hot(y):
  """Transforms label vector into one-hot encoding.

  Turns y into vector of shape [n_samples, 2] (assuming binary labels).

  y: np.ndarray
    A vector of shape [n_samples, 1]
  """
  n_samples = np.shape(y)[0]
  y_hot = np.zeros((n_samples, 2))
  for index, val in enumerate(y):
    if val == 0:
      y_hot[index] = np.array([1, 0])
    elif val == 1:
      y_hot[index] = np.array([0, 1])
  return y_hot

def from_one_hot(y):
  """Transorms label vector from one-hot encoding.

  y: np.ndarray
    A vector of shape [n_samples, num_classes]
  """
  return np.argmax(y, axis=1)

def threshold_predictions(y, threshold):
  y_out = np.zeros_like(y)
  for ind, pred in enumerate(y):
    y_out[ind] = 1 if pred > threshold else 0
  return y_out

class Evaluator(object):
  """Class that evaluates a model on a given dataset."""

  def __init__(self, model, dataset, transformers, verbose=False):
    self.model = model
    self.dataset = dataset
    self.transformers = transformers
    self.task_names = dataset.get_task_names()
    self.task_type = model.get_task_type()
    self.verbose = verbose

  def compute_model_performance(self, metrics, csv_out, stats_file, threshold=None):
    """
    Computes statistics of model on test data and saves results to csv.
    """
    pred_y_df = self.model.predict(self.dataset, self.transformers)

    task_type = self.task_type
    colnames = ["task_name"] + [metric.name for metric in metrics]
    performance_df = pd.DataFrame(columns=colnames)

    for i, task_name in enumerate(self.task_names):
      y = pred_y_df[task_name].values
      y_pred = pred_y_df["%s_pred" % task_name].values
      if threshold is not None:
        # TODO(rbharath): This is a hack. More structured approach?
        y = pred_y_df[task_name+"_raw"].values
        y_pred = threshold_predictions(y_pred, threshold)
      w = pred_y_df["%s_weight" % task_name].values

      if task_type == "classification":
        y, y_pred = y[w.nonzero()].astype(int), y_pred[w.nonzero()].astype(int)
        # Sometimes all samples have zero weight. In this case, continue.
        if not len(y):
          continue

      scores = []
      for metric in metrics:
        scores.append(metric.compute_metric(y, y_pred))
      performance_df.loc[i] = [task_name] + scores

    log("Saving predictions to %s" % csv_out, self.verbose)
    pred_y_df.to_csv(csv_out)
    log("Saving model performance scores to %s" % stats_file, self.verbose)
    performance_df.to_csv(stats_file)

    return pred_y_df, performance_df