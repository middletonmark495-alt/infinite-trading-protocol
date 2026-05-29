"""EVM wallet balance queries and transaction signing for the dashboard."""

from typing import Optional
from web3 import Web3

CHAINS: dict[str, dict] = {
    "ethereum": {"rpc": "https://eth.llamarpc.com",          "chain_id": 1,     "name": "Ethereum",     "symbol": "ETH"},
    "base":     {"rpc": "https://mainnet.base.org",           "chain_id": 8453,  "name": "Base",         "symbol": "ETH"},
    "polygon":  {"rpc": "https://polygon-rpc.com",            "chain_id": 137,   "name": "Polygon",      "symbol": "POL"},
    "arbitrum": {"rpc": "https://arb1.arbitrum.io/rpc",       "chain_id": 42161, "name": "Arbitrum One", "symbol": "ETH"},
    "optimism": {"rpc": "https://mainnet.optimism.io",        "chain_id": 10,    "name": "OP Mainnet",   "symbol": "ETH"},
}

ERC20_ABI = [
    {"constant": True,  "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True,  "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}],   "type": "function"},
    {"constant": True,  "inputs": [], "name": "symbol",   "outputs": [{"name": "", "type": "string"}],  "type": "function"},
    {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
]

# Popular tokens per network (address, symbol, decimals)
TOKENS: dict[str, list[dict]] = {
    "ethereum": [
        {"address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "symbol": "USDC",  "decimals": 6},
        {"address": "0xdAC17F958D2ee523a2206206994597C13D831ec7", "symbol": "USDT",  "decimals": 6},
        {"address": "0x6B175474E89094C44Da98b954EedeAC495271d0F", "symbol": "DAI",   "decimals": 18},
        {"address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", "symbol": "WBTC",  "decimals": 8},
        {"address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "symbol": "WETH",  "decimals": 18},
        {"address": "0x514910771AF9Ca656af840dff83E8264EcF986CA", "symbol": "LINK",  "decimals": 18},
        {"address": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", "symbol": "UNI",   "decimals": 18},
    ],
    "base": [
        {"address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "symbol": "USDC",  "decimals": 6},
        {"address": "0x4200000000000000000000000000000000000006", "symbol": "WETH",  "decimals": 18},
        {"address": "0x940181a94A35A4569E4529a3CDfB74e38FD98631", "symbol": "AERO",  "decimals": 18},
        {"address": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb", "symbol": "DAI",   "decimals": 18},
    ],
    "polygon": [
        {"address": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", "symbol": "USDC",  "decimals": 6},
        {"address": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F", "symbol": "USDT",  "decimals": 6},
        {"address": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063", "symbol": "DAI",   "decimals": 18},
        {"address": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6", "symbol": "WBTC",  "decimals": 8},
    ],
    "arbitrum": [
        {"address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", "symbol": "USDC",  "decimals": 6},
        {"address": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9", "symbol": "USDT",  "decimals": 6},
        {"address": "0x912CE59144191C1204E64559FE8253a0e49E6548", "symbol": "ARB",   "decimals": 18},
        {"address": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f", "symbol": "WBTC",  "decimals": 8},
    ],
    "optimism": [
        {"address": "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85", "symbol": "USDC",  "decimals": 6},
        {"address": "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58", "symbol": "USDT",  "decimals": 6},
        {"address": "0x4200000000000000000000000000000000000042", "symbol": "OP",    "decimals": 18},
        {"address": "0x68f180fcCe6836688e9084f035309E29Bf0A2095", "symbol": "WBTC",  "decimals": 8},
    ],
}


class EVMService:
    def _w3(self, network: str, rpc_url: Optional[str] = None) -> Web3:
        chain = CHAINS.get(network)
        if not chain:
            raise ValueError(f"Unknown network: {network}. Valid: {list(CHAINS)}")
        return Web3(Web3.HTTPProvider(rpc_url or chain["rpc"]))

    def get_native_balance(self, address: str, network: str, rpc_url: Optional[str] = None) -> dict:
        w3 = self._w3(network, rpc_url)
        chain = CHAINS[network]
        checksum = Web3.to_checksum_address(address)
        wei = w3.eth.get_balance(checksum)
        return {
            "symbol": chain["symbol"],
            "balance": float(Web3.from_wei(wei, "ether")),
            "balance_raw": str(wei),
            "name": chain["name"],
        }

    def get_token_balances(self, address: str, network: str, rpc_url: Optional[str] = None) -> list[dict]:
        w3 = self._w3(network, rpc_url)
        checksum = Web3.to_checksum_address(address)
        results: list[dict] = []
        for tok in TOKENS.get(network, []):
            try:
                contract = w3.eth.contract(address=Web3.to_checksum_address(tok["address"]), abi=ERC20_ABI)
                raw = contract.functions.balanceOf(checksum).call()
                balance = raw / (10 ** tok["decimals"])
                if balance > 0:
                    results.append({"symbol": tok["symbol"], "address": tok["address"], "balance": balance, "decimals": tok["decimals"]})
            except Exception:
                pass
        return results

    def send_eth(self, from_addr: str, to_addr: str, amount_eth: str, network: str, private_key: str, rpc_url: Optional[str] = None) -> str:
        w3 = self._w3(network, rpc_url)
        chain = CHAINS[network]
        fr = Web3.to_checksum_address(from_addr)
        to = Web3.to_checksum_address(to_addr)
        value = w3.to_wei(float(amount_eth), "ether")
        nonce = w3.eth.get_transaction_count(fr)
        gas_price = w3.eth.gas_price
        tx = {"nonce": nonce, "to": to, "value": value, "gas": 21000, "gasPrice": gas_price, "chainId": chain["chain_id"]}
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()

    def send_token(self, from_addr: str, to_addr: str, token_address: str, amount: str, decimals: int, network: str, private_key: str, rpc_url: Optional[str] = None) -> str:
        w3 = self._w3(network, rpc_url)
        chain = CHAINS[network]
        fr = Web3.to_checksum_address(from_addr)
        to = Web3.to_checksum_address(to_addr)
        tok = Web3.to_checksum_address(token_address)
        contract = w3.eth.contract(address=tok, abi=ERC20_ABI)
        raw_amount = int(float(amount) * (10 ** decimals))
        nonce = w3.eth.get_transaction_count(fr)
        gas_price = w3.eth.gas_price
        tx = contract.functions.transfer(to, raw_amount).build_transaction({
            "chainId": chain["chain_id"], "gas": 100000, "gasPrice": gas_price, "nonce": nonce,
        })
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()

    @staticmethod
    def list_chains() -> list[dict]:
        return [{"id": k, "name": v["name"], "symbol": v["symbol"], "chain_id": v["chain_id"]} for k, v in CHAINS.items()]
