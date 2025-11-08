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
from Crypto.Cipher.AES import new, MODE_CBC, block_size
from Crypto.Util.Padding import unpad
import pandas as pd
from src.utils.base import infolog

# ---------------------- 信息获取相关操作 ----------------------
aes_key = b64decode(
    "6Jaa0qVAJZuXkZCLiOa/Ax5tIZVu+taKUN1V1nqwkks="
)  # 解密存档文件需要用的参数
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

        infolog(f"Request type：{method}")
        infolog(f"Request URL：{url}")
        infolog(f"Request header：{headers}")
        infolog(f"Request data：{data}")
        infolog(f"Return header：{response.headers}")
        infolog(f"Status code：{response.status_code}")
        try:
            infolog(f"Return data：{response.content.decode()}")
        except UnicodeDecodeError:
            infolog(f"Return data：Decoding data failed")

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
            # infolog(
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
            }  # 全局的默认请求头

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
            raise ValueError(f'传入的请求类型不合法！不应为"{method}"！')

        infolog(f"请求类型 ：{method}")
        infolog(f"请求URL ：{url}")
        infolog(f"请求头 ：{self._req.request.headers}")
        infolog(f"状态码 ：{self._req.status_code}")

        if self._req.request.body is None:
            infolog(f"请求数据 : *无请求数据*")

        elif isinstance(self._req.request.body, str):
            infolog(f"请求数据 : {repr(self._req.request.body)}")

        else:
            infolog(f"请求数据 : *{len(self._req.request.body)} bytes*")

        if self._req.content is None:
            infolog(f"返回数据 : *无返回数据*")

        else:
            try:
                infolog(f"返回数据 : {self._req.content.decode()}")

            except UnicodeDecodeError:
                infolog(f"返回数据 : *{len(self._req.content)} bytes*")

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

    def getNickname(self) -> str:
        """
        获取玩家昵称

        返回:
            (str): 玩家昵称
        """
        infolog("调用函数：getNickname()")

        # 请求并解析获取玩家昵称
        return_data = (self.request.get(self.baseUrl + "users/me")).json()["nickname"]

        infolog(f'函数"getNickname()"返回：{return_data}')
        return return_data

    def getSummary(self):
        """
        获取玩家summary

        返回:
            (dict): 玩家summary数据
        """
        infolog("调用函数：getSummary()")

        # 请求并初步解析存档信息
        result = (self.request.get(self.baseUrl + "classes/_GameSave?limit=1")).json()[
            "results"
        ][0]
        summary_data = b64decode(result["summary"])  # base64解码summary数据

        # 解析summary数据（谢谢废酱！）
        summary_dict = Reader(summary_data).parseStructure(summary)

        return_data = {  # 解析数据并返回一个字典
            # 这是存档的md5校验值
            "checksum": result["gameFile"]["metaData"]["_checksum"],
            "updateAt": result["updatedAt"],  # 这是存档更新时间
            "url": result["gameFile"]["url"],  # 这是存档直链
            "saveVersion": summary_dict["saveVersion"],  # 这是存档版本
            "challenge": summary_dict["challenge"],  # 课题分
            "rks": summary_dict["rks"],  # 正如其名不多讲了
            "gameVersion": summary_dict["gameVersion"],  # 这是游戏版本
            "avatar": summary_dict["avatar"],  # 这是头像
            "EZ": summary_dict["EZ"],  # EZ难度的评级情况
            "HD": summary_dict["HD"],  # HD难度的评级情况
            "IN": summary_dict["IN"],  # IN难度的评级情况
            "AT": summary_dict["AT"],  # AT难度的评级情况
        }

        infolog(f'函数"getSummary()"返回：{return_data}')
        return return_data

    def getSave(
        self, url: Optional[str] = None, checksum: Optional[str] = None
    ) -> bytes:
        """
        获取存档数据并进行校验 (压缩包数据)
        (返回的数据可用ReadGameSave()读取)

        参数:
            url (str | None): 存档的 URL 。留空自动获取当前token的数据
            checksum (str | None): 存档的 md5 校验值。留空自动获取当前token的数据

        返回:
            (bytes): 存档压缩包数据
        """
        infolog("调用函数：getSave()")

        if url is None:
            summary = self.getSummary()
            url = summary["url"]
            if checksum is None:
                checksum = summary["checksum"]

        elif checksum is None:
            checksum = (self.getSummary())["checksum"]

        # 请求存档文件并获取数据
        save_data = (self.request.get(url)).content  # type: ignore
        # infolog(f"存档文件第一步输出是这个{save_data}")
        if len(save_data) <= 30:
            infolog(
                f"严重警告！！！获取到的云存档大小不足 30 字节！当前大小：{len(save_data)}"
            )
            infolog("可能云存档已丢失！！！请重新将本地存档同步至云端！")
            raise ValueError(
                f"获取到的云存档大小不足 30 字节！当前大小：{len(save_data)}"
            )

        save_md5 = md5()  # 创建一个md5对象，用来计算md5校验值
        save_md5.update(save_data)  # 将存档数据更新进去 传入哈希算法
        actual_checksum = save_md5.hexdigest()  # 获取最终的 MD5 校验和
        if checksum != actual_checksum:  # 对比校验值，不正确则输出警告并等待
            infolog("严重警告！！！存档校验不通过！")
            infolog("这可能是因为不正确地上传存档导致的！")
            raise ValueError(
                f"存档校验不通过！本地存档md5：{actual_checksum}，云端存档md5：{checksum}"
            )

        infolog(f'函数"getSave()"返回：*{len(save_data)} bytes*')
        return save_data  # 返回存档数据

    def refreshSessionToken(self):
        """
        刷新sessionToken

        注意：原先的sessionToken将会失效！

        (会返回新的sessionToken！)

        (刷新是即时的，旧token会立即失效，新的会即时生效)

        返回:
            (str): 新的sessionToken
        """
        infolog("调用函数：refreshSessionToken()")

        # 获取玩家的objectId
        objectId = (self.request.get(self.baseUrl + "users/me")).json()["objectId"]

        # 发送刷新sessionToken请求
        new_sessionToken = (
            self.request.put(self.baseUrl + f"users/{objectId}/refreshSessionToken")
        ).json()[1]["sessionToken"]

        infolog(f'函数"refreshSessionToken()"返回：{new_sessionToken}')
        return new_sessionToken

    def uploadNickname(self, name: str):
        """
        用于更新玩家昵称

        参数:
            name (str): 要更改的昵称

        返回:
            (None): 无~
        """
        infolog("调用函数：uploadNickname()")

        # 请求存档信息
        response = (self.request.get(self.baseUrl + "users/me")).json()
        userObjectId = response["objectId"]  # 获取user的ObjectId
        infolog(f"userObjectId{userObjectId}")

        # 请求更新用户信息
        self.request.put(
            url=self.baseUrl + f"users/{userObjectId}",
            data=dumps({"nickname": name}),
            headers={
                **self.request.headers,
                "Content-Type": "application/json",
            },
        )

        infolog('函数"uploadNickname()"无返回')

    def uploadSummary(self, summary: dict):
        """
        上传summary(从上传存档里面独立出来的)

        (注意这个只能用来看，没有任何实际用处，上传覆盖之后就没了)

        参数:
            summarys (dict): 要上传的summary
        """
        infolog("调用函数：uploadSummary()")

        from struct import pack
        from base64 import b64encode
        from json import dumps
        from datetime import datetime

        # 将解析过的summary构建回去
        avatar_data = summary["avatar"].encode()  # 对头像名称进行编码
        _summary = bytearray()  # 创建一个空的summary数据
        _summary.extend(pack("=B", summary["saveVersion"]))
        _summary.extend(pack("=H", summary["challenge"]))
        _summary.extend(pack("=f", summary["rks"]))
        _summary.extend(pack("=B", summary["gameVersion"]))
        _summary.append(len(avatar_data))
        _summary.extend(avatar_data)
        for key in ["EZ", "HD", "IN", "AT"]:
            for i in summary[key]:
                _summary.extend(pack("=H", i))

        _summary = b64encode(_summary).decode()  # 把summary数据编码回去

        # 请求存档信息
        save_info = (
            self.request.get(self.baseUrl + "classes/_GameSave?limit=1")
        ).json()["results"][0]

        objectId = save_info["objectId"]  # 获取objectId
        userObjectId = save_info["user"]["objectId"]  # 获取user的ObjectId
        # 存档的md5校验值
        checksum = save_info["gameFile"]["metaData"]["_checksum"]
        saveSize = save_info["gameFile"]["metaData"]["size"]  # 存档的大小
        fileObjectId = save_info["gameFile"]["objectId"]  # 存档的objectId

        infolog(f"objectId：{objectId}")
        infolog(f"userObjectId：{userObjectId}")
        infolog(f"checksum：{checksum}")
        infolog(f"saveSize：{saveSize}")

        infolog(f'现summary：{save_info["summary"]}')
        infolog(f"新summary：{summary}")

        # 上传summary
        self.request.put(
            url=self.baseUrl + "classes/_GameSave/{objectId}?",
            data=dumps(
                {
                    "summary": summary,
                    "modifiedAt": {
                        "__type": "Date",
                        "iso": datetime.utcnow().isoformat(timespec="milliseconds")
                        + "Z",
                    },
                    "gameFile": {
                        "__type": "Pointer",
                        "className": "_File",
                        "objectId": fileObjectId,
                    },
                    "ACL": {userObjectId: {"read": True, "write": True}},
                    "user": {
                        "__type": "Pointer",
                        "className": "_User",
                        "objectId": userObjectId,
                    },
                }
            ),
            headers={
                **self.request.headers,
                "Content-Type": "application/json",
            },
        )

        infolog('函数"uploadSummary()"无返回')


