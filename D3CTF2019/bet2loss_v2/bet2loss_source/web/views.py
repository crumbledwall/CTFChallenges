import sha3
import binascii
import traceback
import base64
import time
import hashlib
from web3 import Web3, HTTPProvider
from core.bet2loss_bin import bet2loss_bin
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from core.function import random_num, random_str, get_code
from core.bet2loss_abi import Bet2lossABI
from bet2loss.settings import account
from bet2loss.settings import rpcurl
from web.models import HashTable, Contract

w3 = Web3(Web3.HTTPProvider(rpcurl, request_kwargs={'timeout': 60}))


def index(req):
    return render(req, 'index.html')

def code(req):
    if(req.session.exists("code")):
        return JsonResponse({"code": req.session['code']})
    else:
        req.session['code'] = get_code()
        return JsonResponse({"code": req.session['code']})


def random(req):
    team_id = req.META['HTTP_HOST'].split(".")[0]
    team = Contract.objects.filter(team_id=team_id)
    if len(team) == 0:
        return HttpResponse("You haven't got your own contract address")
    result = {'gasPrice': 12000000000}

    reveal = random_num()
    result['commit'] = "0x" + sha3.keccak_256(
        bytes.fromhex(binascii.hexlify(reveal.to_bytes(32, 'big')).decode('utf-8'))).hexdigest()

    result['commitLastBlock'] = w3.eth.blockNumber + 250

    h = HashTable(reveal=reveal, commit=result['commit'], commitlastblock=result['commitLastBlock'])
    h.save()

    message = binascii.hexlify(result['commitLastBlock'].to_bytes(5, 'big')).decode('utf-8') + result['commit'][2:]
    message_hash = '0x' + sha3.keccak_256(bytes.fromhex(message)).hexdigest()
    signhash = w3.eth.account.signHash(message_hash, private_key=account['croupier']['private_key'])

    result['signature'] = {}
    result['signature']['r'] = '0x' + binascii.hexlify((signhash['r']).to_bytes(32, 'big')).decode('utf-8')
    result['signature']['s'] = '0x' + binascii.hexlify((signhash['s']).to_bytes(32, 'big')).decode('utf-8')

    result['signature']['v'] = signhash['v']

    return JsonResponse(result)


@csrf_exempt
def settlebet(req):
    if 'commit' in req.POST:
        commit = req.POST['commit']
        team_id = req.META['HTTP_HOST'].split(".")[0]
        team = Contract.objects.filter(team_id=team_id)
        if len(team) == 0:
            return HttpResponse("You haven't got your own contract address")
        w3 = Web3(HTTPProvider(rpcurl))
        bet2loss = w3.eth.contract(abi=Bet2lossABI)
        bet2loss = bet2loss(address=Web3.toChecksumAddress(team[0].address))

        h = HashTable.objects.filter(commit=commit, is_settle=0)

        if len(h) == 0:
            return HttpResponse('bad guys!')

        h = h[0]
        reveal = h.reveal
        nonce = w3.eth.getTransactionCount(account['croupier']['address'])

        try:
            transaction = bet2loss.functions.settleBet(int(reveal)).buildTransaction(
                {'chainId': 3, 'gas': 100000, 'nonce': nonce, 'gasPrice': w3.toWei('1', 'gwei')})

            signed = w3.eth.account.signTransaction(transaction, account['croupier']['private_key'])
            result = w3.eth.sendRawTransaction(signed.rawTransaction)

        except:
            print(traceback.print_exc())
            return HttpResponse("Bad network, please retry.")

        h.is_settle = 1
        h.save()

        return HttpResponse('Bet finished.')

    else:
        return HttpResponse('Welcome to d^3ctf ;>')


@csrf_exempt
def deploy(req):
    team_id = req.META['HTTP_HOST'].split(".")[0]
    team = Contract.objects.filter(team_id=team_id)
    if "first" in req.GET.keys():
        if len(team) == 0:
            return HttpResponse("Haven't got address yet.")
        else:
            result = {"address": team[0].address}
            return JsonResponse(result)
    
    else:
        if 'code' in req.POST:
            str_req = req.POST['code']
            hashobj = hashlib.md5()
            hashobj.update(bytes(str_req, encoding='utf-8'))
            hash_req = hashobj.hexdigest()[:6]
            if req.session['code'] == hash_req:
                gaslimit = 2000000
                w3 = Web3(HTTPProvider(rpcurl))
                tx = {
                    'from': account['owner']['address'],
                    'nonce': w3.eth.getTransactionCount(account['owner']['address']),
                    'gas': gaslimit,
                    'value': 0,
                    'gasPrice': w3.eth.gasPrice*10,
                    'data': '0x' + bet2loss_bin,
                }
                try:
                    signed_tx = w3.eth.account.signTransaction(tx, account['owner']['private_key'])
                    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
                    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
                    if len(team) == 0:
                        team = Contract(team_id=team_id, address=tx_receipt.contractAddress)
                        team.save()
                    else:
                        team.update(address=tx_receipt.contractAddress)
                    result = {"address": tx_receipt.contractAddress}
                    req.session['code'] = get_code()
                    return JsonResponse(result)
                except:
                    print(traceback.print_exc())
                    return HttpResponse("Bad network, please retry.")
            else:
                return HttpResponse("Wrong code.")
        else:
            return HttpResponse("Code required.")


@csrf_exempt
def checkflag(req):
    team_id = req.META['HTTP_HOST'].split(".")[0]
    team = Contract.objects.filter(team_id=team_id)
    if len(team) == 0:
        return HttpResponse("You haven't got your own contract address")
    address = team[0].address
    w3 = Web3(HTTPProvider(rpcurl))
    try:
        flag_logs = w3.eth.getLogs({"address": Web3.toChecksumAddress(address),
                                "topics": ["0x8c4b53bc7444f9d52efc9942d9d10fdd15b45421761af26fe1a5189bcd2bbb37"],
                                "fromBlock": "0x64d63f"})
    except:
        return HttpResponse("Bad network, please retry.")
    if flag_logs:
        return JsonResponse({"flag": r"d3ctf\{bet2loss_v2_example_flag\}"})
    return HttpResponse("It seems that you haven't got the flag")
