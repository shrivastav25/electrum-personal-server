#! /usr/bin/python3

from configparser import ConfigParser, NoSectionError
from jsonrpc import JsonRpc, JsonRpcError
from datetime import datetime

def search_for_block_height_of_date(datestr, rpc):
    target_time = datetime.strptime(datestr, "%d/%m/%Y")
    bestblockhash = rpc.call("getbestblockhash", [])
    best_head = rpc.call("getblockheader", [bestblockhash])
    if target_time > datetime.fromtimestamp(best_head["time"]):
        print("ERROR: date in the future")
        return -1
    genesis_block = rpc.call("getblockheader", [rpc.call("getblockhash", [0])])
    if target_time < datetime.fromtimestamp(genesis_block["time"]):
        print("WARNING: date is before the creation of bitcoin")
        return 0
    first_height = 0
    last_height = best_head["height"]
    while True:
        m = (first_height + last_height) // 2
        m_header = rpc.call("getblockheader", [rpc.call("getblockhash", [m])])
        m_header_time = datetime.fromtimestamp(m_header["time"])
        m_time_diff = (m_header_time - target_time).total_seconds()
        if abs(m_time_diff) < 60*60*2: #2 hours
            return m_header["height"]
        elif m_time_diff < 0:
            first_height = m
        elif m_time_diff > 0:
            last_height = m
        else:
            return -1

def main():
    try:
        config = ConfigParser()
        config.read(["config.cfg"])
        config.options("electrum-master-public-keys")
    except NoSectionError:
        log("Non-existant configuration file `config.cfg`")
        return
    rpc = JsonRpc(host = config.get("bitcoin-rpc", "host"),
                port = int(config.get("bitcoin-rpc", "port")),
                user = config.get("bitcoin-rpc", "user"),
                password = config.get("bitcoin-rpc", "password"))
    user_input = input("Enter earliest wallet creation date (DD/MM/YYYY) "
        "or block height to rescan from: ")
    try:
        height = int(user_input)
    except ValueError:
        height = search_for_block_height_of_date(user_input, rpc)
        if height == -1:
            return
        height -= 2016 #go back two weeks for safety

    if input("Rescan from block height " + str(height) + " ? (y/n):") != 'y':
        return
    rpc.call("rescanblockchain", [height])
    print("end")
    

main()

