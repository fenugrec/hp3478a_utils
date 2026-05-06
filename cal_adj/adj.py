#!/usr/bin/env python

# fenugrec 2026, gplv3
# for hp3478a
# This script implements the 'Calibration' (=adjustment) described in SM section 4-48, p.43

# **** usage:
# - copy/edit .conf file for connection settings and cal resistor values
# - copy/customize cal_mfc.py as required for calibrator used

# **** code structure
# - main() near the end initializes stuff
# - general config is held in external adj.conf to ideally avoid having to edit this script at all

# TODO :
# - read f/r switch
# - check errors
# - check cal switch status
# - truncate strings to correct width when sending 'real value' to 3478

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

def logprint(*args, **kwargs):
    logf.info(*args, **kwargs)

#func to format each measurement result
def print_result_header():
    logprint(f'\n{'range':10}\t{'target':10}\t{'reading':10}\t{'delta':20}\t{'tol':10}\t{'pass':10}')

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
    logprint(f'{range:8g}\t{tgt:10.7g}\t{rdg:10.7g}\t'
        + f'{delta:10.7g} ({delta_ppm:.4g} ppm)\t{tol:10.7g}\t{result}')

# ugh, normalize resistance values to match 3478 display, cant have exp notation
# e.g. 999.97k on range 3e6 should be '0.99997'
def normalize_rval(range, rval):
    while range > 1e3:
        rval /= 1e3
        range /= 1e3
    return rval

######## cal points

@dataclass
class calstep():
    range: float
    val: float = None   #actual value of Ohms std
    freq: float = 0 # for AC ranges
    extra_mode: str = None  # optional config like AZ off, 3/4/5 digit etc
    config_dwell: str = None   #if set, will query .conf for given string and use its value. Only for I stuff

mfc_r_root=1.9
class calpoints():
    dcv = [
            calstep(30e-3),
            calstep(300e-3),
            calstep(3),
            calstep(30),
            calstep(300),
            ]
    # dci, acv, aci a bit weird, no point in having a table
    r = [
            calstep(3e1, mfc_r_root*1e1),
            calstep(3e2, mfc_r_root*1e2),
            calstep(3e3, mfc_r_root*1e3),
            calstep(3e4, mfc_r_root*1e4),
            calstep(3e5, mfc_r_root*1e5),
            calstep(3e6, mfc_r_root*1e6),
            calstep(3e7, mfc_r_root*1e7),
            ]

def adj_dcv(dmm, cal, point=None):
    print('\n******** DCV ********')
    print('******** CAUTION up to 300V on terminals ! ********')
    print('******** wiring for 4-wire sense : DUT_L => CAL_FL, CAL_SL')
    cal.disable()
    input("-------- press Enter when ready ---------")
    cal.set_dcv(0)
    dmm.config_basic()
    points = calpoints.dcv
    if point in range(0, len(points)):
        points = [points[point]]
    for ap in points:
        r = ap.range
        logf.info(f'adjusting range {r}')
        dmm.range_dcv(r)
#        cal.set_dcv(0)
        cal.set_r(0)
        cal.enable()
#        input('--------- optional: apply short, enter when done')
        sleep(cfg.adj.step_dwell)
        dmm.write('D2+000000')
        dmm.write('C')
        dmm.wait_stb(10)
        cal.set_dcv(r)
        cal.enable()
        sleep(cfg.adj.step_dwell)
        # assume calibrator is applying exact value
        # tweak entered value for mV ranges!
        if r < 1:
            r = r * 1000
        dmm.write(f'D2+{r:.5f}')
        dmm.write('C')
        dmm.wait_stb(10)
        cal.disable()
    return

def adj_dci(dmm, cal, point=None):
    print('\n******** DCI up to 1A ********')
    cal.disable()
    input("-------- disconnect dmm, press Enter ")
    dmm.config_basic()
    dmm.range_dci(0.3)
    sleep(cfg.adj.step_dwell)
    dmm.write('D2+000000')
    dmm.write('C')
    dmm.wait_stb(10)
    dmm.range_dci(3)
    sleep(cfg.adj.step_dwell)
    dmm.write('D2+000000')
    dmm.write('C')
    dmm.wait_stb(10)
    dmm.range_dci(0.3)
    cal.set_dci(0.1)
    cal.enable()
    sleep(30)
    dmm.write('D2+100.000')
    dmm.write('C')
    dmm.wait_stb(10)
    dmm.range_dci(3)
    cal.set_dci(1)
    sleep(180)
    dmm.write('D2+1.00000')
    dmm.write('C')
    dmm.wait_stb(10)
    cal.set_dci(0)
    cal.disable()
    return

# SM says, only one signal, 3V 1kHz
def adj_acv(dmm, cal, point=None):
    print('\n******** ACV ********')
    cal.disable()
    input("-------- connect 4-wire sense to dut")
    dmm.config_basic()
    dmm.range_acv(3)
    cal.set_acv(3, 1e3)
    cal.enable()
    sleep(cfg.adj.step_dwell)
    dmm.write('D2+3.00000')
    dmm.write('C')
    dmm.wait_stb(10)
    cal.set_dcv(0)
    cal.disable()
    return

def adj_aci(dmm, cal, point=None):
    print('ACI cal normally not needed. skipping')
    return

def adj_r(dmm, cal, point=None):
    print('\n******** R (4w) ********')
    print('******** wiring for 4-wire sense')
    cal.disable()
    input("-------- press Enter when ready ---------")
    dmm.config_basic()
    points = calpoints.r
    if point in range(0, len(points)):
        points = [points[point]]
    for ap in points:
        r = ap.range
        val = ap.val
        val_real = cfg.calsource.rvalues[val]
        val_normal = normalize_rval(r, val_real)
        logf.info(f'adjusting range {r} with nominal {val}, actual {val_real}')
        dmm.range_r4(r)
        cal.set_r4(0)
        cal.enable()
        input('--------- optional: apply short, enter when done')
        sleep(cfg.adj.step_dwell)
        dmm.write('D2+000000')
        dmm.write('C')
        dmm.wait_stb(10)
        cal.set_r4(val)
        sleep(cfg.adj.step_dwell)
        dmm.write(f'D2+{val_normal:.5f}')
        dmm.write('C')
        dmm.wait_stb(10)
        cal.disable()
    return


# gather calsteps together
calsteps = [adj_dcv, adj_dci, adj_acv, adj_aci, adj_r]

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
        logprint('cannot specify single point without step !')
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
    logf.info(f'start cal on {dt.datetime.now().isoformat()}')
    logf.info(f'Using following parameters:')
    cfg.print_configtree(logf)

    logprint('\n******** STEP 1 (prep)\nbacking up CAL constants...')
    caldata = dmm.get_caldata()
    logf.info(f'original cal data:\n{caldata}')

    steps = calsteps
    if args.step in range(0, len(calsteps)+1):
        steps = [calsteps[args.step]]
        logprint(f'Running only step {args.step}')

    for s in steps:
        s(dmm, calsource, point)

    caldata = dmm.get_caldata()
    logf.info(f'new cal data:\n{caldata}')
    logf.info(f'\n*********** DONE *********')
    return


if __name__ == '__main__':
    main()
