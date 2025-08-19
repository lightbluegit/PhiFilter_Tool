from typing import Any, Optional, Union
from base64 import b64decode
from requests import Session
from struct import unpack, pack
from hashlib import md5
from zipfile import ZipFile, ZIP_DEFLATED
from io import BytesIO
from base64 import b64decode, b64encode
from hmac import new
from json import dumps
from hashlib import sha256, sha1
from random import randint
from time import *
from uuid import uuid4
from qrcode import make
from time import sleep
from Crypto.Cipher.AES import new, MODE_CBC, block_size
from Crypto.Util.Padding import unpad, pad
import pandas as pd


# ---------------------- 信息获取相关操作喵 ----------------------
aes_key = b64decode("6Jaa0qVAJZuXkZCLiOa/Ax5tIZVu+taKUN1V1nqwkks=")
aes_iv = b64decode("Kk/wisgNYwcAV8WVGMgyUw==")


def checkSessionToken(sessionToken):
    return True


class TapTapLogin:
    AppKey: str = "Qr9AEqtuoSVS3zeD6iVbM4ZC0AtkJcQ89tywVyi0"  # 构建请求头要用
    CloudServerAddress: str = (
        "https://rak3ffdi.cloud.tds1.tapapis.cn"  # 独属phi的Taptap云服务域名）
    )
    ClientId: str = "rAK3FfdieFob2Nn8Am"  # 独属phi的ID
    Client: Session = Session()

    ChinaWebHost: str = "https://accounts.tapapis.cn"
    ChinaApiHost: str = "https://open.tapapis.cn"  # 获取当前账户详细信息
    ChinaCodeUrl: str = ChinaWebHost + "/oauth2/v1/device/code"
    ChinaTokenUrl: str = ChinaWebHost + "/oauth2/v1/token"
    TapSDKVersion: str = "2.1"

    @staticmethod
    def GetMd5Hash(string: str) -> str:
        """获取string的md5hash"""
        md5_hash = md5(string.encode())
        return md5_hash.hexdigest()

    @staticmethod
    def RequestLoginQRCode():
        """请求一个新QRCode的信息"""
        device_id: str = uuid4().hex  # 随机一个device_id出来
        data: dict = {
            "client_id": TapTapLogin.ClientId,
            "response_type": "device_code",
            "scope": "public_profile",
            "version": TapTapLogin.TapSDKVersion,
            "platform": "unity",
            "info": {"device_id": device_id},
        }
        QRCode_info: dict = TapTapLogin.Request(
            url=TapTapLogin.ChinaCodeUrl, method="POST", data=data
        )

        return {
            "device_id": device_id,
            **QRCode_info["data"],
        }  # 把device_id先放进去，省的后面还要另外处理

    @staticmethod
    def CheckQRCodeResult(qrCodeData):
        """检查QRCode的登录授权情况"""
        data: dict = {
            "grant_type": "device_token",
            "client_id": TapTapLogin.ClientId,
            "secret_type": "hmac-sha-1",
            "code": qrCodeData["device_code"],
            "version": "1.0",
            "platform": "unity",
            "info": dumps({"device_id": qrCodeData["device_id"]}),
        }
        try:
            result = TapTapLogin.Request(
                url=TapTapLogin.ChinaTokenUrl, method="POST", data=data
            )

            return result

        except Exception as e:
            return {"error": e}

    @staticmethod
    def GetProfile(token: dict):
        """获取用户信息，可用于后面获取userdata"""
        if not token:
            raise ValueError("传入的token无效！")

        hasPublicProfile: bool = "public_profile" in token["scope"]
        if hasPublicProfile:
            ChinaProfileUrl: str = (
                TapTapLogin.ChinaApiHost + "/account/profile/v1?client_id="
            )
        else:
            ChinaProfileUrl: str = (
                TapTapLogin.ChinaApiHost + "/account/basic-info/v1?client_id="
            )

        url: str = ChinaProfileUrl + TapTapLogin.ClientId
        uri: str = url.split("//")[1]
        sign: str = "MAC " + TapTapLogin.ParseAuthorizationHeader(
            kid=token["kid"],
            mac_key=token["mac_key"],
            mac_algorithm=token["mac_algorithm"],
            method="GET",
            uri="/" + uri.split("/", 1)[1],
            host=uri.split("/")[0],
            port="443",
            timestamp=int(time()),
        )

        response: dict = TapTapLogin.Request(
            url=url, method="GET", headers={"Authorization": sign}
        )

        return response

    @staticmethod
    def GetUserData(data: dict):
        """获取Phigros的userdata"""
        url: str = f"{TapTapLogin.CloudServerAddress}/1.1/users"
        response: dict = TapTapLogin.Request(
            url=url,
            method="POST",
            headers={
                "X-LC-Id": TapTapLogin.ClientId,
                "Content-Type": "application/json",  # 想研究原理的注意一下，此处得保证请求头的Content-Type为application/json
            },
            data={"authData": {"taptap": data}},
            addAppKey=True,
        )
        return response

    @staticmethod
    def Request(
        url: str,
        method: str,
        headers: dict = None,
        data: dict = None,
        addAppKey: bool = False,
    ) -> dict:
        """综合请求函数"""
        headers: dict = (
            headers or {}
        )  # 如果没有传入headers则创建一个空字典，防止构建请求头时出错
        TapTapLogin.ParseHeaders(headers, addAppKey)  # 构建请求头
        method: str = method.upper()  # 将请求类型转为大写便于判断

        if method == "POST":  # 如果是POST请求
            if (
                headers.get("Content-Type") == "application/json"
            ):  # 对GetUserData做适配性判断
                data: str = dumps(data)  # 序列化为标准json字符串
            else:
                data: dict = {
                    key: str(value) for key, value in data.items()
                }  # 将所有值转为字符串

            response = TapTapLogin.Client.post(url, headers=headers, data=data)

        elif method == "GET":  # 如果是GET请求
            response = TapTapLogin.Client.get(url, headers=headers)

        else:
            raise ValueError("不支持的请求类型！")

        print(f"Request type：{method}")
        print(f"Request URL：{url}")
        print(f"Request header：{headers}")
        print(f"Request data：{data}")
        print(f"Return header：{response.headers}")
        print(f"Status code：{response.status_code}")
        try:
            print(f"Return data：{response.content.decode()}")
        except UnicodeDecodeError:
            print(f"Return data：Decoding data failed")

        response.raise_for_status()  # 对非200状态码抛出错误
        return response.json()  # 将响应数据反序列化为字典

    @staticmethod
    def ParseAuthorizationHeader(
        kid, mac_key, mac_algorithm, method, uri, host, port, timestamp
    ):
        """构建Authorization请求头"""
        nonce = str(randint(0, 2147483647))
        normalized_string = f"{timestamp}\n{nonce}\n{method}\n{uri}\n{host}\n{port}\n\n"

        if mac_algorithm == "hmac-sha-256":
            hash_generator = new(mac_key.encode(), normalized_string.encode(), sha256)
        elif mac_algorithm == "hmac-sha-1":
            # print(
            #     f"mac_key.encode()={mac_key.encode()},normalized_string.encode()={normalized_string.encode()}"
            # )
            # hash_generator = new(mac_key.encode(), normalized_string.encode(), sha1)
            import hmac  # ?为什么又要hmac了?????????

            hash_value = hmac.new(
                mac_key.encode(), normalized_string.encode(), sha1
            ).digest()
        else:
            raise ValueError("Unsupported MAC algorithm")

        # hash_value = b64encode(hash_generator.digest()).decode()
        # return f'id="{kid}",ts="{timestamp}",nonce="{nonce}",mac="{hash_value}"'
        return f'id="{kid}",ts="{timestamp}",nonce="{nonce}",mac="{b64encode(hash_value).decode()}"'

    @staticmethod
    def ParseHeaders(headers, addAppKey: bool = False):
        """构造签名请求头"""
        timestamp = int(time() * 1000)
        if addAppKey:  # GetUserData会用到带AppKey的签名
            data = f"{timestamp}{TapTapLogin.AppKey}"
        else:
            data = str(timestamp)

        hash_value = TapTapLogin.GetMd5Hash(data)
        sign = f"{hash_value},{timestamp}"
        headers["X-LC-Sign"] = sign


class PigeonRequest:
    def __init__(
        self,
        sessionToken: Optional[str] = None,
        client: Optional[Session] = None,
        headers: Optional[dict] = None,
    ):
        if client:
            self.client = client
        else:
            self.client = Session()

        if headers:
            self.headers = headers
        else:
            self.headers = {
                "X-LC-Id": "rAK3FfdieFob2Nn8Am",
                "X-LC-Key": "Qr9AEqtuoSVS3zeD6iVbM4ZC0AtkJcQ89tywVyi0",
                "User-Agent": "LeanCloud-CSharp-SDK/1.0.3",
                "Accept": "application/json",
                "X-LC-Session": sessionToken,
            }  # 全局的默认请求头喵

        self._req = None

    def addHeaders(self, headers: Optional[dict] = None, **kwargs):
        if headers:
            header = {**self.headers, **headers, **kwargs}

        else:
            header = {**self.headers, **kwargs}

        return PigeonRequest(client=self.client, headers=header)

    def request(self, method: str, url: str, headers: Optional[dict] = None, **kwargs):
        method = method.upper()

        if headers is None:
            headers = self.headers

        if method == "GET":
            self._req = self.client.get(url, headers=headers, **kwargs)

        elif method == "POST":
            self._req = self.client.post(url, headers=headers, **kwargs)

        elif method == "PUT":
            self._req = self.client.put(url, headers=headers, **kwargs)

        elif method == "DELETE":
            self._req = self.client.delete(url, headers=headers, **kwargs)

        else:
            raise ValueError(f'传入的请求类型不合法喵！不应为"{method}"！')

        print(f"请求类型 ：{method}")
        print(f"请求URL ：{url}")
        print(f"请求头 ：{self._req.request.headers}")
        print(f"状态码 ：{self._req.status_code}")

        if self._req.request.body is None:
            print(f"请求数据 : *无请求数据*")

        elif isinstance(self._req.request.body, str):
            print(f"请求数据 : {repr(self._req.request.body)}")

        else:
            print(f"请求数据 : *{len(self._req.request.body)} bytes*")

        if self._req.content is None:
            print(f"返回数据 : *无返回数据*")
        else:
            try:
                print(f"返回数据 : {self._req.content.decode()}")

            except UnicodeDecodeError:
                print(f"返回数据 : *{len(self._req.content)} bytes*")

        self._req.raise_for_status()

        return self._req

    def get(self, url: str, headers: Optional[dict] = None):
        return self.request("GET", url, headers)

    def post(
        self,
        url: str,
        data: Optional[Union[str, bytes]] = None,
        headers: Optional[dict] = None,
    ):
        return self.request("POST", url, headers, data=data)

    def put(
        self,
        url: str,
        data: Optional[Union[str, bytes]] = None,
        headers: Optional[dict] = None,
    ):
        return self.request("PUT", url, headers, data=data)

    def delete(self, url: str, headers: Optional[dict] = None):
        return self.request("DELETE", url, headers)


