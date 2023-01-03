import json
import base64
from algosdk import account, mnemonic, constants
from algosdk.v2client import algod
from algosdk.future import transaction
from algosdk.future.transaction import AssetConfigTxn, AssetTransferTxn, wait_for_confirmation
from algosdk.mnemonic import to_private_key


#Creating accounts
def create_accounts():
    
    global private_key1
    global my_mnemonic1
    global my_address1

    global private_key2
    global my_mnemonic2
    global my_address2

    print("Creating accounts function")

    private_key1, my_address1 = account.generate_account()
    print("My address 1: {}".format(my_address1))
    print("My private key 1: {}".format(private_key1))
    print("My passphrase 1: {}".format(mnemonic.from_private_key(private_key1)))

    my_mnemonic1 = mnemonic.from_private_key(private_key1)

    private_key2, my_address2 = account.generate_account()
    print("My address 2: {}".format(my_address2))
    print("My private key 2: {}".format(private_key2))
    print("My passphrase 2: {}".format(mnemonic.from_private_key(private_key2)))

    my_mnemonic2 = mnemonic.from_private_key(private_key2)


#Creating an asset
def create_asset(algod_address, my_address1, my_mnemonic1):

    global asset_id

    print("Creating an asset function")

    algod_client = algod.AlgodClient("", algod_address)

    asset_creator_address = my_address1
    passphrase = my_mnemonic1
    private_key = to_private_key(passphrase)

    txn = AssetConfigTxn(
        sender=asset_creator_address,
        sp=algod_client.suggested_params(),
        total=1000,
        default_frozen=False,
        unit_name="LATINUM",
        asset_name="latinum",
        manager=asset_creator_address,
        reserve=asset_creator_address,
        freeze=asset_creator_address,
        clawback=asset_creator_address,
        url="https://path/to/my/asset/details", 
        decimals=0)

    # Sign with secret key of creator
    stxn = txn.sign(private_key)
    
    # Send the transaction to the network and retrieve the txid.
    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)  
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))   
    except Exception as err:
        print(err)
    
    # Retrieve the asset ID of the newly created asset by first
    # ensuring that the creation transaction was confirmed,
    # then grabbing the asset id from the transaction.
    print("Transaction information: {}".format(json.dumps(confirmed_txn, indent=4)))
    #print("Decoded note: {}".format(base64.b64decode(confirmed_txn["txn"]["txn"]["note"]).decode()))
    try:
        # get asset_id from tx
        ptx = algod_client.pending_transaction_info(txid)
        asset_id = ptx["asset-index"]
        print("Asset ID: ", asset_id)

    except Exception as err:
        print(err)




#Modifying an asset
def update_asset(algod_address, asset_id, my_address1, my_mnemonic1, my_address2):
    
    print("Modifying an asset function")

    algod_client = algod.AlgodClient("", algod_address)

    asset_creator_address = my_address1
    passphrase = my_mnemonic1
    private_key = to_private_key(passphrase)

    asset_new_manager_address = my_address2

    params = algod_client.suggested_params()

    txn = AssetConfigTxn(
        sender=asset_creator_address,
        sp=params,
        index=asset_id, 
        manager=asset_new_manager_address,
        reserve=asset_creator_address,
        freeze=asset_creator_address,
        clawback=asset_creator_address)

    stxn = txn.sign(private_key)
    
    # txid = algod_client.send_transaction(stxn)
    # print(txid)
    # Wait for the transaction to be confirmed
    # Send the transaction to the network and retrieve the txid.
    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4) 
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))   
    except Exception as err:
        print(err)    
    # Check asset info to view change in management. manager should now be account 2



#OPT-IN an asset
def optin_asset(algod_address, asset_id, my_address1, my_mnemonic1):
    
    print("OPT-IN an asset function")

    algod_client = algod.AlgodClient("", algod_address)

    asset_optin_address = my_address1
    passphrase = my_mnemonic1
    private_key = to_private_key(passphrase)

    params = algod_client.suggested_params()

    account_info = algod_client.account_info(asset_optin_address)
    holding = None
    idx = 0
    for my_account_info in account_info['assets']:        
        scrutinized_asset = account_info['assets'][idx]
        idx = idx + 1            
        print("Opt-in asset index = ", scrutinized_asset['asset-id'])
        if (scrutinized_asset['asset-id'] == asset_id):
            holding = True
            break

    if not holding:
        # Use the AssetTransferTxn class to transfer assets and opt-in
        txn = AssetTransferTxn(
            sender=asset_optin_address,
            sp=params,
            receiver=asset_optin_address,
            amt=0,
            index=asset_id)
        stxn = txn.sign(private_key)
        
        # Send the transaction to the network and retrieve the txid.
        try:
            txid = algod_client.send_transaction(stxn)
            print("Signed transaction with txID: {}".format(txid))
            # Wait for the transaction to be confirmed
            confirmed_txn = wait_for_confirmation(algod_client, txid, 4) 
            print("TXID: ", txid)
            print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))    
        except Exception as err:
            print(err)
        # Now check the asset holding for that account.
        # This should now show a holding with a balance of 0.

        print("Checking Opt-in asset")
        account_info = algod_client.account_info(asset_optin_address)
        idx = 0        
        for my_account_info in account_info['assets']:        
            scrutinized_asset = account_info['assets'][idx]
            idx = idx + 1    
            print("Opt-in asset index = ", scrutinized_asset['asset-id'])




