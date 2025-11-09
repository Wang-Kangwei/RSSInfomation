#!/usr/bin/env python3
"""
微信公众号接口测试脚本
"""
import hashlib
import time
import requests
import xml.etree.ElementTree as ET
from wechatpy.utils import check_signature
from wechatpy import parse_message


def test_wechat_verification():
    """测试微信验证接口"""
    print("🔍 测试微信公众号验证接口...")

    # 微信验证参数
    token = "Change_Me123"
    timestamp = str(int(time.time()))
    nonce = "123456789"

    # 生成签名
    signature_list = [token, timestamp, nonce]
    signature_list.sort()
    signature_str = ''.join(signature_list)
    signature = hashlib.sha1(signature_str.encode('utf-8')).hexdigest()

    # 随机echostr
    echostr = "test_echo_123456"

    # 测试URL
    url = "http://localhost:2222/wechat"
    params = {
        'signature': signature,
        'timestamp': timestamp,
        'nonce': nonce,
        'echostr': echostr
    }

    print(f"📋 验证参数:")
    print(f"   Token: {token}")
    print(f"   Timestamp: {timestamp}")
    print(f"   Nonce: {nonce}")
    print(f"   Signature: {signature}")
    print(f"   Echostr: {echostr}")

    try:
        response = requests.get(url, params=params, timeout=10)

        print(f"\n📊 验证结果:")
        print(f"   状态码: {response.status_code}")
        print(f"   响应内容: {response.text}")

        if response.status_code == 200 and response.text == echostr:
            print("✅ 微信验证接口测试成功！")
            return True
        else:
            print("❌ 微信验证接口测试失败！")
            return False

    except Exception as e:
        print(f"❌ 验证接口测试异常: {e}")
        return False


def test_wechat_message():
    """测试微信消息接收接口"""
    print("\n📨 测试微信消息接收接口...")

    # 构造测试消息XML
    xml_message = """
    <xml>
        <ToUserName><![CDATA[toUser]]></ToUserName>
        <FromUserName><![CDATA[test_user_123]]></FromUserName>
        <CreateTime>1234567890</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[新闻]]></Content>
        <MsgId>1234567890123456</MsgId>
    </xml>
    """

    url = "http://localhost:2222/wechat"
    headers = {
        'Content-Type': 'text/xml'
    }

    print(f"📋 测试消息:")
    print(f"   用户: test_user_123")
    print(f"   内容: 新闻")
    print(f"   类型: text")

    try:
        response = requests.post(url, data=xml_message.encode('utf-8'), headers=headers, timeout=10)

        print(f"\n📊 消息处理结果:")
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        print(f"   响应内容: {response.text}")

        if response.status_code == 200:
            print("✅ 微信消息接收接口测试成功！")
            return True
        else:
            print("❌ 微信消息接收接口测试失败！")
            return False

    except Exception as e:
        print(f"❌ 消息接收接口测试异常: {e}")
        return False


def test_signature():
    """测试签名生成"""
    print("\n🔐 测试签名生成...")

    token = "Change_Me123"
    timestamp = str(int(time.time()))
    nonce = "123456789"
    echostr = "test_echo_123456"

    # 生成签名
    signature_list = [token, timestamp, nonce]
    signature_list.sort()
    signature_str = ''.join(signature_list)
    signature = hashlib.sha1(signature_str.encode('utf-8')).hexdigest()

    print(f"📋 签名生成过程:")
    print(f"   原始列表: [token, timestamp, nonce]")
    print(f"   排序后: {signature_list}")
    print(f"   拼接字符串: {signature_str}")
    print(f"   SHA1签名: {signature}")

    # 验证签名
    try:
        is_valid = check_signature(token, signature, timestamp, nonce)
        print(f"   签名验证: {'✅ 通过' if is_valid else '❌ 失败'}")
        return is_valid
    except Exception as e:
        print(f"   签名验证异常: {e}")
        return False


def main():
    """主测试函数"""
    print("🧪 微信公众号接口测试")
    print("=" * 50)

    # 测试签名生成
    signature_ok = test_signature()

    # 测试验证接口
    verification_ok = test_wechat_verification()

    # 测试消息接收
    message_ok = test_wechat_message()

    print("\n" + "=" * 50)
    print("📋 测试总结:")
    print(f"   签名生成: {'✅' if signature_ok else '❌'}")
    print(f"   验证接口: {'✅' if verification_ok else '❌'}")
    print(f"   消息接收: {'✅' if message_ok else '❌'}")

    if all([signature_ok, verification_ok, message_ok]):
        print("\n🎉 所有测试通过！微信公众号接口可以正常使用。")
        print("📱 请在微信公众平台配置服务器地址: http://124.220.147.33:2222/wechat")
    else:
        print("\n❌ 部分测试失败，请检查配置和日志。")


if __name__ == "__main__":
    main()