class PhigrosCloud:
    def __init__(self, sessionToken: str, client: Optional[Any] = None):
        if checkSessionToken(sessionToken):
            self.create_client = False
            if client:
                self.client = client
            else:
                self.client = Session()
                self.create_client = True

            self.request = PigeonRequest(sessionToken, client)
            self.baseUrl = "https://rak3ffdi.cloud.tds1.tapapis.cn/1.1/"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.create_client:
            self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.create_client:
            self.close()

    def close(self):
        self.client.close()

    def getSummary(self):
        """
        获取玩家summary喵

        返回:
            (dict): 玩家summary数据喵
        """
        print("调用函数：getSummary()")

        # 请求并初步解析存档信息喵
        result = (self.request.get(self.baseUrl + "classes/_GameSave?limit=1")).json()[
            "results"
        ][0]
        summary = b64decode(result["summary"])  # base64解码summary数据喵
        print(
            summary
        )  # b'\x06Y\x01\xc0\x94}A\x81\x01\x07\xe7\x93\xb7\xe5\xb2\x811\x00\x00\x00\x00\x00\x00\x05\x00\x04\x00\x02\x00\xdd\x00L\x00\t\x00\x1f\x00\x02\x00\x00\x00'
        # 解析summary数据喵(这行是真的看不懂喵)
        # summary = unpack("=BHfBx%ds12H" % summary[8], summary)
        return_data = {  # 解析数据并返回一个字典喵
            # 这是存档的md5校验值喵
            "checksum": result["gameFile"]["metaData"]["_checksum"],
            "updateAt": result["updatedAt"],  # 这是存档更新时间喵
            "url": result["gameFile"]["url"],  # 这是存档直链喵
            "saveVersion": summary[0],  # 这是存档版本喵
            "challenge": summary[1],  # 课题分喵
            "rks": summary[2],  # 正如其名不多讲了喵
            "gameVersion": summary[3],  # 这是游戏版本喵
            "avatar": summary[4],  # 这是头像喵
            "EZ": summary[5:8],  # EZ难度的评级情况喵
            "HD": summary[8:11],  # HD难度的评级情况喵
            "IN": summary[11:14],  # IN难度的评级情况喵
            "AT": summary[14:17],  # AT难度的评级情况喵
        }

        print(f'函数"getSummary()"返回：{return_data}')
        return return_data

    def getSave(
        self, url: Optional[str] = None, checksum: Optional[str] = None
    ) -> bytes:
        """
        获取存档数据喵 (压缩包数据喵)

        (返回的数据可用ReadGameSave()读取喵)

        参数:
            url (str | None): 存档的 URL 喵。留空自动获取当前token的数据喵
            checksum (str | None): 存档的 md5 校验值喵。留空自动获取当前token的数据喵

        返回:
            (bytes): 存档压缩包数据喵
        """
        print("调用函数：getSave()")

        if url is None:
            return

        elif checksum is None:
            return

        # 请求存档文件并获取数据喵
        save_data = (self.request.get(url)).content  # type: ignore
        if len(save_data) <= 30:
            print(
                f"严重警告喵！！！获取到的云存档大小不足 30 字节喵！当前大小喵：{len(save_data)}"
            )
            print("可能云存档已丢失喵！！！请重新将本地存档同步至云端喵！")
            raise ValueError(
                f"获取到的云存档大小不足 30 字节喵！当前大小喵：{len(save_data)}"
            )

        save_md5 = md5()  # 创建一个md5对象，用来计算md5校验值喵
        save_md5.update(save_data)  # 将存档数据更新进去喵
        actual_checksum = save_md5.hexdigest()
        if checksum != actual_checksum:  # 对比校验值喵，不正确则输出警告并等待喵
            print("严重警告喵！！！存档校验不通过喵！")
            print("这可能是因为不正确地上传存档导致的喵！")
            raise ValueError(
                f"存档校验不通过喵！本地存档md5：{actual_checksum}，云端存档md5：{checksum}"
            )

        print(f'函数"getSave()"返回：*{len(save_data)} bytes*')
        return save_data  # 返回存档数据喵


def unzipSave(zip_data: bytes) -> dict[str, bytes]:
    """
    读取存档压缩包

    参数:
        zip_data (bytes): 压缩包数据喵

    返回:
        (dict[str, bytes]): 存档原始数据喵
    """
    save_dict = {}
    # 打开存档文件喵(其实存档是个压缩包哦喵！)
    with ZipFile(BytesIO(zip_data)) as zip_file:
        # 打开压缩包中中对应的文件喵

        for file in zip_file.filelist:
            filename = file.filename
            print(f'解压"{filename}"文件喵')
            with zip_file.open(filename) as file:
                save_dict[filename] = file.read()  # 读取文件数据喵

    print("解压完毕喵！")
    return save_dict


def decrypt(data: bytes):
    """
    AES CBC解密喵

    参数:
        data (bytes): 要解密的数据喵

    返回:
        (bytes): 解密后的数据
    """
    data = new(aes_key, MODE_CBC, aes_iv).decrypt(data)
    return unpad(data, block_size)


class dataTypeAbstract:
    @staticmethod
    def read(data: bytes, pos: int): ...

    @staticmethod
    def write(data: bytearray, value): ...


class Byte(dataTypeAbstract):
    """一个字节喵 (1字节喵)"""

    @staticmethod
    def read(data: bytes, pos: int):
        """
        读取一个字节的数据喵 (1字节喵)

        参数:
            data (bytes): 包含数据的字节序列喵
            pos (int): 当前数据的字节位置喵

        返回:
            (tuple[int, int]): 包含读取的字节和下一个数据的位置喵
        """
        return data[pos], pos + 1

    @staticmethod
    def write(data: bytearray, value):
        """
        将一段字节写入字节序列喵

        参数:
            data (bytearray): 包含数据的字节序列喵
            value (Any): 要写入的字节值喵

        返回:
            (bytearray): 修改后的数据序列喵
        """
        if isinstance(value, int):
            data.append(value)
        else:
            data.extend(value)

        return data


class VarInt(dataTypeAbstract):
    """变长整型喵 (1-2字节喵)"""

    @staticmethod
    def read(data: bytes, pos: int):
        """
        读取一个变长整型数据喵 (1-2字节喵)

        参数:
            data (bytes): 包含数据的字节序列喵
            pos (int): 当前数据的字节位置喵

        返回:
            (tuple[int, int]): 包含读取的变长整型数据和下一个数据的位置喵
        """
        if data[pos] > 127:  # 如果当前字节位置数据的值大于127喵
            pos += 2  # 将指针后移2位喵
            # 脑子爆烧唔喵
            var_int = (data[pos - 2] & 0b01111111) ^ (data[pos - 1] << 7)
        else:
            var_int = data[pos]  # 读取当前字节位置数据的值喵
            pos += 1  # 将指针后移1位喵

        return var_int, pos  # 最后返回读取到的变长整数喵

    @staticmethod
    def write(data: bytearray, value: int):
        """
        将变长整型数据写入字节序列喵

        参数:
            data (bytearray): 用于存储数据的字节序列喵
            value (int): 需要写入的变长整型数据喵

        返回:
            (bytearray): 更新后的字节序列喵
        """
        if value > 127:  # 如果大于127喵，则写入两个字节喵
            data = Byte.write(data, (value & 0b01111111) | 0b10000000)
            data = Byte.write(data, value >> 7)
        else:
            data = Byte.write(data, value)  # 写入一个字节喵

        return data


class Bit:
    @staticmethod
    def read(data: int, index: int) -> int:
        """
        读取一个整数中指定索引的比特位值喵

        参数:
            int (data): 要读取的整数值喵
            int (index): 比特位索引喵 (0 到 7 ，其中 0 表示最低位喵)

        返回:
            (int): 指定索引的比特位值喵 (1 或 0 喵)
        """
        # return 1 if bool(data & (1 << index)) else 0
        return (data >> index) & 1

    @staticmethod
    def write(data: int, index: int, value: int) -> int:
        """
        修改一个整数中指定索引的比特位值喵

        参数:
            data (int): 要修改的整数值喵
            index (int): 比特位索引喵 (0 到 7 ，其中 0 表示最低位喵)
            value (int): 要设置的比特位值 (1 或 0 喵)

        返回:
            (int): 修改后的整数值
        """
        mask = 1 << index
        return (data & ~mask) | ((value & 1) << index)
        # if value == 0:
        #     return data & ~(1 << index)
        # else:
        #     return data | (1 << index)


class String(dataTypeAbstract):
    """字符串"""

    @staticmethod
    def read(data: bytes, pos: int):
        """
        读取一个字符串数据喵

        参数:
            data (bytes): 包含数据的字节序列喵
            pos (int): 当前数据的字节位置喵

        返回:
            (tuple[int, int]): 包含读取的字符串和下一个数据的位置喵
        """
        string_len, pos = VarInt.read(
            data, pos
        )  # 读当前位置的变长整数喵，代表后续字节长度喵
        string_val = data[pos : pos + string_len].decode()  # 读取一段字节并uft-8解码喵

        return string_val, pos + string_len  # 返回读取到的数据喵

    @staticmethod
    def write(data: bytearray, value: str):
        """
        将字符串数据写入字节序列喵

        参数:
            data (bytearray): 用于存储数据的字节序列喵
            value (str): 需要写入的变长整型数据喵

        返回:
            (bytearray): 更新后的字节序列喵
        """
        encoded_string = value.encode("utf-8")
        data = VarInt.write(data, len(encoded_string))
        data.extend(encoded_string)

        return data


class Int(dataTypeAbstract):
    """整型喵 (4 字节喵)"""

    @staticmethod
    def read(data: bytes, pos: int):
        """
        读取一个整型的数据喵 (4 字节喵)

        参数:
            data (bytes): 包含数据的字节序列喵
            pos (int): 当前数据的字节位置喵

        返回:
            (tuple[int, int]): 包含读取的整型数据和下一个数据的位置喵
        """
        return unpack("<I", data[pos : pos + 4])[0], pos + 4

    @staticmethod
    def write(data: bytearray, value: int):
        """
        将一个整型值写入到字节序列喵

        参数:
            data (bytearray): 存储数据的字节序列喵
            value (int): 需要写入的整型值喵

        返回:
            (bytearray): 更新后的字节序列喵
        """
        data.extend(pack("<I", value))

        return data


class ShortInt(dataTypeAbstract):
    """短整型喵 (2字节喵)"""

    @staticmethod
    def read(data: bytes, pos: int):
        """
        读取一个短整型的数据喵 (2字节喵)

        参数:
            data (bytes): 包含数据的字节序列喵
            pos (int): 当前数据的字节位置喵

        返回:
            (tuple[int, int]): 包含读取的短整型数据和下一个数据的位置喵
        """
        return unpack("<H", data[pos : pos + 2])[0], pos + 2

    @staticmethod
    def write(data: bytearray, value: int):
        """
        将短整型数据写入字节序列喵

        参数:
            data (bytearray): 用于存储数据的字节序列喵
            value (int): 待写入的短整型数据喵

        返回:
            (bytearray): 更新后的字节序列喵
        """
        data.extend(pack("<H", value))

        return data


class Float(dataTypeAbstract):
    """浮点型喵 (4字节喵)"""

    @staticmethod
    def read(data: bytes, pos: int):
        """
        读取一个浮点型数据喵 (4字节喵)

        参数:
            data (bytes): 包含数据的字节序列喵
            pos (int): 当前数据的字节位置喵

        返回:
            (tuple[int, int]): 包含读取的浮点型数据和下一个数据的位置喵
        """
        return unpack("<f", data[pos : pos + 4])[0], pos + 4

    @staticmethod
    def write(data: bytearray, value: float):
        """
        将浮点型数据写入字节序列喵

        参数:
            data (bytearray): 存储数据的字节序列喵
            value (float): 需要写入的浮点型数据喵

        返回:
            (bytearray): 包含写入数据后的字节序列喵
        """
        data.extend(pack("<f", value))

        return data


class _Bits(dataTypeAbstract):
    """比特位喵 (1字节，带长度截取喵)"""

    def __init__(self, _len: int = 8):
        """比特位喵 (1字节，带长度截取喵)"""
        self._len = _len

    def read(self, data: bytes, pos: int) -> tuple[str, int]:
        """
        读取一个整数的所有比特位值喵 (1字节，带长度截取喵)

        参数:
            data (bytes): 要读取的字节数据喵
            pos (int): 数据在字节中的位置喵

        返回:
            (str, int]): 包含每个比特位的值 (1 或 0) 的列表以及下一个字节的位置喵
        """
        bits: list[int] = []
        for i in range(self._len):
            bit = Bit.read(data[pos], i)
            bits.append(bit)

        return str(bits), pos + 1

    @staticmethod
    def write(data: bytearray, value: str) -> bytearray:
        """
        根据给定的比特位值列表构建一个整数喵

        参数:
            data (bytearray): 存储结果的字节数组喵
            value (str): 每个比特位的值 (1 或 0) 的列表喵

        返回:
            (bytearray): 更新后的数据序列喵
        """
        _value: type = eval(value)

        if not isinstance(_value, list):
            raise TypeError(
                f'传入的值不能够被解析为list喵！而被解析为："{_value.__class__.__name__}"'
            )

        byte = 0

        if len(_value) < 8:
            _value.extend([0] * (8 - len(_value)))

        for i, bit in enumerate(_value):
            byte = Bit.write(byte, i, bit)

        data.append(byte)
        return data


