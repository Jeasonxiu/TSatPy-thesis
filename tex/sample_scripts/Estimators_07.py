import sys
from TSatPy import Estimator, State, StateOperator
from TSatPy.Clock import Metronome
import numpy as np
import matplotlib.pyplot as plt
import time
import random
import json
from GradientDescent import GradientDescent

print('Sliding Mode Observer')

run_time = 120
speed = 20
dts = [0.8, 1.2]
c = Metronome()
c.set_speed(speed)

def grid_me(ax):
    ax.grid(color='0.75', linestyle='--', linewidth=1)

def run_test(Lq, Lw, Kq, Kw, Sq, Sw, plot=False):
    ts, q_tracking, w_tracking = test(Lq, Lw, Kq, Kw, Sq, Sw)

    if plot:
        fig = plt.figure(dpi=80, facecolor='w', edgecolor='k')
        ax1 = fig.add_subplot(4,1,1)
        plt.title('Quaternion Angle')
        ax1.scatter(ts, q_tracking['measured'], c='b', label='measured')
        ax1.scatter(ts, q_tracking['estimated'], c='r', label='estimated')
        grid_me(ax1)
        ax1.set_ylabel(r'$\theta$ (rad)')
        plt.legend()

        ax = fig.add_subplot(4,1,2,sharex=ax1)
        plt.title('Quaternion Angle Error')
        ax.scatter(ts, q_tracking['err'], c='g', label=r'$\theta_{e}$')
        grid_me(ax)
        ax.set_ylabel(r'$\theta_{e}$ (rad)')

        ax = fig.add_subplot(4,1,3,sharex=ax1)
        plt.title('Body Rate $\omega_z$')
        ax.scatter(ts, w_tracking['measured'], c='b', label='measured')
        ax.scatter(ts, w_tracking['estimated'], c='r', label='estimated')
        grid_me(ax)
        ax.set_ylabel(r'$\omega_z$ (rad/s)')
        plt.legend()

        ax = fig.add_subplot(4,1,4,sharex=ax1)
        plt.title('Body Rate Error $\omega_{ze}$')
        ax.scatter(ts, w_tracking['err'], c='g', label=r'$\omega_{ze}$')
        grid_me(ax)
        ax.set_ylabel(r'$\omega_{ze}$ (rad/s)')
        ax.set_xlabel('$t(k)$ seconds')

        plt.tight_layout()
        plt.show()

    return ts, q_tracking, w_tracking


def test(Lq, Lw, Kq, Kw, Sq, Sw):

    x_ic = State.State(
        State.Quaternion([0,0,1], radians=4),
        State.BodyRate([0,0,0.314]))

    I = [[2, 0, 0], [0, 2, 0], [0, 0, 2]]
    plant = State.Plant(I, x_ic, c)
    plant_est = State.Plant(I, State.State(), c)

    L = StateOperator.StateGain(
        StateOperator.QuaternionGain(Lq),
        StateOperator.BodyRateGain(np.eye(3) * Lw))
    K = StateOperator.StateGain(
        StateOperator.QuaternionGain(Kq),
        StateOperator.BodyRateGain(np.eye(3) * Kw))

    Sx = StateOperator.StateSaturation(
        StateOperator.QuaternionSaturation(Sq),
        StateOperator.BodyRateSaturation(Sw))

    smo = Estimator.SMO(c, plant=plant_est)
    smo.set_S(Sx)
    smo.set_L(L)
    smo.set_K(K)

    ts = []
    q_tracking = {
        'measured': [],
        'estimated': [],
        'err': [],
    }
    w_tracking = {
        'measured': [],
        'estimated': [],
        'err': [],
    }
    start_time = c.tick()
    end_time = c.tick() + run_time
    while c.tick() < end_time:
        plant.propagate()

        offset = np.random.randn() * 20 / 180.0 * np.pi
        q_noise = State.Quaternion([0,0,1], radians=offset) * plant.x.q

        x_m = State.State(q_noise, plant.x.w)
        smo.update(x_m)

        ts.append(c.tick() - start_time)

        e, r = plant.x.q.to_rotation()
        q_tracking['measured'].append(r)
        e, r = smo.x_hat.q.to_rotation()
        q_tracking['estimated'].append(r)

        q_e = State.QuaternionError(smo.x_hat.q, plant.x.q)
        e, r = q_e.to_rotation()
        q_tracking['err'].append(r)

        w_tracking['measured'].append(x_m.w.w[2,0])
        w_tracking['estimated'].append(smo.x_hat.w.w[2,0])
        w_tracking['err'].append(smo.x_hat.w.w[2,0] - x_m.w.w[2,0])

        random.shuffle(dts)
        time.sleep(dts[0] / float(speed))

    return [ts, q_tracking, w_tracking]


def calc_err(ts, q_tracking, w_tracking):
    err = np.array(q_tracking['err'])
    cost = np.abs(err).mean() * err.std()
    return cost


def main():
    domains = [
        ['Lq', 0, 1],
        ['Lw', 0, 1],
        ['Kq', 0, 1],
        ['Kw', 0, 1],
        ['Sq', 0, 1],
        ['Sw', 0, 1],
    ]

    kwargs = {
        # Number of iterations to run
        'N': 200,

        # Definition of parameter search domain
        'domains': domains,

        # Function that will run a test
        'run_test': test,

        # Function that will take the return of run_test and determine
        # how well the parameters worked.
        'calc_cost': calc_err,
    }
    print(GradientDescent.descend(**kwargs))
    return 0

if __name__ == "__main__":

    kwargs = None
    kwargs = {
        'Lq': 0.282, 'Lw': 0.444,
        'Kq': 0.307, 'Kw': 0.464,
        'Sq': 0.886, 'Sw': 0.569,
    }

    if kwargs is not None:
        kwargs['plot'] = True
        ts, q_tracking, w_tracking = run_test(**kwargs)
    else:
        exit(main())

