# MIT License

# Copyright (c) 2022 Duke University. All rights reserved.

# See LICENSE for license information

from sre_constants import SUCCESS
import subprocess
import argparse
import os
import json
import time

from husky_config import *

ETH_DEV = None
MONITOR_SEC = 2
ETH_BYTES = "rx_vport_rdma_unicast_bytes"
ETH_PACKETS = "rx_vport_rdma_unicast_packets"

TEST_CNT = 0
SUCCESS_CNT = 0

def List(config: dict):
    directory = config[DIRECTORY]
    print ("Victims: ")
    victims = os.listdir("{}/victim/".format(directory))
    victims.sort()
    for victim in victims:
        print ("      {}".format(victim))
    print ("")
    print ("Attackers: ")
    print ("  BW - ")
    BW_attackers = os.listdir("{}/attacker/BW/".format(directory))
    BW_attackers.sort()
    for attacker in BW_attackers:
        print ("      {}".format(attacker))
    print ("  PCIe - ")
    PCIe_attackers = os.listdir("{}/attacker/PCIe/".format(directory))
    PCIe_attackers.sort()
    for attacker in PCIe_attackers:
        print ("      {}".format(attacker))
    print ("  Cache -")
    Cache_attackers = os.listdir("{}/attacker/Cache/".format(directory))
    Cache_attackers.sort()
    for attacker in Cache_attackers:
        print ("      {}".format(attacker))
    print ("  PU - ")
    PU_attackers = os.listdir("{}/attacker/PU/".format(directory))
    PU_attackers.sort()
    for attacker in PU_attackers:
        print ("      {}".format(attacker))


def SetupTraffic(config, file, verbose):
    run_cmd = ["bash", file]
    # This invoke the background process
    if verbose == False:
        subprocess.run(run_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(run_cmd)

def MonitorVictim(config, victim):
    username = config[VICTIM_USER_NAME]
    receiver = config[VICTIM_MGMT_IP_LIST][RECEIVE_IDX]
    for _ in victim.split('_'):
        if 'r' == _ or "read" == _:
            receiver = config[VICTIM_MGMT_IP_LIST][SEND_IDX]
            break
    global ETH_DEV
    eth_dev = ETH_DEV
    # Get Victim Receiver Name
    if ETH_DEV == None:
        cmd = "ssh {}@{} \'ibdev2netdev\' ".format(username, receiver)
        output = subprocess.check_output(cmd, shell=True).decode().split('\n')
        for l in output:
            if config[VICTIM_DEVICE] in l:
                words = l.split(' ')
                eth_dev = words[-2]
        if eth_dev == None:
            print ("Warning: no such device on victim receiver - {}".format(config[VICTIM_DEVICE]))
            return None,None
        ETH_DEV = eth_dev
    
    cmd = "ssh {}@{} \'python3 /tmp/rdma_monitor.py --interface {} --count {}\'".format(username, receiver, eth_dev, MONITOR_SEC)
    result = subprocess.check_output(cmd, shell=True).decode().split('\n')
    bps = float(result[0].split(':')[-1])
    pps = float(result[1].split(':')[-1])
    return bps, pps


def CleanupTraffics(config):
    for ip in config[ATTACKER_MGMT_IP_LIST]:
        cmd = "ssh {}@{} \'python3 /tmp/rdma_monitor.py --action kill  \' >/dev/null 2>/dev/null".format(config[ATTACKER_USER_NAME], ip)
        subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
    for ip in config[VICTIM_MGMT_IP_LIST]:
        cmd = "ssh {}@{} \'python3 /tmp/rdma_monitor.py --action kill  \' >/dev/null 2>/dev/null".format(config[VICTIM_USER_NAME], ip)
        subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)

