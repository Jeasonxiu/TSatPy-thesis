## TSatPy

This module is designed to run a variety of observer based controls
with a rotating rigid body.

Notable characteristics of this implementation of a rotating body's
attitude observer based controller are:

**Adaptive Step Algorithms**

All time dependent calculations vary their parameters at run-time dependent
on the time since the last time it ran.  For example, calculations based on
integrals or derivatives reference the system clock to scale the results
based on what the clock reports is the current time step.

**Variable System Clock**

The system clock is the official time keeper for the entire ADCS.  Advantages
to using a central clock instead of the computer time is that the speed
of elapsed time can be modified at run-time during simulations to either
compress the time to complete the simulation or slow down the simulation to
inspect a certain event.

**Quaternion Multiplicative Corrections**

Quaternions that quantify a system's position contain 4 values that are
commonly tracked and controlled separately.  This produces a lot of errors
since the 4 values are co-dependent and altering one modifies the rest as
well.  Breaking the values apart also creates a disconnect between the values
and the physical position they help define.  Use of the quaternion
multiplicative correction technique maintains the integrity of the values
and their relation to the physical position of the system.  Usages of
quaternions in most estimators and controllers require normalization of
the state to a unit vector after each calculation.  In this implementation,
the only time normalization that should ever be required is to correct
for floating point error accumulation.

**Quaternion Scaling**

Unlike body rates that can be linearly scaled, the 4 quaternion values are a
sinusoidal value where multiple values can represent the same attitude
(i.e. 0, 360 degrees).  The common method of scaling by the raw values can
have unexpected results.  Due to the trig of small angle interacting with
quaternions that represent small deviations in this manner introduces a
little error, but the linear assumption creates larger errors as the angle
increases.  All quaternion scaling in this library is performed or the angle
that the quaternion represents.  With this method, we can maintain the
linear scaling affect that is desired while maintaining the integrity
of the quaternion representation.

**Run-time interface**

Through the use of a python twisted daemon process an restful API interface
is available to query the state of the system in the middle of a run.
This creates the ability to display meaningful representations of the
system and increase insight into the system's dynamic behavior instead of
relying on batch post processing.

