#!/usr/bin/env python

# fenugrec 2026, gplv3
# for hp3478a
# This script implements the Performance Tests described in SM section 4-21, p.35

# **** usage:
# - copy/edit .conf file for connection settings and cal resistor values
# - copy/customize cal_dummy.py as required for calibrator used

# **** code structure
# - main() near the end initializes stuff
# - general config is held in external pv.conf to ideally avoid having to edit this script at all

# TODO :

import pyvisa
import argparse
from dataclasses import dataclass
import datetime as dt
import logging
import sys
from time import sleep
from calsource_dummy import *
from hp3478_common import *
from magiconfig import magiconfig

#func to format each measurement result
def print_result_header():
    print(f'\n{'range':10}\t{'target':10}\t{'reading':10}\t{'delta':20}\t{'tol':10}\t{'pass':10}')

def print_result(range, tgt, rdg, delta, tol):
    if tgt:
        delta_ppm = (delta / tgt) * 1e6
    else:
        # avoid div0
        delta_ppm = delta * 1e6
    if abs(delta) > tol:
        result = '* FAIL *'
    else:
        result = 'OK'
    print(f'{range:8g}\t{tgt:10.7g}\t{rdg:10.7g}\t'
        + f'{delta:10.7g} ({delta_ppm:.4g} ppm)\t{tol:10.7g}\t{result}')

######## verification points

@dataclass
class pvstep():
    range: float
    target: float #value of 0 to indicate 'short'
    tol: float # such that 'acceptable range = [(target - tol) ... (target + tol)]
    freq: float = 0 # for AC ranges
    extra_mode: str = None  # optional config like AZ off, 3/4/5 digit etc
    config_dwell: str = None   #if set, will query .conf for given string and use its value. Only for I stuff

class limits_1y():
    #dcv_limits : SM 4-27, parag a-w (step 1-25)
    dcv_limits = [
            pvstep(30e-3, 0, 4e-6),
            pvstep(0.3, 0, 5e-6),
            pvstep(3, 0, 20e-6),
            pvstep(30, 0, 40e-6),
            pvstep(300, 0, 2e-3),
            pvstep(30e-3, 30e-3, 14.5e-6),
            pvstep(0.3, 0.3, 26e-6),
            pvstep(3, 0.3, 40e-6),
            pvstep(3, 1, 80e-6),
            pvstep(3, -1, 80e-6),
            pvstep(3, -3, 200e-6),
            pvstep(3, 3, 230e-6),
            pvstep(3, 3, 200e-6, extra_mode='Z0'), #AZ off
            pvstep(3, 3, 200e-6, extra_mode='N4'), #4dig
            pvstep(3, 3, 200e-6, extra_mode='N3'), #3dig
            pvstep(30, 3, 600e-6),
            pvstep(30, 10, 1.1e-3),
            pvstep(30, 30, 2.5e-3),
            pvstep(30, 30, 3.6e-3, extra_mode='Z0'),
            pvstep(300, 300, 23e-3),
            ]
    #parag y, step 26 : DC CMRR, no need for data
    #SM 4-32, DCI, parag a-j
    dci_limits = [
            pvstep(0.3, 0, 40e-6),
            pvstep(3, 0, 60e-6),
            pvstep(0.3, 0.1, 190e-6),
            pvstep(3, 1, 1.76e-3),
            ]
    #SM 4-37, ACV, pdf p.39
    acv_limits = [
            pvstep(0.3, 28e-3, 176e-6, freq=20e3),
            pvstep(0.3, 280e-3, 680e-6, freq=20e3),
            pvstep(3, 280e-3, 1.26e-3, freq=20e3),
            pvstep(3, 1.5, 3.7e-3, freq=20e3),
            pvstep(3, 2.8, 6.3e-3, freq=20e3),
            pvstep(30, 2.8, 12.6e-3, freq=20e3),
            pvstep(30, 28, 63e-3, freq=20e3),
            pvstep(300, 28, 137e-3, freq=20e3),
            pvstep(300, 280, 742e-3, freq=20e3),
            pvstep(0.3, 280e-3, 1.269e-3, freq=50e3),
            pvstep(30, 28, 86.8e-3, freq=50e3),
            pvstep(300, 280, 1.316, freq=50e3),
            pvstep(0.3, 0.28, 4.2e-3, freq=100e3),
            pvstep(3, 0.28, 10.24e-3, freq=100e3),
            pvstep(3, 2.8, 32.16e-3, freq=100e3),
            pvstep(30, 15, 208.5e-3, freq=100e3),
            pvstep(30, 28, 321.6e-3, freq=100e3),
            pvstep(300, 280, 3.524, freq=100e3),
            pvstep(30, 25.5, 3.397, freq=300e3), #weird numbers in SM, asymetric around 25, unless they meant 25.5
            pvstep(3, 2.8, 13.91e-3, freq=50),
            pvstep(3, 2.8, 32.94e-3, freq=20),
            ]
    # SM 4-38 ACI p.40
    aci_limits = [
            pvstep(0.3, 30e-3, 379e-6, freq=5e3),
            pvstep(0.3, 100e-3, 883e-6, freq=5e3),
            pvstep(1, 1, 15.83e-3, freq=5e3),
            ]
    # SM 4-47, R, p.41
    r_limits = [
            pvstep(30, 0, 4.1e-3),
            pvstep(300, 0, 5e-3),
            pvstep(3e3, 0, 20e-3),
            pvstep(30e3, 0, 200e-3),
            pvstep(300e3, 0, 2),
            pvstep(3e6, 0, 20),
            pvstep(30e6, 0, 200),
            # the following can be done with 1/3scale values instead i.e. 10, 100, 1000...
            pvstep(30, 30, 14.3e-3),
            pvstep(300, 300, 56e-3),
            pvstep(3e3, 3e3, 500e-3),
            pvstep(30e3, 30e3, 5),
            pvstep(300e3, 300e3, 50),
            pvstep(3e6, 3e6, 500),
            pvstep(30e6, 30e6, 23.6e3),
            ]