def OneTest(config, victim, attacker, verbose: bool):
    global TEST_CNT
    global SUCCESS_CNT
    # Set up victim 
    SetupTraffic(config, victim, verbose)
    # Get victim performance
    bps, pps = MonitorVictim(config, victim)
    print  ("Test Case #{}".format(TEST_CNT + 1))
    OUTPUT ("Attacker: {}".format(attacker.split('/')[-1]))
    OUTPUT ("Victim:   {}".format(victim.split('/')[-1]))
    OUTPUT ("Victim performance w/o attacker:")
    OUTPUT ("        {:.3f} Gbps".format(bps))
    OUTPUT ("        {:.3f} Mpps".format(pps))
    # Set up attacker
    SetupTraffic(config, attacker, verbose)
    # wait for a while
    time.sleep(1)
    atk_bps, atk_pps = MonitorVictim(config, victim)
    OUTPUT ("[Under Attack] Victim performance:")
    OUTPUT ("        {:.3f} Gbps".format(atk_bps))
    OUTPUT ("        {:.3f} Mpps".format(atk_pps))
    # Clean up all the traffics and compute
    CleanupTraffics(config)
    bps_ratio = atk_bps * 1.0 / bps
    pps_ratio = atk_pps * 1.0 / pps
    if bps_ratio < config[ALPHA] or pps_ratio < config[ALPHA]: 
        OUTPUT ("The degradation for bps is {:.3f}%".format(100.0 * (1 - bps_ratio)))
        OUTPUT ("The degradation for pps is {:.3f}%".format(100.0 * (1 - pps_ratio)))
        ERROR_OUTPUT ("Test ...... Fail")
    else:
        OUTPUT ("Test ...... Success")
        SUCCESS_CNT += 1
    TEST_CNT += 1
    print ("Current test: {}/{} tests passed.".format(SUCCESS_CNT, TEST_CNT))
    print ()

def OUTPUT(message: str):
    print("\033[0;32;40m{}\033[0m".format(message))

def ERROR_OUTPUT(message: str):
    print("\033[1;31;40m{}\033[0m".format(message))

def GetTestList(config, args):
    directory = config[DIRECTORY]
    attackers = None
    victims = None
    if args.victim == None:
        victim_names = os.listdir("{}/victim/".format(directory))
        victims = ["{}/victim/{}".format(directory, v) for v in victim_names]
    else:
        if os.path.exists("{}/victim/{}".format(directory, args.victim)):
            victims = ["{}/victim/{}".format(directory, args.victim)] 
    if args.attacker == "all":
        attackers = []
        for t in ["PU", "PCIe", "BW", "Cache"]:
            attacker_names = os.listdir("{}/attacker/{}/".format(directory, t))
            attackers += ["{}/attacker/{}/{}".format(directory, t, atk) for atk in attacker_names]
    else:
        attack_type = args.attacker.split('-')[0]
        try:
            if args.attacker.endswith("all"):
                attacker_names = os.listdir("{}/attacker/{}/".format(directory, attack_type))
                attackers = ["{}/attacker/{}/{}".format(directory, attack_type, atk) for atk in attacker_names]
            else:
                if os.path.exists("{}/attacker/{}/{}".format(directory, attack_type, args.attacker)):
                    attackers = ["{}/attacker/{}/{}".format(directory, attack_type, args.attacker)]
        except Exception as e:
            print (e)
            return None, victims
    if attackers != None:
        attackers.sort()
    if victims != None:
        victims.sort()
    return attackers, victims

def RunTests(config:dict, attackers: list, victims: list, verbose : bool):
    print ("Test start!!!!!")
    print()
    for attacker in attackers:
        for victim in victims:
            OneTest(config, victim, attacker, verbose)

def main():
    parser = argparse.ArgumentParser(description="Run Test")
    parser.add_argument("--config", action="store", required=True, help="The configuration file for scripts. See example.json as config example.")
    parser.add_argument("--list", default=False, action="store_true", help="list all the tests")
    parser.add_argument("--victim", action="store", type=str, default=None, help="The selected victim traffic. None means run all.")
    parser.add_argument("--attacker", action="store", default=None, type=str,
                        help="The selected attacker traffic. Select a concrete traffic (e.g., BW-1MB_ib_write_bw) or a set of traffics (e.g., BW-all)")
    parser.add_argument("--verbose", action="store_true", default=False, help="print more details")
    args = parser.parse_args()
    config = {}
    with open(args.config, "r") as f:
        config = json.load(f)
    if (args.list == True):
        List(config)
        exit(0)
    if (args.attacker == None):
        print ("Should set attacker (concrete traffic or at least a type)")
        exit(0)

    attackers, victims = GetTestList(config, args)
    if attackers == None or victims == None:
        print ("Invalid attacker or victim...")
        print ("Exit...")
        exit(0)

    RunTests(config, attackers=attackers, victims=victims, verbose=args.verbose)


if __name__ == "__main__":
    main()