def unzipSave(zip_data: bytes) -> dict[str, bytes]:
    """
    读取并解压存档压缩包 存档原始数据

    参数:
        zip_data (bytes): 压缩包数据

    返回:
        (dict[str, bytes]): 存档原始数据 {文件名1: 加密的文件内容, ...}
    """
    save_dict = {}
    # 打开存档文件(其实存档是个压缩包哦！)
    with ZipFile(BytesIO(zip_data)) as zip_file:
        # 打开压缩包中中对应的文件

        for file in zip_file.filelist:
            filename = file.filename
            infolog(f'解压"{filename}"文件')
            with zip_file.open(filename) as file:
                save_dict[filename] = file.read()  # 读取文件数据

    infolog("解压完毕！")
    return save_dict


def decrypt(data: bytes):
    """
    AES CBC解密

    参数:
        data (bytes): 要解密的数据

    返回:
        (bytes): 解密后的数据
    """
    data = new(aes_key, MODE_CBC, aes_iv).decrypt(data)
    return unpad(data, block_size)  # 移除填充


class dataTypeAbstract:
    @staticmethod
    def read(data: bytes, pos: int): ...

    @staticmethod
    def write(data: bytearray, value): ...


class Byte(dataTypeAbstract):
    """一个字节 (1字节)"""

    @staticmethod
    def read(data: bytes, pos: int):
        """
        读取一个字节的数据 (1字节)

        参数:
            data (bytes): 包含数据的字节序列
            pos (int): 当前数据的字节位置

        返回:
            (tuple[int, int]): 包含读取的字节和下一个数据的位置
        """
        return data[pos], pos + 1

    @staticmethod
    def write(data: bytearray, value):
        """
        将一段字节写入字节序列

        参数:
            data (bytearray): 包含数据的字节序列
            value (Any): 要写入的字节值

        返回:
            (bytearray): 修改后的数据序列
        """
        if isinstance(value, int):
            data.append(value)
        else:
            data.extend(value)

        return data


