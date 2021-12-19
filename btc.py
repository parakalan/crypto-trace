import requests

satoshi_to_btc = 0.00000001
btc_to_satoshi = 1 / satoshi_to_btc

def get_all_transactions(address):
    """
        Get all transactions involving `address` from blockchain.com API
    """
    all_txns = []
    resp = requests.get(f"https://api.blockchain.info/haskoin-store/btc/address/{address}/transactions/full?limit=4000&offset=0").json()
    all_txns = all_txns + resp
    offset = 4000
    limit = 8000
    while len(resp) >= 4000:
        resp = requests.get(f"https://api.blockchain.info/haskoin-store/btc/address/{address}/transactions/full?limit={limit}&offset={offset}").json()
        offset = limit + 1
        limit += 4000
        all_txns = all_txns + resp
    all_txns_unique = []
    txn_hash = set()
    for txn in all_txns:
        if txn['txid'] not in txn_hash:
            all_txns_unique.append(txn)
            txn_hash.add(txn['txid'])
    return all_txns_unique

def get_major_contributor(all_txns, address):
    """
        Get major contributor to this address, ie., the wallet which has sent the most to this.
        Note that this can also be coinbase transactions (newly mined coins)
    """
    address_value_map = {}
    address_value_map["COINBASE"] = 0
    for txn in all_txns:
        input_wallet_ids = [i['address'] for i in txn['inputs']]
        output_wallet_ids = [i['address'] for i in txn['outputs']]
        if address in output_wallet_ids and not address in input_wallet_ids:
            for inp in txn['inputs']:
                if inp['coinbase']:
                    for op in txn['outputs']:
                        if op['address'] == address:
                            address_value_map["COINBASE"] += op['value']
                    break
                else:
                    address_value_map[inp['address']] = address_value_map.get(inp['address'], 0) + inp['value']
    major = max(address_value_map.items(), key=lambda m: m[1])
    return major

def get_major_chain(address):
    chain = []
    """
        Get major chain to this address, ie. the path which contributed most to this address. We find this out getting
        the major contributor recursively.

        Example -
        We want to find the major chain for address `N`. We see that `D` has sent the most BTC to `N`. We find the wallet
        which sent most BTC to `D`, which is `C` suppose. We continue this until we reach address `A` which gets newly minted coins.

        This is one such chain -

        COINBASE -> 18cBEMRxXHqzWWCxZNtU91F5sbUNKhL5PX -> 1JLQ5izr2QZnEwNbUsVJTGRAbDgJ628vL4 -> bc1q4xtxgpjn82anm7dvhqjshud2j5qzlcckqf60c6 -> bc1qpkq0sssdm8wemesv6v3yjq0gh39tjzpd34mjfj
    """
    major = address
    while major != "COINBASE":
        all_txns = get_all_transactions(major)
        major, value = get_major_contributor(all_txns, major)
        chain.append((major, value * satoshi_to_btc))
    return chain

if __name__ == '__main__':
    print(get_major_chain("bc1qpkq0sssdm8wemesv6v3yjq0gh39tjzpd34mjfj"))
