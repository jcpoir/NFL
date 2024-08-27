## skewed_voigt.py
# @author jcpoir
# Defines a fittable skewed voigt model class, with some modifications/simplifications,
# that will be used in some form for all play smoothing. This model inherits from the pytorch
# neural net framework.

import torch
import torch.optim as optim
from torch.nn import Parameter
import torch.nn as nn
from numpy import (real)
from torch.special import erf
from random import uniform
import matplotlib.pyplot as plt
import math
from tqdm import tqdm
import numpy as np
import warnings
warnings.filterwarnings("ignore")

from smoothing_tools import *

# (1) Support Functions

def get_dist_mean(x,y):
  ''' gets the expected value of a distribution with values "x" and freqs "y" '''

  if torch.is_tensor(x) and torch.is_tensor(y):
    return torch.matmul(x,y)
  
  else: return np.matmul(x,y)

def load_x():
    x = np.linspace(-20,100,121)
    x = torch.tensor(x, requires_grad = True)
    return x
x = load_x()

mse_fn = nn.MSELoss()
def MSE_Mean_Loss(y1, y2, ratio = 10):
  global x

  mse = mse_fn(y1, y2)
  m1, m2 = get_dist_mean(x, y1), get_dist_mean(x, y2)
  means = abs(m1 - m2) * ratio

  return mse + means

# (2) Class Definitions

class SkewedVoigt(nn.Module):
  ''' A PyTorch-based pseudo-skewed voigt distribution whose probability mass is capped at one '''

  def __init__(self):
    super(SkewedVoigt, self).__init__()

    amp, cen, sig, gam, skew = 1.0, uniform(5,6), uniform(1,2), uniform(1,2), uniform(0.5, 0.9)

    # Establish the skewev voigt components as model parameters
    self.amp = Parameter(torch.tensor([amp]))
    self.cen = Parameter(torch.tensor([cen]))
    self.sig = Parameter(torch.tensor([sig]))
    self.gam = Parameter(torch.tensor([gam]))
    self.skew = Parameter(torch.tensor([skew]))

    # print(f"amp: {amp}, cen: {cen}, sig: {sig}, gam: {gam}, skew: {skew}")

    self.tiny = 1.0e-15

  def get_params(self):
    return self.amp, self.cen, self.sig, self.gam, self.skew

  def forward(self, x):
    ''' computes a skewed voigt result based on the optimizing parameters above '''

    def nonzero(num): return max(num, self.tiny)

    # i. Voigt
    z = (x - self.cen + 1j * self.gam) / nonzero(self.sig)
    wofz_result = torch.exp(-z) * (1- erf(real(-z)))
    wofz_result = real(wofz_result)
    voigt_result = self.amp * wofz_result / nonzero(self.sig * (math.pi*2) ** 2)

    # ii. Skewed Voigt
    beta = self.skew / nonzero(self.sig * math.log(2))
    asym = 1 + erf(beta * (x - self.cen))
    out = asym * voigt_result

    # iii. Ensure Output of Prob Mass = 1
    out = out / torch.sum(out)

    return out