class VarInt(dataTypeAbstract):
    """变长整型 (1-2字节)"""

    @staticmethod
    def read(data: bytes, pos: int):
        """
        读取一个变长整型数据 (1-2字节)

        参数:
            data (bytes): 包含数据的字节序列
            pos (int): 当前数据的字节位置

        返回:
            (tuple[int, int]): 包含读取的变长整型数据和下一个数据的位置
        """
        if data[pos] > 127:  # 如果当前字节位置数据的值大于127
            pos += 2  # 将指针后移2位
            # 脑子爆烧唔
            var_int = (data[pos - 2] & 0b01111111) ^ (data[pos - 1] << 7)
        else:
            var_int = data[pos]  # 读取当前字节位置数据的值
            pos += 1  # 将指针后移1位

        return var_int, pos  # 最后返回读取到的变长整数

    @staticmethod
    def write(data: bytearray, value: int):
        """
        将变长整型数据写入字节序列

        参数:
            data (bytearray): 用于存储数据的字节序列
            value (int): 需要写入的变长整型数据

        返回:
            (bytearray): 更新后的字节序列
        """
        if value > 127:  # 如果大于127，则写入两个字节
            data = Byte.write(data, (value & 0b01111111) | 0b10000000)
            data = Byte.write(data, value >> 7)
        else:
            data = Byte.write(data, value)  # 写入一个字节

        return data


