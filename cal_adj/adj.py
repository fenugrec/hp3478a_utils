#!/usr/bin/env python

# fenugrec 2026, gplv3
# for hp3478a
# This script implements the 'Calibration' (=adjustment) described in SM section 4-48, p.43

# **** usage:
# - copy/edit .conf file for connection settings and cal resistor values
# - copy/customize cal_mfc.py as required for calibrator used

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
from cal_mfc import *
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

######## cal points

@dataclass
class calstep():
    range: float
    freq: float = 0 # for AC ranges
    extra_mode: str = None  # optional config like AZ off, 3/4/5 digit etc
    config_dwell: str = None   #if set, will query .conf for given string and use its value. Only for I stuff

class calpoints():
    dcv = [
            calstep(30e-3),
            calstep(300e-3),
            calstep(3),
            calstep(30),
            calstep(300),
            ]

def adj_dcv(dmm, cal, point=None):
    cal.disable()
    cal.mode_dcv()
    cal.set_v(0)
    dmm.config_basic()
    points = calpoints.dcv
    if point in range(0, len(points)):
        points = [points[point]]
    for ap in points:
        r = ap.range
        logf.info(f'adjusting range {r}')
        dmm.range_dcv(r)
        cal.set_v(0)
        cal.enable()
        input('--------- optional: apply short, enter when done')
        sleep(cfg.pv.step_dwell)
        dmm.write('D2+000000')
        dmm.write('C')
        input('--------- observe "CALIBRATING", enter when done')
        cal.set_v(target)
        sleep(cfg.pv.step_dwell)
        # assume calibrator is applying exact value
        dmm.write(f'D2+{r:.5g}')
        dmm.write('C')
        input('--------- wait for "CAL FINISHED", enter when done')
        cal.disable()


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
    parser = argparse.ArgumentParser(description="hp 3478a calibration (adjustment)")
    parser.add_argument('-c', '--cfg', type=argparse.FileType('r'), required=True, help='config file')
    parser.add_argument('-s', '--step', type=int, help='run only step #')
    parser.add_argument('-p', '--point', type=int, help='run only one cal point (use with -s)')
    parser.add_argument('-t', action='store_true', help='test mode (dev)')
    parser.add_argument('-l', '--log', default='cal.log', help='output log file')
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
        calsource = cal_mfc(pyvisa_dummy('dmm_dummy'))
        logf.setLevel(logging.DEBUG)
    else:
        rm = pyvisa.ResourceManager()
        dmm = dmm_3478(rm.open_resource(cfg.dut.res))
        calsource = cal_mfc(rm.open_resource(cfg.calsource.res))
        logf.setLevel(logging.INFO)

    ## start cal process
    logf.info(f'start PV on {dt.datetime.now().isoformat()}')
    logf.info(f'Using following parameters for PV:')
    cfg.print_configtree(logf)

    print('\n******** STEP 1 (prep)')

    steps = calsteps
    if args.step in range(2, len(calsteps)+1):
        steps = [calsteps[args.step]]
        print(f'Running only step {args.step}')

    for s in steps:
        s(dmm, calsource, point)

    logf.info(f'\n*********** DONE *********')
    return


if __name__ == '__main__':
    main()