class Bits(dataTypeAbstract):
    """比特位喵 (1字节喵)"""

    @staticmethod
    def read(data: bytes, pos: int) -> tuple[str, int]:
        """
        读取一个整数的所有比特位值喵 (1字节喵)

        参数:
            data (bytes): 要读取的字节数据喵
            pos (int): 数据在字节中的位置喵

        返回:
            (tuple[str, int]): 包含每个比特位的值 (1 或 0) 的列表以及下一个字节的位置喵
        """
        bits: list[int] = []
        for i in range(8):  # 一个字节有8位
            bit = Bit.read(data[pos], i)
            bits.append(bit)

        return str(bits), pos + 1

    @staticmethod
    def write(data: bytearray, value: str) -> bytearray:
        """
        根据给定的比特位值列表构建一个整数喵

        参数:
            data (bytearray): 存储结果的字节数组喵
            value (list[int]): 每个比特位的值 (1 或 0) 的列表喵

        返回:
            (bytearray): 更新后的数据序列喵
        """
        _value: type = eval(value)

        if not isinstance(_value, list):
            raise TypeError(
                f'传入的值不能够被解析为list喵！而被解析为："{_value.__class__.__name__}"'
            )

        byte = 0
        if len(_value) < 8:
            _value.extend([0] * (8 - len(_value)))

        for i, bit in enumerate(_value):
            byte = Bit.write(byte, i, bit)

        data.append(byte)
        return data

    @staticmethod
    def __class_getitem__(key: int):
        return _Bits(key)


class Reader:
    """反序列化存档数据的操作类喵"""

    def __init__(self, data: Union[bytes, bytearray], pos: int = 0):
        """
        反序列化存档数据的操作类喵

        参数:
            data (bytes | bytearray): 要读取的二进制数据喵
            pos (int): 当前读写位置喵。默认为 0 喵
        """
        self.data = data
        self.pos = pos
        self.bit_read = [bytes(), False, 0]

        self.read_dict = {}

    def type_read(self, type_class) -> Any:
        """
        使用数据类型提供的read()方法进行反序列化数据喵

        参数:
            type_class (class): 定义了read()方法的数据类型喵

        返回:
            (Any): 反序列化的数据喵
        """
        if type_class == Bit:
            if not self.bit_read[1]:
                self.bit_read[0], self.pos = Byte.read(self.data, self.pos)
                self.bit_read[1] = True

            read_data = Bit.read(self.bit_read[0], self.bit_read[2])
            self.bit_read[2] += 1

        else:
            if self.bit_read[1]:
                self.bit_read[1] = False
                self.bit_read[2] = 0

            read_data, self.pos = type_class.read(self.data, self.pos)

        return read_data

    def parseStructure(self, structure) -> dict[str, Any]:
        """
        按照数据结构类定义的结构进行反序列化数据喵

        参数:
            structure (class): 数据结构类喵

        返回:
            (dict[str, Any]): 反序列化的数据喵
        """
        obj = structure()

        if not isinstance(obj, dataTypeAbstract):
            for key, type_obj in structure.__annotations__.items():
                if not __debug__:
                    print(key, type_obj)

                self.read_dict[key] = self.type_read(type_obj)

                if not __debug__:
                    print(key, getattr(obj, key))

        else:
            self.read_dict = self.type_read(obj)

        if self.remaining() == 0:
            print(
                f'结构"{obj.__class__.__name__}"读取完毕喵！剩余{self.remaining()}字节喵！'
            )
            if str(obj.__class__.__name__) == "user01":
                print(self.read_dict)

        else:
            print(
                f'结构"{obj.__class__.__name__}"尚未读取完毕喵！剩余{self.remaining()}字节喵！'
            )

        return self.read_dict

    def remaining(self) -> int:
        """
        返回剩余未反序列化的数据长度喵

        返回:
            (int): 剩余未反序列化的数据长度喵
        """
        return len(self.data) - self.pos


class Writer:
    """序列化存档数据的操作类喵"""

    def __init__(self, data: Optional[Union[bytearray, bytes]] = None):
        """
        序列化存档数据的操作类喵

        参数:
            data (bytes | bytearray | None): 若不为空，则基于此数据向后拼接序列化数据喵
        """
        if data is None:
            self.data = bytearray()

        elif isinstance(data, bytes):
            self.data = bytearray(data)

        elif isinstance(data, bytearray):
            self.data = data

        else:
            raise TypeError(f'传入的数据类型不合法喵！不应为"{type(data)}"喵！')

        self.bit_temp = [0, False, 0]

    def type_write(self, type_fc, value):
        """
        使用数据类型提供的write()方法进行序列化数据喵

        参数:
            type_class (class): 定义了write()方法的数据类型喵
            value (Any): 要序列化的数据喵
        """
        if type_fc == Bit:
            if not self.bit_temp[1]:
                self.bit_temp[0] = 0
                self.bit_temp[1] = True

            self.bit_temp[0] = Bit.write(self.bit_temp[0], self.bit_temp[2], value)
            self.bit_temp[2] += 1

        else:
            if self.bit_temp[1]:
                self.bit_temp[1] = False
                self.bit_temp[2] = 0
                self.data = Byte.write(self.data, self.bit_temp[0])

            self.data = type_fc.write(self.data, value)

    def buildStructure(self, structure, data: dict) -> bytearray:
        """
        按照数据结构类定义的结构进行反序列化数据喵

        参数:
            structure (class): 数据结构类喵

        返回:
            (dict[str, Any]): 反序列化的数据喵
        """
        obj = structure()

        if not isinstance(obj, dataTypeAbstract):
            for key, type_obj in structure.__annotations__.items():
                if not __debug__:
                    print(key, type_obj)

                self.type_write(type_obj, data[key])

                if not __debug__:
                    print(key, getattr(obj, key))

        else:
            self.type_write(obj, data)

        return self.data

    def get_data(self) -> bytearray:
        """
        返回已经序列化的数据喵

        返回:
            (bytearray): 已序列化的数据喵
        """
        return self.data


class user01:
    file_head = b"\x01"

    showPlayerId: Byte
    """右上角展示用户id喵"""

    selfIntro: String
    """自我介绍喵"""

    avatar: String
    """头像喵"""

    background: String
    """背景曲绘喵"""


class GameKey(dataTypeAbstract):
    @staticmethod
    def read(data: bytes, pos: int):
        all_keys = {}
        reader = Reader(data, pos)
        keySum = reader.type_read(VarInt)  # 总共key的数量，决定循环多少次喵

        for _ in range(keySum):  # 循环keySum次喵
            name = reader.type_read(String)  # key的名称喵
            # 总数据长度喵(不包含key的昵称喵)
            length = reader.type_read(Byte)
            one_key = all_keys[name] = {}  # 存储单个key的数据喵
            # 获取key的状态标志喵(收藏品阅读、单曲解锁、收藏品、背景、头像喵)
            one_key["type"] = str((reader.type_read(Bits[5])))

            # 用来存储该key的标记喵(长度与type中1的数量一致，每位值相同，与收藏品碎片收集有关，默认为1喵)
            flag = []
            # 因为前面已经读取了一个类型标志了，所以减一喵
            for _ in range(length - 1):
                flag_value, reader.pos = Byte.read(data, reader.pos)
                flag.append(flag_value)
            one_key["flag"] = str(flag)

        return all_keys, reader.pos

    @staticmethod
    def write(data: bytearray, value: dict):
        writer = Writer(data)

        writer.type_write(VarInt, len(value))

        for keys in value.items():
            writer.type_write(String, keys[0])
            writer.type_write(Byte, len(eval(keys[1]["flag"])) + 1)
            writer.type_write(Bits, keys[1]["type"])

            for flag in eval(keys[1]["flag"]):
                writer.type_write(Byte, flag)

        return writer.get_data()


class gameKey03:
    """
    版本号≥3.9.0喵

    新增"sideStory4BeginReadKey"和"oldScoreClearedV390"喵
    """

    file_head = b"\x03"

    keyList: GameKey
    """
    游戏中所有Key的状态值喵
    
    结构:
        type: key的状态标志喵(收藏品阅读、单曲解锁、收藏品、背景、头像喵)
        flag: key的标记喵(长度与type中1的数量一致，每位值相同，与收藏品碎片收集有关，默认为1喵)
    """

    lanotaReadKeys: Bits[6]
    """Lanota收藏品阅读进度喵(解锁倒霉蛋和船的AT喵)"""

    camelliaReadKey: Bits
    """极星卫收藏品阅读进度喵(解锁S.A.T.E.L.L.I.T.E.的AT喵)"""

    sideStory4BeginReadKey: Byte
    """解锁支线4喵"""

    oldScoreClearedV390: Byte
    """是否已清除改谱之前的成绩喵(如果为0则会清除喵)"""


class gameKey02:
    """版本号<3.9.0喵"""

    file_head = b"\x02"

    keyList: GameKey

    lanotaReadKeys: Bits[6]
    """Lanota收藏品阅读进度喵(解锁倒霉蛋和船的AT喵)"""

    camelliaReadKey: Bits
    """极星卫收藏品阅读进度喵(解锁S.A.T.E.L.L.I.T.E.的AT喵)"""


class GameRecord(dataTypeAbstract):
    @staticmethod
    def read(data: bytes, pos: int):
        all_record = {}  # 用来存储解析出来的数据喵
        diff_list: tuple = ("EZ", "HD", "IN", "AT", "Legacy")

        reader = Reader(data, pos)
        songSum: int = reader.type_read(VarInt)  # 总歌曲数目喵

        for _ in range(songSum):
            songName: str = (reader.type_read(String))[:-2]  # 歌曲名字喵
            # 数据总长度喵(不包括歌曲名字喵)
            length: int = reader.type_read(VarInt)
            end_position: int = reader.pos + length  # 单首歌数据结束字节位置喵
            unlock: int = reader.type_read(Byte)  # 每个难度解锁情况喵
            fc: int = reader.type_read(Byte)  # 每个难度fc情况喵
            song = all_record[songName] = {}  # 存储单首歌的成绩数据喵

            # 遍历每首歌的EZ、HD、IN、AT、Legacy(旧谱)难度的成绩喵
            for level in range(5):
                if Bit.read(unlock, level):  # 判断当前难度是否解锁喵
                    score: int = reader.type_read(Int)  # 读取分数喵
                    acc: float = reader.type_read(Float)  # 读取acc喵

                    song[diff_list[level]] = {  # 按难度存储进单首歌的成绩数据中喵
                        "score": score,  # 分数喵
                        "acc": acc,  # ACC喵
                        "fc": Bit.read(fc, level),  # 是否Full Combo喵(FC)
                    }

            if reader.pos != end_position:
                print(f'在读取"{songName}"的数据时发生错误喵！当前位置：{reader.pos}')
                print(f"错误喵！！！当前读取字节位置不正确喵！应为：{end_position}")

        return all_record, reader.pos

    @staticmethod
    def write(data: bytearray, value: dict):
        diff_list: dict = {"EZ": 0, "HD": 1, "IN": 2, "AT": 3, "Legacy": 4}

        writer = Writer(data)
        writer.type_write(VarInt, len(value))

        for name, song in value.items():
            writer.type_write(String, name + ".0")

            # 这行不是冗余代码啊喵！本喵这样子写是有原因的！
            writer.type_write(VarInt, len(song) * (4 + 4) + 1 + 1)
            unlock = eval(Bits.read(b"\x00", 0)[0])
            fc = eval(Bits.read(b"\x00", 0)[0])
            record_writer = Writer()
            for diff, index in diff_list.items():
                if song.get(diff) is not None:
                    unlock[index] = 1
                    record_writer.type_write(Int, song[diff]["score"])
                    record_writer.type_write(Float, song[diff]["acc"])
                    fc[index] = song[diff]["fc"]

            writer.type_write(Bits, str(unlock))
            writer.type_write(Bits, str(fc))
            writer.type_write(Byte, record_writer.get_data())

        return writer.get_data()