class Bit:
    @staticmethod
    def read(data: int, index: int) -> int:
        """
        读取一个整数中指定索引的比特位值

        参数:
            int (data): 要读取的整数值
            int (index): 比特位索引 (0 到 7 ，其中 0 表示最低位)

        返回:
            (int): 指定索引的比特位值 (1 或 0 )
        """
        # return 1 if bool(data & (1 << index)) else 0
        return (data >> index) & 1

    @staticmethod
    def write(data: int, index: int, value: int) -> int:
        """
        修改一个整数中指定索引的比特位值

        参数:
            data (int): 要修改的整数值
            index (int): 比特位索引 (0 到 7 ，其中 0 表示最低位)
            value (int): 要设置的比特位值 (1 或 0 )

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
        读取一个字符串数据

        参数:
            data (bytes): 包含数据的字节序列
            pos (int): 当前数据的字节位置

        返回:
            (tuple[int, int]): 包含读取的字符串和下一个数据的位置
        """
        string_len, pos = VarInt.read(
            data, pos
        )  # 读当前位置的变长整数，代表后续字节长度
        string_val = data[pos : pos + string_len].decode()  # 读取一段字节并uft-8解码

        return string_val, pos + string_len  # 返回读取到的数据

    @staticmethod
    def write(data: bytearray, value: str):
        """
        将字符串数据写入字节序列

        参数:
            data (bytearray): 用于存储数据的字节序列
            value (str): 需要写入的变长整型数据

        返回:
            (bytearray): 更新后的字节序列
        """
        encoded_string = value.encode("utf-8")
        data = VarInt.write(data, len(encoded_string))
        data.extend(encoded_string)

        return data


class Int(dataTypeAbstract):
    """整型 (4 字节)"""

    @staticmethod
    def read(data: bytes, pos: int):
        """
        读取一个整型的数据 (4 字节)

        参数:
            data (bytes): 包含数据的字节序列
            pos (int): 当前数据的字节位置

        返回:
            (tuple[int, int]): 包含读取的整型数据和下一个数据的位置
        """
        return unpack("<I", data[pos : pos + 4])[0], pos + 4

    @staticmethod
    def write(data: bytearray, value: int):
        """
        将一个整型值写入到字节序列

        参数:
            data (bytearray): 存储数据的字节序列
            value (int): 需要写入的整型值

        返回:
            (bytearray): 更新后的字节序列
        """
        data.extend(pack("<I", value))

        return data


class ShortInt(dataTypeAbstract):
    """短整型 (2字节)"""

    @staticmethod
    def read(data: bytes, pos: int):
        """
        读取一个短整型的数据 (2字节)

        参数:
            data (bytes): 包含数据的字节序列
            pos (int): 当前数据的字节位置

        返回:
            (tuple[int, int]): 包含读取的短整型数据和下一个数据的位置
        """
        return unpack("<H", data[pos : pos + 2])[0], pos + 2

    @staticmethod
    def write(data: bytearray, value: int):
        """
        将短整型数据写入字节序列

        参数:
            data (bytearray): 用于存储数据的字节序列
            value (int): 待写入的短整型数据

        返回:
            (bytearray): 更新后的字节序列
        """
        data.extend(pack("<H", value))

        return data


class Float(dataTypeAbstract):
    """浮点型 (4字节)"""

    @staticmethod
    def read(data: bytes, pos: int):
        """
        读取一个浮点型数据 (4字节)

        参数:
            data (bytes): 包含数据的字节序列
            pos (int): 当前数据的字节位置

        返回:
            (tuple[int, int]): 包含读取的浮点型数据和下一个数据的位置
        """
        return unpack("<f", data[pos : pos + 4])[0], pos + 4

    @staticmethod
    def write(data: bytearray, value: float):
        """
        将浮点型数据写入字节序列

        参数:
            data (bytearray): 存储数据的字节序列
            value (float): 需要写入的浮点型数据

        返回:
            (bytearray): 包含写入数据后的字节序列
        """
        data.extend(pack("<f", value))

        return data


