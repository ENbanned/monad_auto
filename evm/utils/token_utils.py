from typing import Optional
from ..client import EVMClient


async def get_token_balance(
    client: EVMClient,
    token_address: str,
    wallet_address: Optional[str] = None
) -> int:
    wallet_address = wallet_address or client.account.address
    token_address = client.web3.to_checksum_address(token_address)

    contract = client.web3.eth.contract(
        address=token_address,
        abi=[{
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }]
    )
    return await contract.functions.balanceOf(wallet_address).call()


async def approve_token_if_needed(
    client: EVMClient,
    token_address: str,
    spender: str,
    amount_wei: int
) -> Optional[str]:
    erc20_abi = [
        {
            "constant": True,
            "inputs": [
                {"name": "_owner", "type": "address"},
                {"name": "_spender", "type": "address"}
            ],
            "name": "allowance",
            "outputs": [{"name": "remaining", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "success", "type": "bool"}],
            "type": "function"
        }
    ]

    token_contract = client.web3.eth.contract(
        address=token_address,
        abi=erc20_abi
    )
    
    allowance = await token_contract.functions.allowance(
        client.account.address,
        spender
    ).call()

    if allowance < amount_wei:
        approve_amount = amount_wei * 10
        tx = await client.build_transaction(
            to=token_address,
            data=token_contract.encodeABI(
                fn_name="approve",
                args=[spender, approve_amount]
            )
        )
        return await client.send_transaction(tx)

    return None