## Main Class
## Main Class
class SkewedVoigtModel(SkewedVoigt):
    ''' A fittable SkewedVoigt '''

    def __init__(self):
        super(SkewedVoigtModel, self).__init__()
        self.optimizer = optim.Adam(self.parameters(), lr = 0.1)
        self.loss = torch.tensor(0)

    def fit_transform(self, x, y, loss_fn, n_epochs=1000, conv_thresh=1e-8, mean_conv=None, isKickoff=False, isSack=False, show_plots=False, verbose=False):

        # Hopefully fix the new tensor bug . . .
        x, y = torch.tensor(x[:]), torch.tensor(y[:])

        model, optimizer = self, self.optimizer

        model.train()

        # Special graph arrays are maintained for the verbose case . . . no need to maintain them otherwise
        y_graph, x_graph = y.clone().detach(), x.clone().detach()
        y_graph.requires_grad = False

        loss, mse, means = 0, 0, 0

        if verbose:
            weights = {}
            par_names = ["amp", "cen", "sig", "gam", "skew"]
            for par in par_names:
                weights[par] = []
            X = []

        pbar = range(n_epochs)
        if verbose: pbar = tqdm(range(n_epochs))
        for epoch in pbar:
            if verbose: pbar.set_description(f"epoch = {epoch}, loss = {loss}")

            optimizer.zero_grad()

            y_pred = model(x)
            if isKickoff:
              y_pred[-35:] = torch.zeros(35) # For kickoffs, we don't want to predict non-touchbacks that go in the endzone
            elif isSack: y_pred[-100:] = torch.zeros(100)
            y_pred = y_pred / torch.sum(y_pred)
            
            y_p_graph = y_pred.clone().detach() # update graph arrays

            ## Compute loss & backpropogate
            last = loss
            loss = loss_fn(y, y_pred)
            self.loss = loss # for tracking

            is_divergent = torch.isnan(model.loss)
            if is_divergent: return y_p_graph

            # if loss > last: break
            if abs(last - loss) < conv_thresh: break

            # Adding a convergence condition for stage 2 in which we break when the means are close enough
            if mean_conv != None:
                m1, m2 = get_dist_mean(x_graph, y_graph), get_dist_mean(x_graph, y_p_graph)
                if abs(m1 - m2) <= mean_conv: break

            if verbose: X.append(epoch)

            loss.backward()
            optimizer.step()

            if verbose:
                def update_weights(weights, model):

                    pars = model.get_params()
                    for par, val in zip(par_names, pars):
                        weights[par].append(val.clone().detach())

                    return weights

                weights = update_weights(weights, model)

        if show_plots:

            ## (1) Parameter Graph

            plt.title("Skewed Voigt Parameter Optimization")
            for par_name in par_names: plt.plot(X, weights[par_name])
            plt.legend(par_names)
            plt.xlabel("Epoch")
            plt.ylabel("Value")
            plt.show()

            ## (2) Distributions

            plt.title("Final Distribution Fit")
            plt.plot(x_graph, y_p_graph)
            plt.plot(x_graph, y_graph)
            plt.legend(["Predicted", "Actual"])
            plt.xlabel("Yards")
            plt.ylabel("freq")
            plt.show()

            mean_actual, mean_pred = get_dist_mean(x_graph, y_graph), get_dist_mean(x_graph, y_p_graph)
            print(f"Actual Mean: {mean_actual}, Predicted Mean: {mean_pred}")

        return y_p_graph.numpy()

    def smooth_normalize(self, x, y, verbose = True, show_plots = False, isKickoff = False, isSack = False):
        ''' Perform a two-phase contrained optimization. In the first phase, use MSE to optimize for shape.
        Then, freeze the skew and optimize on MSE and difference of means using sigma and center '''

        conv_thresh, mean_conv = 1e-8, None  # Stage one: shape fit
        self.amp.requires_grad = False

        ## For certain playtypes, shape is prioritized over similarity of mean values
        loss_fns = [nn.MSELoss()]
        if not isSack and not isKickoff: loss_fns.append(MSE_Mean_Loss) # For most, however, we NEED the means to be as close as possible for simulations to be accurate!

        for loss_fn in loss_fns:
            out = self.fit_transform(x, y, loss_fn, conv_thresh=conv_thresh, mean_conv=mean_conv, verbose=verbose, show_plots = show_plots, isKickoff=isKickoff, isSack=isSack)
            if isKickoff or isSack: self.skew.requires_grad = False
            conv_thresh, mean_conv = 1e-6, 0.01  # Stage two: mean fit
            self.optimizer.lr = 0.01
        self.optimizer.lr, self.skew.requires_grad = 0.1, True

        return out
    
def smooth_normalize(x, y, isKickoff = False, isSack = False, show_plots = False, verbose = True, n_retries = 10):
    ''' We're getting some messy fits with smooth normalize (seeing divergence at points, especially in special
    teams dists). Working on that, but in the meantime this function will serve as a buffer by abstracting the
    instantiation and retrying the fit a predefined number of times '''

    y = y / np.sum(y)
    lr = 0.1

    for i in range(n_retries):
              
        model = SkewedVoigtModel()
        model.optimizer.lr = lr

        if i == n_retries - 1: model.optimizer.lr = 0

        x_t,y_t = get_tensors(x, y)
        out = model.smooth_normalize(x_t,y_t, isKickoff=isKickoff, isSack=isSack, verbose=verbose, show_plots=show_plots)
        
        is_divergent = torch.isnan(model.loss) or np.isnan(y[0])
        if not is_divergent: break

        lr = lr / 2

    return out