class Money(dataTypeAbstract):
    @staticmethod
    def read(data: bytes, pos: int):
        money = []
        for _ in range(5):
            money_value, pos = VarInt.read(data, pos)
            money.append(money_value)

        return money, pos

    @staticmethod
    def write(data: bytearray, value: list):
        for money_value in value:
            data = VarInt.write(data, money_value)

        return data


class gameProgress04:
    """
    版本号≥3.8.1喵

    新增了"flagOfSongRecordKeyTakumi"喵
    """

    file_head = b"\x04"

    isFirstRun: Bit
    """是否首次运行喵"""

    legacyChapterFinished: Bit
    """过去的章节是否完成喵"""

    alreadyShowCollectionTip: Bit
    """是否展示收藏品Tip喵"""

    alreadyShowAutoUnlockINTip: Bit
    """是否展示自动解锁IN Tip喵"""

    completed: String
    """剧情完成喵 (用于显示全部歌曲和课题模式入口喵)"""

    songUpdateInfo: VarInt

    challengeModeRank: ShortInt
    """课题分喵"""

    money: Money
    """Data值喵"""

    unlockFlagOfSpasmodic: Bits[4]
    """Spasmodic解锁喵"""

    unlockFlagOfIgallta: Bits[4]
    """Igallta解锁喵"""

    unlockFlagOfRrharil: Bits[4]
    """Rrhar'il解锁喵"""

    flagOfSongRecordKey: Bits
    """
    部分歌曲IN达到S解锁AT喵
    
    (倒霉蛋, 船, Shadow, 心之所向, inferior, DESTRUCTION 3,2,1, Distorted Fate, Cuvism)
    """

    randomVersionUnlocked: Bits[6]
    """Random切片解锁喵"""

    chapter8UnlockBegin: Bit
    """第八章入场喵"""

    chapter8UnlockSecondPhase: Bit
    """第八章第二阶段喵"""

    chapter8Passed: Bit
    """第八章通过喵"""

    chapter8SongUnlocked: Bits[6]
    """第八章各曲目解锁喵"""

    flagOfSongRecordKeyTakumi: Bits[3]
    """第四章Takumi AT解锁喵"""


class gameProgress03:
    """版本号<3.8.1喵"""

    file_head = b"\x03"

    isFirstRun: Bit
    """是否首次运行喵"""

    legacyChapterFinished: Bit
    """过去的章节是否完成喵"""

    alreadyShowCollectionTip: Bit
    """是否展示收藏品Tip喵"""

    alreadyShowAutoUnlockINTip: Bit
    """是否展示自动解锁IN Tip喵"""

    completed: String
    """剧情完成喵 (用于显示全部歌曲和课题模式入口喵)"""

    songUpdateInfo: VarInt

    challengeModeRank: ShortInt
    """课题分喵"""

    money: Money
    """Data值喵"""

    unlockFlagOfSpasmodic: Bits[4]
    """Spasmodic解锁喵"""

    unlockFlagOfIgallta: Bits[4]
    """Igallta解锁喵"""

    unlockFlagOfRrharil: Bits[4]
    """Rrhar'il解锁喵"""

    flagOfSongRecordKey: Bits
    """
    部分歌曲IN达到S解锁AT喵
    
    (倒霉蛋, 船, Shadow, 心之所向, inferior, DESTRUCTION 3,2,1, Distorted Fate, Cuvism)
    """

    randomVersionUnlocked: Bits[6]
    """Random切片解锁喵"""

    chapter8UnlockBegin: Bit
    """第八章入场喵"""

    chapter8UnlockSecondPhase: Bit
    """第八章第二阶段喵"""

    chapter8Passed: Bit
    """第八章通过喵"""

    chapter8SongUnlocked: Bits[6]
    """第八章各曲目解锁喵"""


class settings01:
    file_head = b"\x01"

    chordSupport: Bit
    """多押辅助喵"""

    fcAPIndicator: Bit
    """FC/AP指示器喵"""

    enableHitSound: Bit
    """打击音效喵"""

    lowResolutionMode: Bit
    """低分辨率模式喵"""

    deviceName: String
    """设备名喵"""

    bright: Float
    """背景亮度喵"""

    musicVolume: Float
    """音乐音量喵"""

    effectVolume: Float
    """界面音效音量喵"""

    hitSoundVolume: Float
    """打击音效音量喵"""

    soundOffset: Float
    """谱面延迟喵"""

    noteScale: Float
    """按键缩放喵"""


def getStructure(file_head: dict[str, bytes]) -> dict[str, Any]:
    """
    根据文件头获取对应结构类喵

    参数:
        file_head (dict[str, bytes]): 每个文件的文件头喵

    返回:
        (dict[str, Any]): 每个文件对应的结构类喵
    """
    structure_list = {}

    # gameKey
    if file_head.get("gameKey") == b"\x03":
        structure_list["gameKey"] = gameKey03

    elif file_head.get("gameKey") == b"\x02":
        structure_list["gameKey"] = gameKey02

    elif isinstance(file_head.get("gameKey"), bytes):
        raise ValueError(
            f'文件头不正确，可能数据结构已更新喵！不应为：{file_head.get("gameKey")}'
        )

    # gameProgress
    if file_head.get("gameProgress") == b"\x04":
        structure_list["gameProgress"] = gameProgress04

    elif file_head.get("gameProgress") == b"\x03":
        structure_list["gameProgress"] = gameProgress03

    elif isinstance(file_head.get("gameProgress"), bytes):
        raise ValueError(
            f'文件头不正确，可能数据结构已更新喵！不应为：{file_head.get("gameProgress")}'
        )

    # gameRecord
    if file_head.get("gameRecord") == b"\x01":
        structure_list["gameRecord"] = GameRecord

    elif isinstance(file_head.get("gameRecord"), bytes):
        raise ValueError(
            f'文件头不正确，可能数据结构已更新喵！不应为：{file_head.get("gameRecord")}'
        )

    # settings
    if file_head.get("settings") == b"\x01":
        structure_list["settings"] = settings01

    elif isinstance(file_head.get("settings"), bytes):
        raise ValueError(
            f'文件头不正确，可能数据结构已更新喵！不应为：{file_head.get("settings")}'
        )

    # user
    if file_head.get("user") == b"\x01":
        structure_list["user"] = user01
        print("进入user页面", structure_list["user"])

    elif isinstance(file_head.get("user"), bytes):
        raise ValueError(
            f'文件头不正确，可能数据结构已更新喵！不应为：{file_head.get("user")}'
        )

    return structure_list