[Sample video](http://vimeo.com/42960673)

**Concurrent Estimation/Control Algorithms**

When running a comparative analysis between different types of estimators
or different types of controllers, common methods are to re-run simulations
for each variation and compare the results.  The library allows for
configurations such as providing the same measurement values to both a PID
and SMO estimator to compare their performance.

**Quaternion Decomposition**

With spin stabilized satellites the only part of the attitude quaternion
that requires control is the one that quantifies the "wobble".  Since the 4
values are co-dependent as mentioned above just modifying 2 of the values
results in a corrupted position representation.

**Modular Design**

This library is designed to have interchangeable components with predefined
and consistent interfaces and roles by allowing for the inclusion of
additional estimation and control techniques.  In the case of estimation,
an Extended Kalman Filter (EKF) class can be added by creating a new class
in Estimator.py that has contains the common properties (`x_hat`, `last_err`..)
and common methods (`x_hat = update(x)`).

**Portable Design**

The portable design dictates that with the defined interfaces between modules,
the observer based control methods have no knowledge of what is producing
the sensor readings and what is accepting moment commands.  This enforces
consistency in the behavior of the system whether it's hooked up to an
in-memory model of a satellite, TableSat IA, or any future spin spin
stabilized platform.  The only code change that may be required (Sensor.py and
Actuator.py) is in applying the system to a new platform that contains
new types of sensors and actuators.

**Python**

Since control systems professionals regularly work in a Numerical Simulation
Software environment (like MATLAB Simulink or Octave) and when it comes to
implementation the logic is generally converted to a more standard language
by software engineers there becomes a disconnect between the planning and
implementation of a controller.  By using a language like python, the code
can be written in an expressive manner so that a control systems
professional only needs a little programming experience to modify the code.
It also keeps the controller in a language than could be reviewed for
optimization by a software engineer and applied to the actual system
without requiring a conversion to an entirely different system or language.

## Modules

Below is an outline of the separate modules contained in the TSatPy
library and their associated roles.

### Actuators

This module defines the output of the controller.  The actuator instance
on initialization, is supplied with the physical arrangement of the actuators
and when activated, what moments they are able to produce.  During run-time
the actuators follow the following logic:

* Accept a R^3 moment from the controller
* Determine the actual moment that is possible from the physical arrangement
* Convert the desired moments to voltage settings
* Submit the actuator voltage settings to
    * the Comm for transmission to the experimental setup _or_
    * the plant for theoretical simulations
* Report the actual applied moments back to the estimator for state propagation

input: Moment desired
output: Voltages and actual moment delivered

### ADCS

This module is the parent container for all the observer based controls,
and comm instances.  The instance of the ADCS should accept a json config
that can be easily stored and define the setup of the model including type
and number of estimators.

* input: config json
* output: ADCS model

### Clock

This module governs the system clock of the ADCS system and should be
referenced by any logic in the observer or controller that is time dependent
such as calculations reliant on integrals or derivatives of parameters.
The metronome class by default track seconds since the initialization of the
clock, but when running simulations can have it's speed dynamically altered
to either run faster for long term simulations or run slower to get better
inspection of an event.

* input: None
* output: elapsed time

### Comm

This module handles the interface between the the control system and either
the physical system or the theoretical model.  With the physical system, a
UDP socket is opened and either listens for packets transmitted from the
sensors or submits voltage packets to set actuator voltages.  When running
in simulations, the module submits and receives the voltage messages to
an in-memory model of the system that contains the system dynamics and can
return mocked sensor voltages based on the behavior.

**From Controller to Satellite**

* input: Voltage setting determined by the actuator
* output: UDP packet to the system or in-memory model

**From Satellite to Controller**

* input: Sensor voltages from the system or in-memory model
* output: Sensor data to submit to sensor class for conversion to a state

### Controller

This module contains the algorithms that take what we have estimated the
system to be doing, compare it to what we want it to do, and determine
what moments need to be applied to make the system behave as desired.

The master control instance governs the interface between the incoming
estimator state and the outgoing actuator moments.  The master controller
can run multiple control algorithms simultaneously which can be individually
tuned to different types of system behaviors like one that can handle
large errors and one for the soft corrections at steady state.

* input: configuration of what types of control algorithms should be used and the parameters required to set them up
* output: a desired moment based on the active control algorithm's calculations

### Estimator

This module contains the algorithm that take the measured state from the
sensor model which jumps around a lot because of the noise in the originating
signal and attempts to eliminate the noise and create an accurate representation
of the true state of the system.

* input: measured state (x)
* output: estimated true state (x_hat)

### Sensor

This module receives raw voltage measurements from either a simulated
truth model of the system or from the Comm module polling sensor voltage
data off the experimental system.

Each class represents a different sensor type (course sun sensor,
magnetometer, gyroscope, ...) and contain the logic to convert sensor
readings from that sensor into a state representation x with quaternion
and body rates.

* input: voltages (V)
* output: measured state (x)

### Service

Based off a twisted daemon.  This module contains the logic setting up the
daemon and establishing the socket interfaces with the physical model.

* input: run configuration
* output: twisted daemon config

### StateOperator

This module contains classes that are designed to modify instances from the
State module or convert between them.  For example a quaternion can represent
the difference between two attitudes.  In an estimator or controller we
don't want to always just jump all the way to the new state because of noise
in the readings.  With a QuaternionGain we can scale back the difference and
adjust our attitude based on a fraction of the difference which over time will
reduce the overall error between the states.  In the case of the controller,
the state instance needs to be converted to a Moment by a StateToMoment class.

| Class | What it does |
|-------|--------------|
| BodyRateGain | Scale a BodyRate instance |
| QuaternionGain | Scale a Quaternion instance |
| StateGain | Scale the State instance (Wrapper for QuaternionGain, BodyRateGain) |
| QuaternionSaturation | Saturate a Quaternion |
| BodyRateSaturation | Saturate a BodyRate |
| StateSaturation | Saturate a State (Wrapper for QuaternionSaturation, BodyRateSaturation) |
| BodyRateToMoment | Convert a BodyRate to a Moment |
| QuaternionToMoment | Convert a Quaternion to a Moment |
| StateToMoment | Convert a State to a Moment (Wrapper for QuaternionToMoment, BodyRateToMoment) |


* input: An instance from the State module
* output: A modified instance or the conversion to a new State instance

### State

This module contains classes that are used to quantify the state of the system.

| State | Class |
|-------|-------|
| Attitude | Quaternion |
| Spin rates | BodyRate |
| Difference in attitudes | QuaternionError |
| How body rates change the attitude | QuaternionDynamics |
| How moments change the body rates | EulerMomentEquations |
| Position and velocity | State - Couples the position (Quaternion) with velocity (BodyRate) |
| Differences in position and velocity | StateError |
| In-memory model of the satellite | Plant |
| Applied torques | Moment |