#Transferring an asset
def transfer_asset(algod_address, asset_id, my_address1, my_mnemonic1, my_address2):
    
    print("Transferring an asset function")

    algod_client = algod.AlgodClient("", algod_address)

    asset_from_address = my_address1
    passphrase = my_mnemonic1
    private_key = to_private_key(passphrase)

    asset_to_address = my_address2

    params = algod_client.suggested_params()

    txn = AssetTransferTxn(
        sender=asset_from_address,
        sp=params,
        receiver=asset_to_address,
        amt=10,
        index=asset_id)
    stxn = txn.sign(private_key)
    
    # Send the transaction to the network and retrieve the txid.
    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4) 
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))
    except Exception as err:
        print(err)
    # The balance should now be 10 on address 2.



#Revoking an asset
def revoke_asset(algod_address, asset_id, my_address1, my_mnemonic1, my_address2, my_mnemonic2):
    
    print("Revoking an asset function")

    algod_client = algod.AlgodClient("", algod_address)

    asset_from_address = my_address1
    passphrase = my_mnemonic1
    private_key = to_private_key(passphrase)

    asset_to_address = my_address2

    params = algod_client.suggested_params()

    txn = AssetTransferTxn(
        sender=asset_from_address,
        sp=params,
        receiver=asset_from_address,
        amt=10,
        index=asset_id,
        revocation_target=asset_to_address)
    stxn = txn.sign(private_key)
    
    # Send the transaction to the network and retrieve the txid.
    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4) 
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))
    except Exception as err:
        print(err)
    # The balance should now be 0 on address 2.


#Destroying an asset
def destroy_asset(algod_address, asset_id, my_address1, my_mnemonic1):
    
    print("Destroying an asset function")

    algod_client = algod.AlgodClient("", algod_address)

    asset_manager_address = my_address1
    passphrase = my_mnemonic1
    private_key = to_private_key(passphrase)

    params = algod_client.suggested_params()

    txn = AssetConfigTxn(
        sender=asset_manager_address,
        sp=params,
        index=asset_id,
        strict_empty_address_check=False
        )
    # Sign with secret key of creator
    stxn = txn.sign(private_key)

    # Send the transaction to the network and retrieve the txid.
    try:
        txid = algod_client.send_transaction(stxn)
        print("Signed transaction with txID: {}".format(txid))
        # Wait for the transaction to be confirmed
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4) 
        print("TXID: ", txid)
        print("Result confirmed in round: {}".format(confirmed_txn['confirmed-round']))     
    except Exception as err:
        print(err)
    # Asset was deleted.




asset_id = 150806978

algod_address = "https://testnet-api.algonode.cloud"

private_key1 = "1LuqqWyO46+xgisLFrlTpdxvvbNmuY8jBesd9JUKc5bjIj4KzyHyvk/dSIzWxSUjdy9MyypjdLWi/EU1PJUV1Q=="
my_mnemonic1 = "kind priority feel traffic shove hip better clog scrap tone prefer ski text urban culture ride impose behind void dove cloud section receive above core"
my_address1 = "4MRD4CWPEHZL4T65JCGNNRJFEN3S6TGLFJRXJNNC7RCTKPEVCXKYCIJ27M"

private_key2 = "qIIva7Y3r0Qw58J3ip3NCCu/jcnroLg3nHHNt8+xKkb2IDWHqe18loVkPOk+XAORD72cRq3/VgwbmcqY4CdK9A=="
my_mnemonic2 = "fence safe culture kiwi fury bachelor define seed exclude involve grocery rack layer gloom furnace path warfare ignore rhythm lamp panda property course able year"
my_address2 = "6YQDLB5J5V6JNBLEHTUT4XADSEH33HCGVX7VMDA3THFJRYBHJL2IIMBRPU"


#Uncomment the functions step by step

#step 1
#create my addresses 1 and 2 by the function create_accounts()
#create_accounts()
#Uncomment the function above create_accounts() and execute the script

#step 2
#create new asset by the function create_asset()
#create_asset(algod_address, my_address1, my_mnemonic1)
#Uncomment the function above create_asset() and execute the script

#step 3
#modify an asset by the function update_asset()
#update_asset(algod_address, asset_id, my_address1, my_mnemonic1, my_address2)
#Uncomment the function above update_asset() and execute the script

#step 4
#OPT-IN an asset in addresses 1 and 2 by the function optin_asset()
#optin_asset(algod_address, asset_id, my_address1, my_mnemonic1)
#optin_asset(algod_address, asset_id, my_address2, my_mnemonic2)
#Uncomment the function above optin_asset() and execute the script

#step 5
#transfer an asset from address 1 to address 2 by the function transfer_asset()
#transfer_asset(algod_address, asset_id, my_address1, my_mnemonic1, my_address2)
#Uncomment the function above transfer_asset() and execute the script

#step 6
#revoke an asset from address 2 to address 1 by the function revoke_asset()
#revoke_asset(algod_address, asset_id, my_address1, my_mnemonic1, my_address2, my_mnemonic2)
#Uncomment the function above revoke_asset() and execute the script

#step 7
#destroy an asset the function destroy_asset()
#destroy_asset(algod_address, asset_id, my_address2, my_mnemonic2)
#Uncomment the function above destroy_asset() and execute the script