class _Bits(dataTypeAbstract):
    """比特位 (1字节，带长度截取)"""

    def __init__(self, _len: int = 8):
        """比特位 (1字节，带长度截取)"""
        self._len = _len

    def read(self, data: bytes, pos: int) -> tuple[str, int]:
        """
        读取一个整数的所有比特位值 (1字节，带长度截取)

        参数:
            data (bytes): 要读取的字节数据
            pos (int): 数据在字节中的位置

        返回:
            (str, int]): 包含每个比特位的值 (1 或 0) 的列表以及下一个字节的位置
        """
        bits: list[int] = []
        for i in range(self._len):
            bit = Bit.read(data[pos], i)
            bits.append(bit)

        return str(bits), pos + 1

    @staticmethod
    def write(data: bytearray, value: str) -> bytearray:
        """
        根据给定的比特位值列表构建一个整数

        参数:
            data (bytearray): 存储结果的字节数组
            value (str): 每个比特位的值 (1 或 0) 的列表

        返回:
            (bytearray): 更新后的数据序列
        """
        _value: type = eval(value)

        if not isinstance(_value, list):
            raise TypeError(
                f'传入的值不能够被解析为list！而被解析为："{_value.__class__.__name__}"'
            )

        byte = 0

        if len(_value) < 8:
            _value.extend([0] * (8 - len(_value)))

        for i, bit in enumerate(_value):
            byte = Bit.write(byte, i, bit)

        data.append(byte)
        return data


