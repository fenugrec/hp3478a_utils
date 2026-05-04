#!/usr/bin/env python

# fenugrec 2026, gplv3
# for hp3478a
# This script implements the Performance Tests described in SM section 4-21, p.35

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

rvalues_real = {
        0: 0.0000020,
        1: 0.9997092,
        1.9: 1.8996760,
        10: 10.001010,
        19: 18.998463,
        100: 99.99357,
        190: 189.99445,
        1e3: 0.9999300e3,
        1.9e3: 1.8998757e3,
        10e3: 9.999638e3,
        19e3: 18.999572e3,
        100e3: 99.99350e3,
        190e3: 190.00899e3,
        1e6: 0.9999007e6,
        1.9e6: 1.9000154e6,
        10e6: 9.998262e6,
        19e6: 19.000306e6,
    }
rvalues = {
        0: 0.0000020,
        1: 0.9997092,
        1.9: 1.8996760,
        10: 10.001010,
        19: 18.998463,
        100: 99.99357,
        190: 189.99445,
        1e3: 0.9999300,
        1.9e3: 1.8998757,
        10e3: 9.999638,
        19e3: 18.999572,
        100e3: 99.99350,
        190e3: 190.00899,
        1e6: 0.9999007,
        1.9e6: 1.9000154,
        10e6: 9.998262,
        19e6: 19.000306,
    }

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
    #dcv_limits : SM 4-27, parag a-w (step 1-25) p. 35
    dcv_shorted = [
            pvstep(30e-3, 0, 4e-6),
            pvstep(0.3, 0, 5e-6),
            pvstep(3, 0, 20e-6),
            pvstep(30, 0, 40e-6),
            pvstep(300, 0, 2e-3),
            ]
    dcv_limits = [
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
            pvstep(0.3, 0.1, 190e-6, config_dwell='dly_100mA'),
            pvstep(3, 1, 1.76e-3, config_dwell='dly_1A'),
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
            pvstep(0.3, 100e-3, 883e-6, freq=5e3, config_dwell='dly_100mA'),
            pvstep(1, 1, 15.83e-3, freq=5e3, config_dwell='dly_1A'),
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
            pvstep(30, 19, 14.3e-3),
            pvstep(300, 190, 56e-3),
            pvstep(3e3, 1.9e3, 500e-3),
            pvstep(30e3, 19e3, 5),
            pvstep(300e3, 190e3, 50),
            pvstep(3e6, 1.9e6, 500),
            pvstep(30e6, 19e6, 23.6e3),
            #            pvstep(30, 30, 14.3e-3),
            #            pvstep(300, 300, 56e-3),
            #            pvstep(3e3, 3e3, 500e-3),
            #            pvstep(30e3, 30e3, 5),
            #            pvstep(300e3, 300e3, 50),
            #            pvstep(3e6, 3e6, 500),
            #            pvstep(30e6, 30e6, 23.6e3),
            ]

def step1(dmm, cal, limits, point=None):
    logprint('\n******** STEP 1 DCV ********')
    logprint('*** initial wiring : DUT inputs SHORTED L to H')
    input("-------- press Enter when ready ---------")
    logf.debug('\n STEP 1')
    cal.disable()
    cal.set_r(0)
    cal.enable()
    print_result_header()
    points = limits.dcv_shorted
    if point in range(0, len(points)):
        points = [points[point]]
    for pvstep in points:
        dmm.config_basic()
        r = pvstep.range
        dmm.range_dcv(r)
        sleep(cfg.pv.step_dwell)
        dmm_rdg = read_multi(dmm.get_rdg, cfg.pv.discard, cfg.pv.keep, logf.debug, 'dut').median
        delta = dmm_rdg - 0
        print_result(r, 0, dmm_rdg, delta, pvstep.tol)
    return

def step2(dmm, cal, limits, point=None):
    logprint('\n******** STEP 2 DCV ********')
    logprint('******** CAUTION up to 300V on terminals ! ********')
    logprint('*** wiring: 2-wire, DUT to CALSRC')
    input("-------- press Enter when ready ---------")
    cal.disable()
    cal.set_dcv(0)
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
        cal.set_dcv(target)
        cal.enable()
        sleep(cfg.pv.step_dwell)
        dmm_rdg = read_multi(dmm.get_rdg, cfg.pv.discard, cfg.pv.keep, logf.debug, 'dut').median
        cal.disable()
        delta = dmm_rdg - target
        print_result(r, target, dmm_rdg, delta, pvstep.tol)
    cal.set_dcv(0)
    return

