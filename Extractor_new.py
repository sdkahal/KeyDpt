import sys
import os
import asyncio
import aiofiles
import collections
import pygob
import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import nest_asyncio

RAW_URL_TEMPLATE = "https://raw.githubusercontent.com/luckygametools/steam-cfg/master/steamdb2/{appid}/00000encrypt.dat"
MIRROR_URL_TEMPLATE = "https://cdn.jsdelivr.net/gh/luckygametools/steam-cfg@master/steamdb2/{appid}/00000encrypt.dat"

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

async def download_and_extract(appid):
    print(f"🔍 正在尝试获取 AppID: {appid} 的解密文件...")
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        content = None
        for url in [RAW_URL_TEMPLATE.format(appid=appid), MIRROR_URL_TEMPLATE.format(appid=appid)]:
            try:
                print(f"📡 正在连接: {url[:50]}...")
                resp = await client.get(url)
                if resp.status_code == 200:
                    content = resp.content
                    print("✅ 文件下载成功！")
                    break
            except Exception as e:
                continue
        
        if not content:
            print(f"❌ 错误：无法在仓库中找到 AppID {appid} 的数据文件，请检查 AppID 是否正确或仓库是否已更新。")
            return

    try:
        content_dec = await symmetric_decrypt(b" s  t  e  a  m  ", content)
        content_dec = await xor_decrypt(b"hail", content_dec)

        content_gob_gen = pygob.load_all(bytes(content_dec))
        raw_data = list(content_gob_gen)

        if not raw_data:
            print("❌ 解析失败：Gob 数据内容异常")
            return

        target_obj = raw_data[0]
        app_id_val = getattr(target_obj, 'Appid', appid)
        depots_list = getattr(target_obj, 'Depots', [])

        print(f"\n✨ 解析成功！App名称/ID: {app_id_val}")
        print(f"📊 包含 Depot 数量: {len(depots_list)}")
        print("-" * 45)
        
        for depot in depots_list:
            d_id = getattr(depot, 'Id', 'Unknown')
            k_bytes = getattr(depot, 'Decryptkey', b'')
            
            if k_bytes:
                k_hex = k_bytes.hex() if hasattr(k_bytes, 'hex') else str(k_bytes)
                print(f"🔹 Depot: {d_id}")
                print(f"🔑 Key  : {k_hex}")
                print("-" * 45)
            else:
                print(f"🔸 Depot: {d_id} (未发现解密 Key)")

    except Exception as e:
        print(f"❌ 运行时处理错误: {e}")

if __name__ == "__main__":
    nest_asyncio.apply()

    repo_scripts_path = '/content/DepotDownloaderMod/Scripts'
    if os.path.exists(repo_scripts_path):
        os.chdir(repo_scripts_path)
        sys.path.append(repo_scripts_path)

    input_id = input("请输入游戏的 AppID (例如 1245620): ").strip()
    if input_id:
        asyncio.run(download_and_extract(input_id))
    else:
        print("未输入有效的 AppID")