def decryptSave(save_dict: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    反序列化存档原始数据喵

    参数:
        save_dict (dict[str, Any]): 存档原始数据喵(unzipSave()可得喵)

    返回:
        (dict[str, dict]): 存档反序列化数据喵
    """
    file_head = {}
    for key, value in save_dict.items():
        file_head[key] = value[0].to_bytes()

    structure_list = getStructure(file_head)

    for key, value in save_dict.items():
        save_dict[key] = decrypt(
            value[1:]
        )  # 键解密了(username) 但是值还是加密状态(b'\x01\x03KRK\x0)
        # print(f"key:{key} val:{save_dict[key]}")
        reader = Reader(save_dict[key])
        save_dict[key] = reader.parseStructure(structure_list[key])

    return save_dict


def formatSaveDict(save_dict: dict[str, dict]):
    new_save_dict = {}

    for key in ["user", "gameProgress", "settings", "gameRecord", "gameKey"]:
        if save_dict.get(key) is not None:
            new_save_dict[key] = save_dict[key]
    # print('存档文件是这个喵:', new_save_dict)
    return new_save_dict


from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QApplication,
    QStackedWidget,
    QDesktopWidget,
)
from qframelesswindow import FramelessWindow, StandardTitleBar
from PyQt5.QtCore import Qt, QUrl, QTimer, QMargins
from PyQt5.QtGui import (
    QGuiApplication,
    QDesktopServices,
    QIcon,
    QPixmap,
)
from qfluentwidgets import (
    NavigationInterface,
    NavigationItemPosition,
    FlowLayout,
    ImageLabel,
    SmoothScrollArea,
    SwitchButton,
)
from qfluentwidgets import FluentIcon as FIF
import sys
import heapq  # 大根堆算b27

from dependences.classes import *


class MainWindow(FramelessWindow):
    def __init__(self):
        super().__init__()

        self.token = ""  # 玩家的token
        self.widgets: dict[str : dict[str:Any]] = {}  # 管理每个页面的控件
        """self.widgets[页面名称][页面控件名称]=控件"""
        self.b27: tuple[float, tuple[str, str, float, float, str, str, bool]] = []
        """self.b27 = (单曲rks,(组合名称, acc,   定数, 难度, 分数, 是否fc))"""
        self.phi3: tuple[float, tuple[str, float, float, str, str, bool]] = []
        """self.phi3 = (单曲rks,(组合名称, acc,   定数, 难度, 分数, 是否fc))"""
        self.cname_to_name: dict[str, tuple[str, str, str, dict[str, str]]] = {}
        """
        self.cname_to_name[组合名称] = (
            正常名称,
            曲师名称,
            画师名称,
            {"EZ": EZ难度谱师, "HD": HD难度谱师, "IN": IN难度谱师}
        )
        """

        # 设置窗口标题
        self.setTitleBar(StandardTitleBar(self))
        self.titleBar.setTitle("PhiFilter Tool")
        self.titleBar.titleLabel.setStyleSheet(
            """
            QLabel {
                font-size: 30px;
                font-family: "Segoe UI";
            }
        """
        )
        self.setWindowTitle("PhiFilter Tool")  # 设置任务栏标题

        # 调整窗口大小和坐标
        self.resize(950, 800)
        screen = QDesktopWidget().screenGeometry()  # 获取屏幕几何信息
        # 计算居中坐标
        pos_x = (screen.width() - self.width()) // 2
        pos_y = (screen.height() - self.height()) // 2
        self.move(pos_x, pos_y)

        # 初始化
        self.widgets["basepage"] = {}
        main_layout = QHBoxLayout(self)  # 横向布局
        self.widgets["basepage"]["main_layout"] = main_layout
        main_layout.setSpacing(0)  # 控件间无间距
        main_layout.setContentsMargins(0, self.titleBar.height(), 0, 0)

        navigation_interface = NavigationInterface(self)  # 生成导航栏
        self.widgets["basepage"]["navigation_interface"] = navigation_interface
        main_layout.addWidget(navigation_interface)
        navigation_interface.setExpandWidth(200)

        content_widget = QStackedWidget(self)  # 创建一个堆叠窗口组件
        self.widgets["basepage"]["content_widget"] = content_widget
        main_layout.addWidget(content_widget, 1)

        self.init_font()
        self.generate_cname_to_name_info()
        self.init_all_pages()
        self.init_navigation()
        self.switch_to(self.home_page)

    def init_font(self):
        """初始化中英文对应字体"""
        en_font_id = QFontDatabase.addApplicationFont(EN_FONT1)
        self.en_font_family = DEFAULT_EN_FONT
        if en_font_id != -1:
            self.en_font_family = QFontDatabase.applicationFontFamilies(en_font_id)[0]

        chi_font_id = QFontDatabase.addApplicationFont(EN_FONT1)
        self.chi_font_family = DEFAULT_CN_FONT
        if chi_font_id != -1:
            self.chi_font_family = QFontDatabase.applicationFontFamilies(chi_font_id)[0]

    def generate_cname_to_name_info(self):
        """生成self.cname_to_name信息\n
        self.cname_to_name[组合名称] = (\n
        正常名称,\n
        曲师名称,\n
        画师名称,\n
        {"EZ": EZ难度谱师, "HD": HD难度谱师, "IN": IN难度谱师} )
        """
        df = pd.read_csv(
            INFO_PATH,
            sep="\t",
            header=None,
            encoding="utf-8",
            names=[
                "combine_name",
                "song_name",
                "composer",
                "drawer",
                "EZchapter",
                "HDchapter",
                "INchapter",
                "ATchapter",
                "Legendchapter",
            ],  # 手动定义所有列名
        )

        df = df.fillna("")  # 将NaN替换为空字符串
        for _, row in df.iterrows():
            combine_name = row["combine_name"]
            song_name = row["song_name"]
            composer = row["composer"]
            drawer = row["drawer"]
            EZchapter = row["EZchapter"]
            HDchapter = row["HDchapter"]
            INchapter = row["INchapter"]
            ATchapter = row["ATchapter"]
            Legendchapter = row["Legendchapter"]  # 当前版本迷宫莉莉丝有Legend难度信息
            self.cname_to_name[combine_name] = (
                song_name,
                composer,
                drawer,
                {"EZ": EZchapter, "HD": HDchapter, "IN": INchapter},
            )
            if ATchapter:  # NaN被替换为了空字符串 如果有信息就表明这首歌有AT难度
                self.cname_to_name[combine_name][3]["AT"] = ATchapter
        # print(self.cname_to_name)

    def add_sub_interface(  # 这个是抄的example的
        self,
        interface,
        icon,
        text: str,
        position=NavigationItemPosition.TOP,
        parent=None,
    ):
        content_widget: QStackedWidget = self.widgets["basepage"]["content_widget"]
        content_widget.addWidget(interface)

        navigation_interface: NavigationInterface = self.widgets["basepage"][
            "navigation_interface"
        ]
        navigation_interface.addItem(
            routeKey=interface.objectName(),
            icon=icon,
            text=text,
            onClick=lambda: self.switch_to(interface),
            position=position,
            tooltip=text,
            parentRouteKey=parent.objectName() if parent else None,
        )

    def switch_to(self, widget):
        content_widget: QStackedWidget = self.widgets["basepage"]["content_widget"]
        content_widget.setCurrentWidget(widget)

    def on_current_interface_changed(self, index):
        content_widget: QStackedWidget = self.widgets["basepage"]["content_widget"]
        widget = content_widget.widget(index)

        navigation_interface: NavigationInterface = self.widgets["basepage"][
            "navigation_interface"
        ]
        navigation_interface.setCurrentItem(widget.objectName())

    def init_all_pages(self):
        self.home_page = self.init_homepage()
        self.home_page.setObjectName("home_page")

        self.account_page = self.init_account_page()
        self.account_page.setObjectName("account_page")

        self.place_b27_phi3_page = self.init_place_b27_phi3_page()
        self.place_b27_phi3_page.setObjectName("place_b27_phi3_page")

        self.search_page = self.init_search_page()
        self.search_page.setObjectName("search_page")

        self.edit_info_page = self.init_edit_info_page()
        self.edit_info_page.setObjectName("edit_info_page")

    def init_navigation(self):
        """初始化左侧导航栏"""
        navigation_interface: NavigationInterface = self.widgets["basepage"][
            "navigation_interface"
        ]

        self.add_sub_interface(
            self.home_page, FIF.HOME, "主页", NavigationItemPosition.TOP
        )
        self.add_sub_interface(
            self.place_b27_phi3_page, FIF.ALBUM, "rks组成页", parent=self.home_page
        )
        navigation_interface.addSeparator()

        account_icon = QIcon(
            ICON_PREPATH + "account_icon.png"
        )  # 推荐 32x32 或 48x48 像素
        self.add_sub_interface(
            self.account_page, account_icon, "账号管理", NavigationItemPosition.BOTTOM
        )

        search_icon = QIcon(
            ICON_PREPATH + "search_icon.png"
        )  # 推荐 32x32 或 48x48 像素
        self.add_sub_interface(
            self.search_page, search_icon, "搜索歌曲", NavigationItemPosition.TOP
        )

        self.add_sub_interface(
            self.edit_info_page,
            FIF.EDIT,
            "编辑歌曲相关信息",
            NavigationItemPosition.TOP,
        )

        # 页面栈
        content_widget: QStackedWidget = self.widgets["basepage"]["content_widget"]
        content_widget.currentChanged.connect(self.on_current_interface_changed)
        content_widget.setCurrentIndex(1)

    def to_github(self):
        github_url = QUrl("https://github.com/lightbluegit/rhythmgame_database")
        QDesktopServices.openUrl(github_url)

    # -------------- 主页/快捷工具 ----------------
    def init_homepage(self) -> QWidget:
        """初始化主页 有生成rks组成等简单功能按钮"""
        self.widgets["home_page"] = {}
        widget = QWidget()
        self.widgets["home_page"]["widget"] = widget
        widget.setContentsMargins(20, 20, 0, 0)

        layout = QVBoxLayout(widget)  # 纵向布局
        self.widgets["home_page"]["layout"] = layout
        widget.setLayout(layout)

        generate_b27_phi3_btn = button("生成rks组成", iconpath=GENERATE_RKS_ICON_PATH)
        self.widgets["home_page"]["generate_b27_phi3_btn"] = generate_b27_phi3_btn
        generate_b27_phi3_btn.set_icon_size(32, 32)
        generate_b27_phi3_btn.bind_click_func(self.generate_b27_phi3)
        layout.addWidget(generate_b27_phi3_btn)
        layout.addStretch(1)  # 保证按钮顶到最上面

        # 测试用的控件
        # s1 = song_info_card(
        #     ILLUSTRATION_PREPATH + "Luminescence.米虾Fomiki初云CLoudie.png",
        #     "Eltawiholu givyf kgtuc hblj;nkolm xc,olsac ascx",
        #     "11.1111",
        #     "22.222",
        #     "33.3",
        #     "EZ",
        #     True,
        #     int("1000000"),
        #     22,
        #     "百九十八 越写越花",
        #     combine_name="Luminescence.米虾Fomiki初云CLoudie",
        # )
        # s1.right_func = self.link_and_show  # 重要!
        # layout.addWidget(s1)

        return widget

    def generate_b27_phi3(self):
        """计算rks组成"""
        # 暂时略过
        with PhigrosCloud(self.token) as cloud:
            # 获取玩家summary喵
            summary = cloud.getSummary()
            # print('summary是',summary)
            # 获取并解析存档喵
            save_data = cloud.getSave(summary["url"], summary["checksum"])
            save_dict = unzipSave(save_data)
            # print("save_dict是这个",save_dict)
            save_dict = decryptSave(save_dict)
            # print("最后得到的是这个东西喵",save_dict)
            save_dict = formatSaveDict(save_dict)
            # print("save_dict是这个", save_dict)

            df = pd.read_csv(
                DIFFICULTY_PATH,
                sep="\t",
                header=None,
                encoding="utf-8",
                names=["song_name", "EZ", "HD", "IN", "AT"],  # 手动定义所有列名
            )

            # 处理缺失值（如果某些行不足5列）
            df = df.fillna("")  # 将NaN替换为空字符串+
            # 转换为目标字典格式

            result: dict[str, dict[str, str]] = {}
            """result[组合名称]={'EZ':EZ定数, 'HD':HD定数, 'IN':IN定数, 'AT':AT定数}"""

            for _, row in df.iterrows():
                name = row["song_name"]  # 使用iloc获取第一列（名称）
                diff_map: dict[str, str] = {
                    "EZ": row["EZ"],
                    "HD": row["HD"],
                    "IN": row["IN"],
                }
                diff_AT = row["AT"]
                if diff_AT:
                    diff_map["AT"] = row["AT"]

                result[name] = diff_map
            # print(result)

            self.b27 = []
            heapq.heapify(self.b27)  # 维护大根堆 只需要固定数量的格子 省空间

            self.phi3 = []
            heapq.heapify(self.phi3)
            for combine_name, all_diff_dic in save_dict["gameRecord"].items():
                for diffi, items in all_diff_dic.items():
                    if diffi == "Legacy":
                        continue
                    score = items["score"]
                    acc = items["acc"]
                    is_fc = items["fc"]
                    level = float(result[combine_name][diffi])
                    singal_rks = round(level * pow((acc - 55) / 45, 2), 4)
                    acc = round(float(items["acc"]), 3)

                    if len(self.b27) < 27:
                        heapq.heappush(
                            self.b27,
                            (
                                singal_rks,
                                (combine_name, acc, level, diffi, score, is_fc),
                            ),
                        )
                    else:
                        heapq.heappushpop(
                            self.b27,
                            (
                                singal_rks,
                                (combine_name, acc, level, diffi, score, is_fc),
                            ),
                        )

                    if int(score) == int(1e6):  # AP了
                        if len(self.phi3) < 3:
                            heapq.heappush(
                                self.phi3,
                                (
                                    singal_rks,
                                    (combine_name, acc, level, diffi, score, is_fc),
                                ),
                            )
                        else:
                            heapq.heappushpop(
                                self.phi3,
                                (
                                    singal_rks,
                                    (combine_name, acc, level, diffi, score, is_fc),
                                ),
                            )

            self.place_b27_phi3()

    def place_b27_phi3(self):
        """布局rks组成"""
        self.widgets["place_b27_phi3_page"]["b27_widgets"] = []
        layout: QVBoxLayout = self.widgets["place_b27_phi3_page"]["main_layout"]

        phi3_folder = folder("phi3:", True)
        self.widgets["place_b27_phi3_page"]["phi3_folder"] = phi3_folder
        layout.addWidget(phi3_folder, 1)

        for idx, bi in enumerate(self.phi3):
            singal_rks, other = bi
            combine_name, acc, level, diff, score, is_fc = other

            # score_level = self.get_score_level(int(score), is_fc)
            (song_name, composer, drawer, chapter_dic) = self.cname_to_name[
                combine_name
            ]
            phi3_cardi = song_info_card(
                ILLUSTRATION_PREPATH + combine_name + ".png",
                song_name,
                singal_rks,
                acc,
                level,
                diff,
                is_fc,
                int(score),
                idx + 1,
                composer,
                chapter_dic[diff],
                drawer,
                False,
                combine_name,
            )
            phi3_cardi.right_func = self.link_and_show
            selected_group = GROUP_INFO[combine_name].split("`")
            # print(f'当前歌曲已经存在的分组是:{selected_group}')

            selected_tag = TAG_INFO[combine_name].split("`")
            # print(f'当前歌曲已经存在的标签是:{selected_tag}')

            now_comment = COMMENT_INFO[combine_name][diff]
            phi3_cardi.set_edited_info(selected_group, selected_tag, now_comment)
            phi3_folder.add_widget(phi3_cardi)
        # print("phi3已布局完成!")

        b27_folder = folder("b27:", True)
        self.widgets["place_b27_phi3_page"]["b27_folder"] = b27_folder
        layout.addWidget(b27_folder, 3)
        for idx, bi in enumerate(self.b27):
            singal_rks, other = bi
            combine_name, acc, level, diff, score, is_fc = other
            # score_level = self.get_score_level(int(score), is_fc)

            (song_name, composer, drawer, chapter_dic) = self.cname_to_name[
                combine_name
            ]
            b27_cardi = song_info_card(
                ILLUSTRATION_PREPATH + combine_name + ".png",
                song_name,
                singal_rks,
                acc,
                level,
                diff,
                is_fc,
                int(score),
                idx + 1,
                composer,
                chapter_dic[diff],
                drawer,
                False,
                combine_name,
            )
            b27_cardi.right_func = self.link_and_show
            selected_group = GROUP_INFO[combine_name].split("`")
            # print(f'当前歌曲已经存在的分组是:{selected_group}')

            selected_tag = TAG_INFO[combine_name].split("`")
            # print(f'当前歌曲已经存在的分组是:{selected_tag}')

            now_comment = COMMENT_INFO[combine_name][diff]
            b27_cardi.set_edited_info(selected_group, selected_tag, now_comment)
            b27_folder.add_widget(b27_cardi)
        # print("b27已布局完成!")
        self.switch_to(self.place_b27_phi3_page)

    def init_place_b27_phi3_page(self) -> QWidget:
        """初始化rks组成页面"""
        self.widgets["place_b27_phi3_page"] = {}

        widget = QWidget()
        self.widgets["place_b27_phi3_page"]["widget"] = widget

        main_layout = QVBoxLayout(widget)
        self.widgets["place_b27_phi3_page"]["main_layout"] = main_layout
        main_layout.setContentsMargins(5, 0, 0, 0)
        main_layout.setSpacing(10)

        return widget

    # ---------------- 添加简评 tag 分组 -----------------
    def init_edit_info_page(self) -> QWidget:
        """初始化添加简评 tag 分组页面"""
        self.widgets["edit_info_page"] = {}

        widget = QWidget()
        self.widgets["edit_info_page"]["widget"] = widget

        main_layout = QHBoxLayout(widget)  # 横向布局
        widget.setLayout(main_layout)
        self.widgets["edit_info_page"]["main_layout"] = main_layout

        # ---------------------- 左侧 展示页面 --------------------
        display_widget = QWidget()
        self.widgets["edit_info_page"]["display_widget"] = display_widget
        main_layout.addWidget(display_widget)

        display_layout = QVBoxLayout(display_widget)  # 纵向布局
        self.widgets["edit_info_page"]["display_layout"] = display_layout
        display_widget.setLayout(display_layout)

        example_song = song_info_card(  # 占位
            ILLUSTRATION_PREPATH + "introduction.png",
            "introduction",
            "00.0000",
            "00.000%",
            "00.0",
            "EZ",
            True,
            1000000,
            0,
            "曲师名称",
            "谱师名称",
            "画师名称",
            True,
            "introduction",
        )
        self.widgets["edit_info_page"]["song_info_card"] = example_song
        display_layout.addWidget(example_song)
        example_song.set_edited_info(["分组1、分组2"], ["此处为标签"], "此处为简评内容")

        # ---------------------- 右侧 编辑页面 --------------------
        edit_widget = QWidget()
        self.widgets["edit_info_page"]["edit_widget"] = edit_widget
        main_layout.addWidget(edit_widget)

        edit_layout = QVBoxLayout(edit_widget)  # 纵向布局
        self.widgets["edit_info_page"]["edit_layout"] = edit_layout
        edit_widget.setLayout(edit_layout)

        # --- 分组控件布局 ---
        group_widget = QWidget()
        self.widgets["edit_info_page"]["group_widget"] = group_widget
        edit_layout.addWidget(group_widget)

        group_layout = QHBoxLayout(group_widget)
        self.widgets["edit_info_page"]["group_layout"] = group_layout
        group_widget.setLayout(group_layout)

        group_label = label("分组:")
        self.widgets["edit_info_page"]["group_label"] = group_label
        group_layout.addWidget(group_label)

        group_ccb = CheckableComboBox()  # ccb!
        self.widgets["edit_info_page"]["group_ccb"] = group_ccb
        group_ccb.addItems(used_group)  # 放各种用户创建的分组(在 contests 文件里的变量)
        group_layout.addWidget(group_ccb)

        # --- 标签控件布局 ---
        tag_widget = QWidget()
        self.widgets["edit_info_page"]["tag_widget"] = tag_widget
        edit_layout.addWidget(tag_widget)

        tag_layout = QHBoxLayout(tag_widget)
        self.widgets["edit_info_page"]["tag_layout"] = tag_layout
        tag_widget.setLayout(tag_layout)

        tag_label = label("标签:")
        self.widgets["edit_info_page"]["tag_label"] = tag_label
        tag_layout.addWidget(tag_label)

        tag_ccb = CheckableComboBox()
        self.widgets["edit_info_page"]["tag_ccb"] = tag_ccb
        tag_ccb.addItems(used_tag)  # 放各种用户创建的标签
        tag_layout.addWidget(tag_ccb)

        comment_label = multiline_text()
        self.widgets["edit_info_page"]["comment_label"] = comment_label
        comment_label.setStyleSheet("""{font-size: 28px;}""")
        edit_layout.addWidget(comment_label)

        # --- 确认按钮 ---
        confirm_btn = button("保存更改", iconpath=SAVE_ICON_PATH)
        self.widgets["edit_info_page"]["confirm_btn"] = confirm_btn
        confirm_btn.set_icon_size(30, 30)
        confirm_btn.bind_click_func(self.save_user_edit)
        edit_layout.addWidget(confirm_btn)

        return widget

    def link_and_show(self, info_card: song_info_card):
        """在用户右键卡片后跳转编辑该歌曲的页面"""
        info_card_copy = info_card.copy()  # .copy 防止破坏掉原来的卡片
        self.switch_to(self.edit_info_page)  # 跳转

        # 删掉之前的卡片
        if isinstance(self.widgets["edit_info_page"]["song_info_card"], song_info_card):
            self.widgets["edit_info_page"]["song_info_card"].deleteLater()
        self.widgets["edit_info_page"]["song_info_card"] = info_card_copy

        layout: QVBoxLayout = self.widgets["edit_info_page"]["display_layout"]
        layout.addWidget(info_card_copy)

        # -------- 更新该歌曲的分组 标签 简评 ------------
        group_ccb: CheckableComboBox = self.widgets["edit_info_page"]["group_ccb"]
        selected_group = GROUP_INFO[info_card_copy.combine_name].split("`")
        # print(f'当前歌曲已经存在的分组是:{selected_group}')
        group_ccb.setSelectedItems(selected_group)

        tag_ccb: CheckableComboBox = self.widgets["edit_info_page"]["tag_ccb"]
        selected_tag = TAG_INFO[info_card_copy.combine_name].split("`")
        # print(f'当前歌曲已经存在的分组是:{selected_tag}')
        tag_ccb.setSelectedItems(selected_tag)

        comment_label: multiline_text = self.widgets["edit_info_page"]["comment_label"]
        now_comment = COMMENT_INFO[info_card_copy.combine_name][info_card.diff]
        comment_label.set_text(now_comment)

        info_card_copy.set_edited_info(selected_group, selected_tag, now_comment)

    def save_user_edit(self):
        now_song_info_card: song_info_card = self.widgets["edit_info_page"][
            "song_info_card"
        ]
        song_combine_name = now_song_info_card.combine_name
        diff = now_song_info_card.diff
        # print(f'当前歌曲难度{diff}')
        new_group = "`".join(
            self.widgets["edit_info_page"]["group_ccb"].selectedItems()
        )
        new_tag = "`".join(self.widgets["edit_info_page"]["tag_ccb"].selectedItems())
        new_comment = self.widgets["edit_info_page"]["comment_label"].get_plain_text()
        # print(f"老分组{GROUP_INFO[song_combine_name]}新分组:{new_group}")
        # print(f"老标签{TAG_INFO[song_combine_name]}新标签:{new_tag}")

        # ----- 更改分组信息 -----
        df = pd.read_csv(
            GROUP_PATH,
            sep=",",
            header=None,
            encoding="utf-8",
            names=["combine_name", "group"],  # 手动定义所有列名
            index_col=0,
        )
        df = df.fillna("")  # 将NaN替换为空字符串
        GROUP_INFO[song_combine_name] = new_group  # 更改当前存储的信息
        df.at[song_combine_name, "group"] = new_group  # 更改数据库里的信息
        df.to_csv(GROUP_PATH, header=False, encoding="utf-8", index=True)

        # ----- 更改标签信息 -----
        df = pd.read_csv(
            TAG_PATH,
            sep=",",
            header=None,
            encoding="utf-8",
            names=["combine_name", "tag"],  # 手动定义所有列名
            index_col=0,
        )
        df = df.fillna("")
        TAG_INFO[song_combine_name] = new_tag
        df.at[song_combine_name, "tag"] = new_tag
        df.to_csv(TAG_PATH, header=False, encoding="utf-8", index=True)

        # ----- 更改简评信息 -----
        df = pd.read_csv(
            COMMENT_PATH,
            sep=",",
            header=None,
            encoding="utf-8",
            names=[
                "combine_name",
                "EZ_comment",
                "HD_comment",
                "IN_comment",
                "AT_comment",
            ],  # 手动定义所有列名
            index_col=0,
        )
        df = df.fillna("")
        COMMENT_INFO[song_combine_name] = new_comment
        df.at[song_combine_name, f"{diff}_comment"] = new_comment
        df.to_csv(COMMENT_PATH, header=False, encoding="utf-8", index=True)

        now_song_info_card.set_edited_info(
            new_group.split("`"), new_tag.split("`"), new_comment
        )  # 同步更新展示部分的信息

    # ----------------- 数据筛选 --------------------------
    def init_search_page(self) -> QWidget:
        self.widgets["search_page"] = {}

        widget = QWidget()
        self.widgets["search_page"]["widget"] = widget

        main_layout = QVBoxLayout(widget)
        self.widgets["search_page"]["main_layout"] = main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  # 筛选条件部分和结果展示部分合在一起就行 不设置间隔了

        # ------------------- 筛选条件部分 ----------------
        filter_part_widget = QWidget()
        self.widgets["search_page"]["filter_part_widget"] = filter_part_widget
        filter_part_widget.setMaximumHeight(220)
        main_layout.addWidget(filter_part_widget, 2)

        filter_part_layout = QVBoxLayout(filter_part_widget)
        self.widgets["search_page"]["filter_part_layout"] = filter_part_layout
        filter_part_layout.setContentsMargins(0, 0, 0, 0)
        filter_part_layout.setSpacing(0)

        # ------ 筛选项布局部分 -------
        # 这里可能会新建出一堆筛选项 给个滚动布局控制一下大小
        scroll_area = SmoothScrollArea()
        self.widgets["search_page"]["scroll_area"] = scroll_area
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea{background: transparent; border: none}")
        scroll_area.setMaximumHeight(130)
        filter_part_widget.setStyleSheet("QWidget{background: transparent}")
        filter_part_layout.setSpacing(0)
        filter_part_layout.addWidget(scroll_area)

        scroll_content_widget = QWidget()
        self.widgets["search_page"]["scroll_content_widget"] = scroll_content_widget
        flow_layout = FlowLayout(scroll_content_widget)  # 使用流式布局
        self.widgets["search_page"]["flow_layout"] = flow_layout
        flow_layout.setSpacing(0)
        flow_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area.setWidget(scroll_content_widget)

        # 设置滚动区域的内容
        filter_obj_list: list[filter_obj] = []
        self.widgets["search_page"]["filter_obj_list"] = filter_obj_list
        filter_elm = filter_obj(0, filter_obj_list, flow_layout)
        # 逻辑链接部分 [&&, ||, 无] 选择
        filter_elm.logical_cbb = combobox(
            ["", "并且(与)", "或者(或)"],
            "",
            {
                "max_width": "90",
                "min_width": "90",
                "min_height": 35,
                "max_height": 35,
                "font_size": 20,
            },
        )
        filter_elm.logical_cbb.setContentsMargins(0, 0, 0, 0)
        filter_elm.main_layout.addWidget(filter_elm.logical_cbb)
        filter_obj_list.append(filter_elm)
        filter_elm.setContentsMargins(0, 0, 0, 0)
        flow_layout.addWidget(filter_elm)

        # ------ 下方的筛选按钮布局部分 -------
        filter_confirm_widget = QWidget()
        filter_confirm_widget.setMaximumHeight(40)
        self.widgets["search_page"]["filter_confirm_widget"] = filter_confirm_widget
        filter_part_layout.addWidget(filter_confirm_widget)

        filter_confirm_layout = QHBoxLayout(filter_confirm_widget)
        self.widgets["search_page"]["filter_confirm_layout"] = filter_confirm_layout
        filter_confirm_layout.setContentsMargins(0, 0, 0, 0)
        filter_confirm_layout.setSpacing(5)

        filter_confirm_btn_style = {"min_height": 45, "max_height": 45, "font_size": 28}
        filter_from_all_song_btn = button(
            "从所有歌曲中筛一遍", filter_confirm_btn_style, FILTER_ICON_PATH
        )
        self.widgets["search_page"][
            "filter_from_all_song_btn"
        ] = filter_from_all_song_btn
        filter_from_all_song_btn.set_icon_size(30, 30)
        self.widgets["search_page"][
            "filter_from_all_song_btn"
        ] = filter_from_all_song_btn
        filter_from_all_song_btn.bind_click_func(self.filter_from_all_song)
        filter_confirm_layout.addWidget(filter_from_all_song_btn)

        filter_from_previous_song_btn = button(
            "从结果中继续筛选", filter_confirm_btn_style, FILTER_AGAIN_ICON_PATH
        )
        self.widgets["search_page"][
            "filter_from_previous_song_btn"
        ] = filter_from_previous_song_btn
        filter_from_previous_song_btn.set_icon_size(30, 30)
        self.widgets["search_page"][
            "filter_from_previous_song_btn"
        ] = filter_from_previous_song_btn
        filter_from_previous_song_btn.bind_click_func(self.filter_from_previous_song)
        filter_confirm_layout.addWidget(filter_from_previous_song_btn)

        # ------------------- 筛选结果布局部分 ----------------
        result_widget = QWidget()
        self.widgets["search_page"]["result_widget"] = result_widget
        result_widget.setStyleSheet("""background-color: #DCDCDC;""")
        main_layout.addWidget(result_widget, 3)

        result_layout = QVBoxLayout(result_widget)
        self.widgets["search_page"]["result_layout"] = result_layout
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(0)

        # ---------------- 上层 分组依据 ------------
        group_widget = QWidget()
        self.widgets["search_page"]["group_widget"] = group_widget
        result_layout.addWidget(group_widget)

        group_widget_layout = QHBoxLayout(group_widget)
        self.widgets["search_page"]["group_widget_layout"] = group_widget_layout
        group_widget_layout.setContentsMargins(0, 0, 20, 0)

        page_change_btn_style = {
            "max_width": 120,
            "min_width": 120,
            "min_height": 40,
            "max_height": 40,
            "font_size": 30,
        }
        reset_page_btn = button("重置", page_change_btn_style, RESET_PATH)
        self.widgets["search_page"]["reset_page_btn"] = reset_page_btn
        reset_page_btn.bind_click_func(self.reset_page)
        group_widget_layout.addWidget(reset_page_btn)

        sort_result_reverse_btn = SwitchButton()
        self.widgets["search_page"]["sort_result_reverse_btn"] = sort_result_reverse_btn
        sort_result_reverse_btn.setOffText("当前:从小到大")
        sort_result_reverse_btn.setOnText("当前:从大到小")
        sort_result_reverse_btn.setChecked(True)
        sort_result_reverse_btn.setStyleSheet(get_switch_button_style())
        sort_result_reverse_btn.label.setStyleSheet(
            """
            font-size: 26px;
            font-family: "楷体";
            """
        )
        sort_result_reverse_btn.checkedChanged.connect(self.place_record)
        group_widget_layout.addStretch(1)
        group_widget_layout.addWidget(sort_result_reverse_btn)  # 右侧控件

        group_by_style = {
            "min_height": 24,
            "max_height": 35,
            "max_width": 80,
            "min_width": 80,
        }
        group_by_hint_style = {
            "font_size": 26,
            "min_width": 110,
            "max_width": 110,
        }
        sort_by_list = ["无", "acc", "单曲rks", "得分", "定数"]
        sort_by = combobox(
            sort_by_list, "排序依据", group_by_style, group_by_hint_style
        )
        self.widgets["search_page"]["sort_by"] = sort_by
        sort_by.bind_react_click_func(self.place_record)
        group_widget_layout.addWidget(sort_by)  # 右侧控件

        group_by_list = [
            "无",
            "曲名",
            "曲师",
            "谱师",
            "画师",
            "难度",
            "评级",
            "分组",
            "标签",
        ]
        group_by = combobox(
            group_by_list, "分组依据", group_by_style, group_by_hint_style
        )
        self.widgets["search_page"]["group_by"] = group_by
        group_by.bind_react_click_func(self.place_record)
        group_widget_layout.addWidget(group_by)  # 右侧控件

        # ----------------- 中层 歌曲布局 ----------------
        result_display_widget = QWidget()
        self.widgets["search_page"]["result_display_widget"] = result_display_widget
        result_layout.addWidget(result_display_widget, 7)

        result_display_layout = QHBoxLayout(result_display_widget)
        self.widgets["search_page"]["result_display_layout"] = result_display_layout
        result_display_layout.setContentsMargins(5, 5, 5, 5)

        result_display_scroll_area = SmoothScrollArea()
        self.widgets["search_page"][
            "result_display_scroll_area"
        ] = result_display_scroll_area
        result_display_scroll_area.setWidgetResizable(True)
        result_display_scroll_area.setStyleSheet(
            "QScrollArea{background: transparent; border: none}"
        )
        result_display_widget.setStyleSheet("QWidget{background: transparent}")
        result_display_layout.addWidget(result_display_scroll_area)
        result_display_layout.setSpacing(0)

        scroll_content_widget = QWidget()
        self.widgets["search_page"]["scroll_content_widget"] = scroll_content_widget

        result_display_flow_layout = FlowLayout(scroll_content_widget)  # 使用流式布局
        self.widgets["search_page"][
            "result_display_flow_layout"
        ] = result_display_flow_layout
        result_display_flow_layout.setSpacing(0)
        result_display_flow_layout.setContentsMargins(0, 0, 0, 0)
        result_display_scroll_area.setWidget(scroll_content_widget)

        self.widgets["search_page"]["song_cards"] = []
        return widget

    def filter_from_all_song(self):
        with PhigrosCloud(self.token) as cloud:
            # 获取玩家summary喵
            summary = cloud.getSummary()
            # print(summary)
            # 获取并解析存档喵
            save_data = cloud.getSave(summary["url"], summary["checksum"])
            save_dict = unzipSave(save_data)
            # print("最后得到的是这个东西喵",save_dict)
            save_dict = decryptSave(save_dict)
            # print("最后得到的是这个东西喵",save_dict)
            save_dict = formatSaveDict(save_dict)
            # print("最后得到的是这个东西喵", save_dict)

            df = pd.read_csv(
                DIFFICULTY_PATH,
                sep="\t",
                header=None,
                encoding="utf-8",
                names=["song_name", "EZ", "HD", "IN", "AT"],  # 手动定义所有列名
            )

            # 处理缺失值（如果某些行不足5列）
            df = df.fillna("")  # 将NaN替换为空字符串+
            # 转换为目标字典格式
            result = {}
            for _, row in df.iterrows():
                name = row.iloc[0]  # 使用iloc获取第一列（名称）
                diffs = [x for x in row.iloc[1:] if x != ""]  # 使用iloc获取后续列
                result[name] = diffs
            # print(result)

            all_song_info = []
            diff_map = {"EZ": 0, "HD": 1, "IN": 2, "AT": 3}
            for combine_name, all_diff_dic in save_dict["gameRecord"].items():
                for diffi, items in all_diff_dic.items():
                    if diffi == "Legacy":
                        continue
                    score = items["score"]
                    acc = items["acc"]
                    is_fc = items["fc"]
                    level = 0
                    try:
                        level = float(result[combine_name][diff_map[diffi]])
                    except:
                        print(combine_name, diffi)
                    singal_rks = round(level * pow((acc - 55) / 45, 2), 4)
                    acc = round(float(items["acc"]), 3)
                    all_song_info.append(
                        (combine_name, diffi, score, acc, level, is_fc, singal_rks)
                    )

        filter_obj_list: list[filter_obj] = self.widgets["search_page"][
            "filter_obj_list"
        ]
        logical_link = filter_obj_list[0].logical_cbb.get_content()
        is_first = True
        self.filter_result = set()
        for filter_obji in filter_obj_list:
            conditioni = filter_obji.get_all_condition()
            # print(conditioni)
            if conditioni is None:
                return
            if not logical_link and len(filter_obj_list) > 1:
                print(f"逻辑链接不对啊!有好多个控件但是怎么逻辑是空呢?")
                return
            if len(filter_obj_list) == 1:  # 强制置空
                logical_link = ""

            if logical_link == "并且(与)":  # 与 &&
                if is_first:
                    self.filter_result = set(all_song_info)
                    is_first = False
                result_list = self.filte_with_condition(self.filter_result, conditioni)
                self.filter_result = set(
                    result_list
                )  # && 的参数传入的就是要被筛选的部分 会删除掉一些东西 直接覆盖就好
            else:  # 空 或 ||
                if is_first:
                    is_first = False
                result_list = self.filte_with_condition(all_song_info, conditioni)
                for resulti in result_list:
                    self.filter_result.add(resulti)  # || 运算只会加入其他东西
        # for i in self.filter_result:
        #     print(i[0], " ", i[1])
        self.place_record()

    def filte_with_condition(self, data, condition):
        (attribution, limit, limit_val) = condition
        print(f"筛选条件:{condition}")
        result = []
        self.cname_to_name  # {combine_name:(正常名称, 曲师名称)}
        if attribution in (
            "曲名",
            "曲师",
            "谱师",
            "画师",
            "标签",
            "分组",
            "简评",
        ):  # 名称相关的部分统一去掉空格并且小写(空格跟大写位置真记不清吧)
            limit_val = limit_val.replace(
                " ", ""
            ).lower()  # 可能是自己输入的 也可能是直接选择的
        for songi in data:
            (combine_name, diffi, score, acc, level, is_fc, singal_rks) = songi
            song_name, composer, *_ = self.cname_to_name[combine_name]
            groups: list[str] = GROUP_INFO[combine_name].split("`")
            tags: list[str] = TAG_INFO[combine_name].split("`")
            comments: str = COMMENT_INFO[combine_name][diffi]
            if attribution == "acc":
                if limit == "大于" and acc > float(limit_val):  # 合法性判断
                    result.append(songi)
                elif limit == "大于等于" and acc >= float(limit_val):
                    result.append(songi)
                elif limit == "小于" and acc < float(limit_val):
                    result.append(songi)
                elif limit == "小于等于" and acc <= float(limit_val):
                    result.append(songi)
                elif limit == "等于" and acc == float(limit_val):
                    result.append(songi)
                elif limit == "不等于" and acc != float(limit_val):
                    result.append(songi)

            elif attribution == "单曲rks":
                if limit == "大于" and singal_rks > float(limit_val):  # 合法性判断
                    result.append(songi)
                elif limit == "大于等于" and singal_rks >= float(limit_val):
                    result.append(songi)
                elif limit == "小于" and singal_rks < float(limit_val):
                    result.append(songi)
                elif limit == "小于等于" and singal_rks <= float(limit_val):
                    result.append(songi)
                elif limit == "等于" and singal_rks == float(limit_val):
                    result.append(songi)
                elif limit == "不等于" and singal_rks != float(limit_val):
                    result.append(songi)

            elif attribution == "得分":
                if limit == "大于" and score > int(limit_val):  # 合法性判断
                    result.append(songi)
                elif limit == "大于等于" and score >= int(limit_val):
                    result.append(songi)
                elif limit == "小于" and score < int(limit_val):
                    result.append(songi)
                elif limit == "小于等于" and score <= int(limit_val):
                    result.append(songi)
                elif limit == "等于" and score == int(limit_val):
                    result.append(songi)
                elif limit == "不等于" and score != int(limit_val):
                    result.append(songi)

            elif attribution == "定数":
                if limit == "大于" and level > float(limit_val):  # 合法性判断
                    result.append(songi)
                elif limit == "大于等于" and level >= float(limit_val):
                    result.append(songi)
                elif limit == "小于" and level < float(limit_val):
                    result.append(songi)
                elif limit == "小于等于" and level <= float(limit_val):
                    result.append(songi)
                elif limit == "等于" and level == float(limit_val):
                    result.append(songi)
                elif limit == "不等于" and level != float(limit_val):
                    result.append(songi)

            elif attribution == "评级":  # ["AP", "FC", "V", "S", "A", "B", "C", "F"]
                score_level = get_score_level(int(score), is_fc).value
                if limit == "等于" and score_level == limit_val:
                    result.append(songi)
                elif limit == "不等于" and score_level != limit_val:
                    result.append(songi)
                elif limit == "包含" and limit_val in score_level:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in score_level:
                    result.append(songi)

            elif attribution == "难度":
                if limit == "等于" and diffi == limit_val:
                    result.append(songi)
                elif limit == "不等于" and diffi != limit_val:
                    result.append(songi)
                elif limit == "包含" and limit_val in diffi:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in diffi:
                    result.append(songi)

            elif attribution == "曲名":
                song_name = song_name.replace(
                    " ", ""
                ).lower()  # 从combine_name那找到的对应名称 小写方便匹配
                if limit == "等于" and song_name == limit_val:
                    result.append(songi)
                elif limit == "不等于" and song_name != limit_val:
                    result.append(songi)
                elif limit == "包含" and limit_val in song_name:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in song_name:
                    result.append(songi)

            elif attribution == "曲师":
                if limit == "等于" and composer == limit_val:
                    result.append(songi)
                elif limit == "不等于" and composer != limit_val:
                    result.append(songi)
                elif limit == "包含" and limit_val in composer:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in composer:
                    result.append(songi)

            elif attribution == "谱师":
                if limit == "等于" and diffi == limit_val:
                    result.append(songi)
                elif limit == "不等于" and diffi != limit_val:
                    result.append(songi)
                elif limit == "包含" and limit_val in diffi:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in diffi:
                    result.append(songi)

            elif attribution == "画师":
                if limit == "等于" and diffi == limit_val:
                    result.append(songi)
                elif limit == "不等于" and diffi != limit_val:
                    result.append(songi)
                elif limit == "包含" and limit_val in diffi:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in diffi:
                    result.append(songi)

            elif attribution == "分组":
                if limit == "包含" and limit_val in groups:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in groups:
                    result.append(songi)

            elif attribution == "标签":
                if limit == "包含" and limit_val in tags:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in tags:
                    result.append(songi)

            elif attribution == "简评":
                if limit == "包含" and limit_val in comments:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in comments:
                    result.append(songi)

        # for i in result:
        #     print(i[0] + i[1])
        return result

    def filter_from_previous_song(self):
        if not hasattr(self, "filter_result"):
            print("要先全局筛选一遍才可以从结果中继续筛选喵")
            return
        print("进入筛选喵")
        filter_obj_list = self.widgets["search_page"]["filter_obj_list"]
        logical_link = filter_obj_list[0].logical_cbb.get_content()
        # self.filter_result
        # print(f"逻辑{logical_link}")
        filter_result_copy = self.filter_result
        is_first = True
        for filter_obji in filter_obj_list:
            conditioni = filter_obji.get_all_condition()
            print(conditioni)
            if not logical_link and len(filter_obj_list) > 1:
                print(f"逻辑链接不对啊!有好多个控件但是怎么逻辑是空呢?")
                return
            if len(filter_obj_list) == 1:  # 强制置空
                logical_link = ""
            if logical_link == "并且(与)":  # 与 &&
                self.filter_result = set(
                    self.filte_with_condition(self.filter_result, conditioni)
                )  # && 的参数传入的就是要被筛选的部分 会删除掉一些东西 直接覆盖就好
            else:  # 空 或 ||
                if is_first:
                    self.filter_result = set()
                    is_first = False
                result_list = self.filte_with_condition(filter_result_copy, conditioni)
                print("结果", result_list)
                for resulti in result_list:
                    self.filter_result.add(resulti)  # || 运算只会加入其他东西
        # for i in self.filter_result:
        #     print(i[0], " ", i[1])
        self.place_record()

    def reset_page(self):
        filter_obj_list: list[filter_obj] = self.widgets["search_page"][
            "filter_obj_list"
        ]
        filter_obj_list[0].add_btn.show()
        for idx in range(1, len(filter_obj_list)):
            filter_obj_list[idx].deleteLater()
        filter_obj_list = [filter_obj_list[0]]
        filter_obj_list[0].filter_obj_list = filter_obj_list
        # print(filter_obj_list[0].filter_obj_list)
        self.filter_result = set()
        for song_cardi in self.widgets["search_page"][
            "song_cards"
        ]:  # 先清除掉上一次布局的所有东西
            song_cardi.deleteLater()
        self.widgets["search_page"]["song_cards"] = []

    def place_record(self):
        if not hasattr(self, "filter_result"):
            print("要先全局筛选一遍才可以布局喵")
            return
        if not self.filter_result:
            print("无匹配的歌曲喵")
            return
        group_by = self.widgets["search_page"]["group_by"].get_content()
        sort_by = self.widgets["search_page"]["sort_by"].get_content()
        is_reversed = self.widgets["search_page"]["sort_result_reverse_btn"].isChecked()
        print(
            f"分组依据{group_by} 组内排序依据{sort_by}，清除{len(self.widgets["search_page"][
            "song_cards"
        ])}个控件"
        )
        for song_cardi in self.widgets["search_page"][
            "song_cards"
        ]:  # 先清除掉上一次布局的所有东西
            song_cardi.deleteLater()
        self.widgets["search_page"]["song_cards"] = []

        result_display_flow_layout = self.widgets["search_page"][
            "result_display_flow_layout"
        ]
        visited_folder: dict[str, list[folder, list[tuple[str, song_info_card]]]] = {}
        empty_sort_list: list[tuple[str, song_info_card]] = []
        for songi in self.filter_result:
            # combine_name, diffi, score, acc, level, is_fc, singal_rks
            combine_name, diffi, score, acc, level, is_fc, singal_rks = songi
            score_level = get_score_level(int(score), is_fc)

            sort_rely = None  # 默认无
            if sort_by == "acc":
                sort_rely = float(acc)
            elif sort_by == "单曲rks":
                sort_rely = float(singal_rks)
            elif sort_by == "得分":
                sort_rely = int(score)
            elif sort_by == "定数":
                sort_rely = float(level)

            (song_name, composer, drawer, chapter_dic) = self.cname_to_name[
                combine_name
            ]
            song_cardi = song_info_card(
                ILLUSTRATION_PREPATH + combine_name + ".png",
                song_name,
                singal_rks,
                acc,
                level,
                diffi,
                is_fc,
                int(score),
                None,
                composer,
                chapter_dic[diffi],
                drawer,
                False,
                combine_name,
            )
            song_cardi.right_func = self.link_and_show
            selected_group = GROUP_INFO[combine_name].split("`")
            # print(f'当前歌曲已经存在的分组是:{selected_group}')

            selected_tag = TAG_INFO[combine_name].split("`")
            # print(f'当前歌曲已经存在的分组是:{selected_tag}')

            now_comment = COMMENT_INFO[combine_name][diffi]
            song_cardi.set_edited_info(selected_group, selected_tag, now_comment)
            self.widgets["search_page"]["song_cards"].append(song_cardi)

            if group_by == "曲名":
                title = self.cname_to_name[combine_name][0]
                # print(f'title={title}, {type(title)}')
                key = combine_name
            elif group_by == "曲师":
                title = self.cname_to_name[combine_name][1]
                key = title
            elif group_by == "画师":
                title = self.cname_to_name[combine_name][2]
                key = title
            elif group_by == "谱师":
                title = self.cname_to_name[combine_name][3][diffi]
                key = title
            elif group_by == "难度":
                title = diffi
                key = title
            elif group_by == "评级":
                title = score_level.value
                key = title
            elif group_by == "分组":
                title = GROUP_INFO[combine_name].split("`")
                key = title
            elif group_by == "标签":
                title = TAG_INFO[combine_name].split("`")
                key = title

            if group_by != "无":
                if group_by in ("分组", "标签"):
                    for index in range(len(title)):
                        # print('title[index]=',title[index])
                        if (
                            visited_folder.get(key[index], None) is None
                        ):  # 还没有记录[index]
                            song_folderi = folder(title[index], expend=True)
                            self.widgets["search_page"]["song_cards"].append(
                                song_folderi
                            )
                            visited_folder[key[index]] = [song_folderi, []]  # 初始化
                            result_display_flow_layout.addWidget(song_folderi)
                        visited_folder[key[index]][1].append((sort_rely, song_cardi))
                        self.widgets["search_page"]["song_cards"].append(song_cardi)
                else:
                    if visited_folder.get(key, None) is None:  # 还没有记录
                        song_folderi = folder(title, expend=True)
                        self.widgets["search_page"]["song_cards"].append(song_folderi)
                        visited_folder[key] = [song_folderi, []]  # 初始化
                        result_display_flow_layout.addWidget(song_folderi)
                    visited_folder[key][1].append((sort_rely, song_cardi))
                    self.widgets["search_page"]["song_cards"].append(song_cardi)
            else:
                empty_sort_list.append((sort_rely, song_cardi))
                self.widgets["search_page"]["song_cards"].append(
                    song_cardi
                )  # 直接加在song_cards里面

        if group_by != "无":
            for itemi in visited_folder.values():
                folderi, cards = itemi
                if cards[0][0]:
                    cards = sorted(cards, key=lambda x: x[0], reverse=is_reversed)
                for _, cardi in cards:
                    folderi.add_widget(cardi)
        else:
            if empty_sort_list[0][0]:
                empty_sort_list = sorted(
                    empty_sort_list, key=lambda x: x[0], reverse=is_reversed
                )
            for _, cardi in empty_sort_list:
                result_display_flow_layout.addWidget(cardi)

    # --------------- 账号页面 -------------------
    def init_account_page(self) -> QWidget:
        self.widgets["account_page"] = {}
        widget = QWidget()
        self.widgets["account_page"]["widget"] = widget

        layout = QVBoxLayout(widget)  # 纵向布局
        widget.setLayout(layout)
        self.widgets["account_page"]["layout"] = layout

        QRcode_img = ImageLabel(QRCODE_EMPTY_IMG_PATH)  # 空二维码
        self.widgets["account_page"]["QRcode_img"] = QRcode_img
        self.widgets["account_page"]["layout"].addWidget(QRcode_img)

        login_confirm_btn = button("点击这里进行授权")
        login_confirm_btn.bind_click_func(self.check_login_status)
        self.widgets["account_page"]["login_confirm_btn"] = login_confirm_btn
        layout.addWidget(login_confirm_btn)

        log_out_btn = button("退出登录")
        log_out_btn.bind_click_func(self.log_out)
        self.widgets["account_page"]["log_out_btn"] = log_out_btn
        layout.addWidget(log_out_btn)

        with open(TOKEN_PATH, "r") as token_file:
            token = token_file.readline()
            if token:
                login_confirm_btn.hide()  # 如果已经有了token就不用再获取了
                QRcode_img.hide()
                self.token = token
                # self.switch_to(self.home_page)
                # get_token_by_qrcode()
            else:
                log_out_btn.hide()
        return widget

    def check_login_status(self):
        self.QRCode_info = TapTapLogin.RequestLoginQRCode()
        print(f"获取二维码信息成功：{self.QRCode_info}")

        print("已生成二维码！")
        qrcod = make(self.QRCode_info["qrcode_url"])
        qrcod.save(QRCODE_IMG_PATH)
        print("添加成功")
        self.widgets["account_page"]["QRcode_img"].setPixmap(QPixmap(QRCODE_IMG_PATH))
        self.login_check_timer = QTimer()
        self.login_check_timer.setInterval(
            self.QRCode_info["interval"] * 1000
        )  # 秒转毫秒
        self.login_check_timer.timeout.connect(self.check_login)
        self.login_check_timer.start()

    def check_login(self):
        Login_info = TapTapLogin.CheckQRCodeResult(self.QRCode_info)
        if Login_info.get("data"):
            self.login_check_timer.stop()
            print(f"登录成功：{Login_info}")
            Profile = TapTapLogin.GetProfile(Login_info["data"])
            print(f"获取用户资料成功：{Profile}")
            # 这里可以触发登录成功后的操作
            Token = TapTapLogin.GetUserData({**Profile["data"], **Login_info["data"]})
            print(f"获取userdata成功：{Token}")
            with open(TOKEN_PATH, "w") as file:
                file.write(Token["sessionToken"])
            print(f"已输出.userdata文件到当前目录！")
            print(f'你的sessionToken为：{Token["sessionToken"]}')
            self.token = Token["sessionToken"]
            self.widgets["account_page"]["QRcode_img"].hide()
            self.widgets["account_page"]["login_confirm_btn"].hide()
            self.widgets["account_page"]["log_out_btn"].show()
            # self.switch_to(self.home_page)
        else:
            print("二维码登录未授权...")

    def log_out(self):
        with open(TOKEN_PATH, "w") as _:  # 清空tokn记录及self.token
            self.token = ""
            self.widgets["account_page"]["QRcode_img"].show()
            self.widgets["account_page"]["login_confirm_btn"].show()
            self.widgets["account_page"]["log_out_btn"].hide()
        # 应该还要清除其他的页面


if __name__ == "__main__":
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )  # 等比缩放窗口 保证图标大小合适
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
