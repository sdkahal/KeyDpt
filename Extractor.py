import sys
import os
import asyncio
import aiofiles
import collections
import pygob
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import nest_asyncio

async def symmetric_decrypt(key, ciphertext):
    iv = ciphertext[:AES.block_size]
    data = ciphertext[AES.block_size:]
    cipher_ecb = AES.new(key, AES.MODE_ECB)
    iv = cipher_ecb.decrypt(iv)
    cipher_cbc = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher_cbc.decrypt(data)
    return unpad(decrypted, AES.block_size)

async def xor_decrypt(key, ciphertext):
    decrypted = bytearray(len(ciphertext))
    for i in range(len(ciphertext)):
        decrypted[i] = ciphertext[i] ^ key[i % len(key)]
    return bytes(decrypted)

async def extract_key_from_local_dat(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 错误：在 {os.getcwd()} 找不到文件 {file_path}")
        return

    try:
        async with aiofiles.open(file_path, mode='rb') as f:
            content = await f.read()

        content_dec = await symmetric_decrypt(b" s  t  e  a  m   ", content)
        content_dec = await xor_decrypt(b"hail", content_dec)

        content_gob_gen = pygob.load_all(bytes(content_dec))
        raw_data = list(content_gob_gen)

        if not raw_data:
            print("❌ 解析失败：Gob 数据为空")
            return

        target_obj = raw_data[0]

        app_id_val = getattr(target_obj, 'Appid', 'Unknown')
        depots_list = getattr(target_obj, 'Depots', [])

        print(f"\n✅ 成功解析！AppID: {app_id_val}")
        print(f"📊 包含 Depot 数量: {len(depots_list)}")
        print("-" * 40)
        
        for depot in depots_list:
            d_id = getattr(depot, 'Id', 'Unknown')
            k_bytes = getattr(depot, 'Decryptkey', b'')
            
            if k_bytes:
                k_hex = k_bytes.hex() if hasattr(k_bytes, 'hex') else str(k_bytes)
                print(f"🔹 Depot ID: {d_id}")
                print(f"🔑 Decryption Key: {k_hex}")
                print("-" * 40)
            else:
                print(f"🔸 Depot ID: {d_id} (未发现解密 Key)")

    except Exception as e:
        print(f"❌ 运行时错误: {e}")
        import traceback
        traceback.print_exc()

nest_asyncio.apply()

repo_scripts_path = '/content/DepotDownloaderMod/Scripts'
if os.path.exists(repo_scripts_path):
    os.chdir(repo_scripts_path)
    sys.path.append(repo_scripts_path)

asyncio.run(extract_key_from_local_dat('00000encrypt.dat'))