def step2(dmm, cal, limits, point=None):
    print('\n******** STEP 2 DCV ********')
    print('\n******** CAUTION up to 300V on terminals ! ********')
    input("-------- press Enter when ready ---------")
    logf.debug('\n STEP 2')
    cal.disable()
    cal.mode_dcv()
    cal.set_v(0)
    print_result_header()
    points = limits.dcv_limits
    if point in range(0, len(points)):
        points = [points[point]]
    for pvstep in points:
        r = pvstep.range
        target = pvstep.target
        dmm.config_basic()
        dmm.range_dcv(r)
        if pvstep.extra_mode:
            dmm.write(pvstep.extra_mode)
        cal.set_v(target)
        cal.enable()
        sleep(cfg.pv.step_dwell)
        dmm_rdg = read_multi(dmm.get_rdg, cfg.pv.discard, cfg.pv.keep, logf.debug, 'dut').median
        cal.disable()
        delta = dmm_rdg - target
        print_result(r, target, dmm_rdg, delta, pvstep.tol)
    return


# gather calsteps together
calsteps = [None, None, step2, ]

def main():
    parser = argparse.ArgumentParser(description="hp 3478a performance verif")
    parser.add_argument('-c', '--cfg', type=argparse.FileType('r'), required=True, help='config file')
    parser.add_argument('-s', '--step', type=int, help='run only step #')
    parser.add_argument('-p', '--point', type=int, help='run only one cal point (use with -s)')
    parser.add_argument('-t', action='store_true', help='test mode (dev)')
    parser.add_argument('-l', '--log', default='pv_tmp.log', help='output log file')
    args = parser.parse_args(sys.argv[1:])

    global cfg
    cfg = magiconfig(args.cfg)

    point = args.point
    if (point and not args.step):
        print('cannot specify single point without step !')
        exit()

    ## setup logging, test/debug options
    global logf
    logf = logging.getLogger()
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    file_handler = logging.FileHandler(filename=args.log, mode='w')
    #for stdout : don't print 'info:root' prefix
    stdout_handler.setFormatter(logging.Formatter('%(message)s'))
    logging.basicConfig(handlers=[file_handler, stdout_handler])

    global testmode
    testmode = args.t

    if testmode:
        dmm = dmm_3478(pyvisa_dummy('dmm_dummy'))
        calsource = caldummy()
        logf.setLevel(logging.DEBUG)
    else:
        rm = pyvisa.ResourceManager()
        dmm_res = rm.open_resource(cfg.dmm.res)
        dmm = dmm_3478(dmm_res)
        logf.setLevel(logging.INFO)

    ## start cal process
    logf.info(f'start PV on {dt.datetime.now().isoformat()}')
    logf.info(f'Using following parameters for PV:')
    cfg.print_configtree(logf)

    print('\n******** STEP 1 (prep)')

    steps = calsteps
    if args.step in range(2, len(calsteps)+1):
        steps = [calsteps[args.step]]
        print(f'Running only step {steps}')

    for s in steps:
        s(dmm, calsource, limits_1y, point)

    logf.info(f'\n*********** DONE *********')
    return


if __name__ == '__main__':
    main()