def step3(dmm, cal, limits, point=None):
    logprint('\n******** STEP 3 DCI ********')
    logprint('*** wiring for CURRENT up to 1A')
    input("-------- press Enter when ready ---------")
    cal.disable()
    cal.write('CUR_POST AUX')
    cal.set_dci(0)
    print_result_header()
    points = limits.dci_limits
    if point in range(0, len(points)):
        points = [points[point]]
    for pvstep in points:
        r = pvstep.range
        target = pvstep.target
        dmm.config_basic()
        dmm.range_dci(r)
        cal.set_dci(target)
        cal.enable()
        if pvstep.config_dwell:
            dwell = getattr(cfg.pv, pvstep.config_dwell)
        else:
            dwell = cfg.pv.step_dwell
        sleep(dwell)
        dmm_rdg = read_multi(dmm.get_rdg, cfg.pv.discard, cfg.pv.keep, logf.debug, 'dut').median
        cal.disable()
        delta = dmm_rdg - target
        print_result(r, target, dmm_rdg, delta, pvstep.tol)
    cal.set_dci(0)
    return

def step4(dmm, cal, limits, point=None):
    logprint('\n******** STEP 4 ACV ********')
    logprint('******** CAUTION up to 300V on terminals ! ********')
    logprint('*** wiring: 2-wire, DUT to CALSRC')
    input("-------- press Enter when ready ---------")
    cal.disable()
    cal.set_acv(0, 60)
    print_result_header()
    points = limits.acv_limits
    if point in range(0, len(points)):
        points = [points[point]]
    for pvstep in points:
        r = pvstep.range
        target = pvstep.target
        dmm.config_basic()
        dmm.range_acv(r)
        if pvstep.extra_mode:
            dmm.write(pvstep.extra_mode)
        cal.set_acv(target, pvstep.freq)
        cal.enable()
        dwell = cfg.pv.step_dwell
        sleep(dwell)
        dmm_rdg = read_multi(dmm.get_rdg, cfg.pv.discard, cfg.pv.keep, logf.debug, 'dut').median
        cal.disable()
        delta = dmm_rdg - target
        print_result(r, target, dmm_rdg, delta, pvstep.tol)
    cal.set_dcv(0)
    return

def step5(dmm, cal, limits, point=None):
    logprint('\n******** STEP 5 ACI ********')
    logprint('*** wiring for CURRENT up to 1A')
    input("-------- press Enter when ready ---------")
    cal.disable()
    cal.write('CUR_POST AUX')
    cal.set_aci(0, 0)
    print_result_header()
    points = limits.aci_limits
    if point in range(0, len(points)):
        points = [points[point]]
    for pvstep in points:
        r = pvstep.range
        target = pvstep.target
        dmm.config_basic()
        dmm.range_aci(r)
        cal.set_aci(target, pvstep.freq)
        cal.enable()
        if pvstep.config_dwell:
            dwell = getattr(cfg.pv, pvstep.config_dwell)
        else:
            dwell = cfg.pv.step_dwell
        sleep(dwell)
        dmm_rdg = read_multi(dmm.get_rdg, cfg.pv.discard, cfg.pv.keep, logf.debug, 'dut').median
        cal.disable()
        delta = dmm_rdg - target
        print_result(r, target, dmm_rdg, delta, pvstep.tol)
    cal.set_aci(0, 0)
    return

def step6(dmm, cal, limits, point=None):
    print('\n******** R (4w) ********')
    print('******** wiring for 4-wire sense')
    cal.disable()
    input("-------- press Enter when ready ---------")
    print_result_header()
    dmm.config_basic()
    points = limits.r_limits
    if point in range(0, len(points)):
        points = [points[point]]
    for ap in points:
        r = ap.range
        val = ap.target
        val_actual = rvalues_real[int(val)]
        dmm.range_r4(r)
        cal.set_r4(0)
        cal.enable()
        if r <= 300 and 0:
            input('--------- optional: apply short, enter when done')
        sleep(cfg.pv.step_dwell)
        cal.set_r4(val)
        dwell = cfg.pv.step_dwell
        sleep(dwell)
        dmm_rdg = read_multi(dmm.get_rdg, cfg.pv.discard, cfg.pv.keep, logf.debug, 'dut').median
        cal.disable()
        delta = dmm_rdg - val_actual
        print_result(r, val_actual, dmm_rdg, delta, ap.tol)
    return

# gather calsteps together
calsteps = [None, step1, step2, step3, step4, step5, step6]

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
    logf.info(f'start PV on {dt.datetime.now().isoformat()}')
    logf.info(f'Using following parameters for PV:')
    cfg.print_configtree(logf)

    logprint('\n******** STEP 1 (prep)')

    steps = calsteps
    if args.step in range(1, len(calsteps)+1):
        steps = [calsteps[args.step]]
        logprint(f'Running only step {args.step}')

    for s in steps:
        s(dmm, calsource, limits_1y, point)

    logf.info(f'\n*********** DONE *********')
    return


if __name__ == '__main__':
    main()