class Bits(dataTypeAbstract):
    """比特位 (1字节)"""

    @staticmethod
    def read(data: bytes, pos: int) -> tuple[str, int]:
        """
        读取一个整数的所有比特位值 (1字节)

        参数:
            data (bytes): 要读取的字节数据
            pos (int): 数据在字节中的位置

        返回:
            (tuple[str, int]): 包含每个比特位的值 (1 或 0) 的列表以及下一个字节的位置
        """
        bits: list[int] = []
        for i in range(8):  # 一个字节有8位
            bit = Bit.read(data[pos], i)
            bits.append(bit)

        return str(bits), pos + 1

    @staticmethod
    def write(data: bytearray, value: str) -> bytearray:
        """
        根据给定的比特位值列表构建一个整数

        参数:
            data (bytearray): 存储结果的字节数组
            value (list[int]): 每个比特位的值 (1 或 0) 的列表

        返回:
            (bytearray): 更新后的数据序列
        """
        _value: type = eval(value)

        if not isinstance(_value, list):
            raise TypeError(
                f'传入的值不能够被解析为list！而被解析为："{_value.__class__.__name__}"'
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
    """反序列化存档数据的操作类"""

    def __init__(self, data: Union[bytes, bytearray], pos: int = 0):
        """
        反序列化存档数据的操作类

        参数:
            data (bytes | bytearray): 要读取的二进制数据
            pos (int): 当前读写位置。默认为 0 
        """
        self.data = data
        self.pos = pos
        self.bit_read = [bytes(), False, 0]

        self.read_dict = {}

    def type_read(self, type_class) -> Any:
        """
        使用数据类型提供的read()方法进行反序列化数据

        参数:
            type_class (class): 定义了read()方法的数据类型

        返回:
            (Any): 反序列化的数据
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
        按照数据结构类定义的结构进行反序列化数据

        参数:
            structure (class): 数据结构类

        返回:
            (dict[str, Any]): 反序列化的数据
        """
        obj = structure()

        if not isinstance(obj, dataTypeAbstract):
            for key, type_obj in structure.__annotations__.items():
                if not __debug__:
                    infolog(key, type_obj)

                self.read_dict[key] = self.type_read(type_obj)

                if not __debug__:
                    infolog(key, getattr(obj, key))

        else:
            self.read_dict = self.type_read(obj)

        if self.remaining() == 0:
            infolog(
                f'结构"{obj.__class__.__name__}"读取完毕！剩余{self.remaining()}字节！'
            )
            # if str(obj.__class__.__name__) == "user01":
            #     infolog(self.read_dict)

        else:
            infolog(
                f'结构"{obj.__class__.__name__}"尚未读取完毕！剩余{self.remaining()}字节！'
            )

        return self.read_dict

    def remaining(self) -> int:
        """
        返回剩余未反序列化的数据长度

        返回:
            (int): 剩余未反序列化的数据长度
        """
        return len(self.data) - self.pos


class Writer:
    """序列化存档数据的操作类"""

    def __init__(self, data: Optional[Union[bytearray, bytes]] = None):
        """
        序列化存档数据的操作类

        参数:
            data (bytes | bytearray | None): 若不为空，则基于此数据向后拼接序列化数据
        """
        if data is None:
            self.data = bytearray()

        elif isinstance(data, bytes):
            self.data = bytearray(data)

        elif isinstance(data, bytearray):
            self.data = data

        else:
            raise TypeError(f'传入的数据类型不合法！不应为"{type(data)}"！')

        self.bit_temp = [0, False, 0]

    def type_write(self, type_fc, value):
        """
        使用数据类型提供的write()方法进行序列化数据

        参数:
            type_class (class): 定义了write()方法的数据类型
            value (Any): 要序列化的数据
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
        按照数据结构类定义的结构进行反序列化数据

        参数:
            structure (class): 数据结构类

        返回:
            (dict[str, Any]): 反序列化的数据
        """
        obj = structure()

        if not isinstance(obj, dataTypeAbstract):
            for key, type_obj in structure.__annotations__.items():
                if not __debug__:
                    infolog(key, type_obj)

                self.type_write(type_obj, data[key])

                if not __debug__:
                    infolog(key, getattr(obj, key))

        else:
            self.type_write(obj, data)

        return self.data

    def get_data(self) -> bytearray:
        """
        返回已经序列化的数据

        返回:
            (bytearray): 已序列化的数据
        """
        return self.data


class user01:
    file_head = b"\x01"

    showPlayerId: Byte
    """右上角展示用户id"""

    selfIntro: String
    """自我介绍"""

    avatar: String
    """头像"""

    background: String
    """背景曲绘"""


class GameKey(dataTypeAbstract):
    @staticmethod
    def read(data: bytes, pos: int):
        all_keys = {}
        reader = Reader(data, pos)
        keySum = reader.type_read(VarInt)  # 总共key的数量，决定循环多少次

        for _ in range(keySum):  # 循环keySum次
            name = reader.type_read(String)  # key的名称
            # 总数据长度(不包含key的昵称)
            length = reader.type_read(Byte)
            one_key = all_keys[name] = {}  # 存储单个key的数据
            # 获取key的状态标志(收藏品阅读、单曲解锁、收藏品、背景、头像)
            one_key["type"] = str((reader.type_read(Bits[5])))

            # 用来存储该key的标记(长度与type中1的数量一致，每位值相同，与收藏品碎片收集有关，默认为1)
            flag = []
            # 因为前面已经读取了一个类型标志了，所以减一
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
    版本号≥3.9.0

    新增"sideStory4BeginReadKey"和"oldScoreClearedV390"
    """

    file_head = b"\x03"

    keyList: GameKey
    """
    游戏中所有Key的状态值
    
    结构:
        type: key的状态标志(收藏品阅读、单曲解锁、收藏品、背景、头像)
        flag: key的标记(长度与type中1的数量一致，每位值相同，与收藏品碎片收集有关，默认为1)
    """

    lanotaReadKeys: Bits[6]
    """Lanota收藏品阅读进度(解锁倒霉蛋和船的AT)"""

    camelliaReadKey: Bits
    """极星卫收藏品阅读进度(解锁S.A.T.E.L.L.I.T.E.的AT)"""

    sideStory4BeginReadKey: Byte
    """解锁支线4"""

    oldScoreClearedV390: Byte
    """是否已清除改谱之前的成绩(如果为0则会清除)"""


class gameKey02:
    """版本号<3.9.0"""

    file_head = b"\x02"

    keyList: GameKey

    lanotaReadKeys: Bits[6]
    """Lanota收藏品阅读进度(解锁倒霉蛋和船的AT)"""

    camelliaReadKey: Bits
    """极星卫收藏品阅读进度(解锁S.A.T.E.L.L.I.T.E.的AT)"""


class GameRecord(dataTypeAbstract):
    @staticmethod
    def read(data: bytes, pos: int):
        all_record = {}  # 用来存储解析出来的数据
        diff_list: tuple = ("EZ", "HD", "IN", "AT", "Legacy")

        reader = Reader(data, pos)
        songSum: int = reader.type_read(VarInt)  # 总歌曲数目

        for _ in range(songSum):
            songName: str = (reader.type_read(String))[:-2]  # 歌曲名字
            # 数据总长度(不包括歌曲名字)
            length: int = reader.type_read(VarInt)
            end_position: int = reader.pos + length  # 单首歌数据结束字节位置
            unlock: int = reader.type_read(Byte)  # 每个难度解锁情况
            fc: int = reader.type_read(Byte)  # 每个难度fc情况
            song = all_record[songName] = {}  # 存储单首歌的成绩数据

            # 遍历每首歌的EZ、HD、IN、AT、Legacy(旧谱)难度的成绩
            for level in range(5):
                if Bit.read(unlock, level):  # 判断当前难度是否解锁
                    score: int = reader.type_read(Int)  # 读取分数
                    acc: float = reader.type_read(Float)  # 读取acc

                    song[diff_list[level]] = {  # 按难度存储进单首歌的成绩数据中
                        "score": score,  # 分数
                        "acc": acc,  # ACC
                        "fc": Bit.read(fc, level),  # 是否Full Combo(FC)
                    }

            if reader.pos != end_position:
                infolog(f'在读取"{songName}"的数据时发生错误！当前位置：{reader.pos}')
                infolog(f"错误！！！当前读取字节位置不正确！应为：{end_position}")

        return all_record, reader.pos

    @staticmethod
    def write(data: bytearray, value: dict):
        diff_list: dict = {"EZ": 0, "HD": 1, "IN": 2, "AT": 3, "Legacy": 4}

        writer = Writer(data)
        writer.type_write(VarInt, len(value))

        for name, song in value.items():
            writer.type_write(String, name + ".0")

            # 这行不是冗余代码啊！本这样子写是有原因的！
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
    版本号≥3.8.1

    新增了"flagOfSongRecordKeyTakumi"
    """

    file_head = b"\x04"

    isFirstRun: Bit
    """是否首次运行"""

    legacyChapterFinished: Bit
    """过去的章节是否完成"""

    alreadyShowCollectionTip: Bit
    """是否展示收藏品Tip"""

    alreadyShowAutoUnlockINTip: Bit
    """是否展示自动解锁IN Tip"""

    completed: String
    """剧情完成 (用于显示全部歌曲和课题模式入口)"""

    songUpdateInfo: VarInt

    challengeModeRank: ShortInt
    """课题分"""

    money: Money
    """Data值"""

    unlockFlagOfSpasmodic: Bits[4]
    """Spasmodic解锁"""

    unlockFlagOfIgallta: Bits[4]
    """Igallta解锁"""

    unlockFlagOfRrharil: Bits[4]
    """Rrhar'il解锁"""

    flagOfSongRecordKey: Bits
    """
    部分歌曲IN达到S解锁AT
    
    (倒霉蛋, 船, Shadow, 心之所向, inferior, DESTRUCTION 3,2,1, Distorted Fate, Cuvism)
    """

    randomVersionUnlocked: Bits[6]
    """Random切片解锁"""

    chapter8UnlockBegin: Bit
    """第八章入场"""

    chapter8UnlockSecondPhase: Bit
    """第八章第二阶段"""

    chapter8Passed: Bit
    """第八章通过"""

    chapter8SongUnlocked: Bits[6]
    """第八章各曲目解锁"""

    flagOfSongRecordKeyTakumi: Bits[3]
    """第四章Takumi AT解锁"""


class gameProgress03:
    """版本号<3.8.1"""

    file_head = b"\x03"

    isFirstRun: Bit
    """是否首次运行"""

    legacyChapterFinished: Bit
    """过去的章节是否完成"""

    alreadyShowCollectionTip: Bit
    """是否展示收藏品Tip"""

    alreadyShowAutoUnlockINTip: Bit
    """是否展示自动解锁IN Tip"""

    completed: String
    """剧情完成 (用于显示全部歌曲和课题模式入口)"""

    songUpdateInfo: VarInt

    challengeModeRank: ShortInt
    """课题分"""

    money: Money
    """Data值"""

    unlockFlagOfSpasmodic: Bits[4]
    """Spasmodic解锁"""

    unlockFlagOfIgallta: Bits[4]
    """Igallta解锁"""

    unlockFlagOfRrharil: Bits[4]
    """Rrhar'il解锁"""

    flagOfSongRecordKey: Bits
    """
    部分歌曲IN达到S解锁AT
    
    (倒霉蛋, 船, Shadow, 心之所向, inferior, DESTRUCTION 3,2,1, Distorted Fate, Cuvism)
    """

    randomVersionUnlocked: Bits[6]
    """Random切片解锁"""

    chapter8UnlockBegin: Bit
    """第八章入场"""

    chapter8UnlockSecondPhase: Bit
    """第八章第二阶段"""

    chapter8Passed: Bit
    """第八章通过"""

    chapter8SongUnlocked: Bits[6]
    """第八章各曲目解锁"""


class settings01:
    file_head = b"\x01"

    chordSupport: Bit
    """多押辅助"""

    fcAPIndicator: Bit
    """FC/AP指示器"""

    enableHitSound: Bit
    """打击音效"""

    lowResolutionMode: Bit
    """低分辨率模式"""

    deviceName: String
    """设备名"""

    bright: Float
    """背景亮度"""

    musicVolume: Float
    """音乐音量"""

    effectVolume: Float
    """界面音效音量"""

    hitSoundVolume: Float
    """打击音效音量"""

    soundOffset: Float
    """谱面延迟"""

    noteScale: Float
    """按键缩放"""


class Summary(dataTypeAbstract):
    @staticmethod
    def read(data: bytes, pos: int):
        reader = Reader(data, pos)
        return [reader.type_read(ShortInt) for _ in range(3)], reader.pos

    @staticmethod
    def write(data: bytearray, value: list):
        writer = Writer(data)
        for i in value:
            writer.type_write(ShortInt, i)

        return writer.get_data()


class summary:
    saveVersion: Byte
    challenge: ShortInt
    rks: Float
    gameVersion: VarInt
    avatar: String
    EZ: Summary
    HD: Summary
    IN: Summary
    AT: Summary


def getStructure(file_head: dict[str, bytes]) -> dict[str, Any]:
    """
    根据文件头获取对应结构类

    参数:
        file_head (dict[str, bytes]): 每个文件的文件头

    返回:
        (dict[str, Any]): 每个文件对应的结构类
    """
    structure_list = {}

    # gameKey
    if file_head.get("gameKey") == b"\x03":
        structure_list["gameKey"] = gameKey03

    elif file_head.get("gameKey") == b"\x02":
        structure_list["gameKey"] = gameKey02

    elif isinstance(file_head.get("gameKey"), bytes):
        raise ValueError(
            f'文件头不正确，可能数据结构已更新！不应为：{file_head.get("gameKey")}'
        )

    # gameProgress
    if file_head.get("gameProgress") == b"\x04":
        structure_list["gameProgress"] = gameProgress04

    elif file_head.get("gameProgress") == b"\x03":
        structure_list["gameProgress"] = gameProgress03

    elif isinstance(file_head.get("gameProgress"), bytes):
        raise ValueError(
            f'文件头不正确，可能数据结构已更新！不应为：{file_head.get("gameProgress")}'
        )

    # gameRecord
    if file_head.get("gameRecord") == b"\x01":
        structure_list["gameRecord"] = GameRecord

    elif isinstance(file_head.get("gameRecord"), bytes):
        raise ValueError(
            f'文件头不正确，可能数据结构已更新！不应为：{file_head.get("gameRecord")}'
        )

    # settings
    if file_head.get("settings") == b"\x01":
        structure_list["settings"] = settings01

    elif isinstance(file_head.get("settings"), bytes):
        raise ValueError(
            f'文件头不正确，可能数据结构已更新！不应为：{file_head.get("settings")}'
        )

    # user
    if file_head.get("user") == b"\x01":
        structure_list["user"] = user01
        # infolog("进入user页面", structure_list["user"])

    elif isinstance(file_head.get("user"), bytes):
        raise ValueError(
            f'文件头不正确，可能数据结构已更新！不应为：{file_head.get("user")}'
        )

    return structure_list


def decryptSave(save_dict: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    反序列化存档原始数据

    参数:
        save_dict (dict[str, Any]): 存档原始数据(unzipSave()可得)

    返回:
        (dict[str, dict]): 存档反序列化数据
    """
    file_head = {}
    for key, value in save_dict.items():
        file_head[key] = value[0].to_bytes()
        infolog(f"文件头为:{file_head}")

    structure_list = getStructure(file_head)  # 获取对应版本的对应文件的配置信息

    for key, value in save_dict.items():
        save_dict[key] = decrypt(
            value[1:]
        )  # 键解密了(username) 但是值还是加密状态(b'\x01\x03KRK\x0) 第一个是文件头 后面才是信息
        # infolog(f"key:{key} val:{save_dict[key]}")
        reader = Reader(save_dict[key])
        save_dict[key] = reader.parseStructure(structure_list[key])

    return save_dict


def formatSaveDict(save_dict: dict[str, dict]):
    new_save_dict = {}

    for key in ["user", "gameProgress", "settings", "gameRecord", "gameKey"]:
        if save_dict.get(key) is not None:
            new_save_dict[key] = save_dict[key]
    # infolog('存档文件是这个:', new_save_dict)
    return new_save_dict
