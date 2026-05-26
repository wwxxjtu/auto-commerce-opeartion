"""测试拼多多搜索工具"""
import requests
import time

def test_shop_search():
    """测试店铺搜索"""
    print("=== 测试店铺搜索 ===")
    url = "http://127.0.0.1:5000/search"
    data = {
        "type": "shop",
        "keyword": "手机"
    }
    
    try:
        # 增加超时时间以适应长延迟
        response = requests.post(url, json=data, timeout=180)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 店铺搜索成功")
                print(f"找到 {len(result['shops'])} 家店铺")
                for shop in result['shops'][:3]:  # 只显示前3个
                    print(f"  {shop['rank']}. {shop['name']} - {shop['sales']}")
            else:
                print(f"❌ 店铺搜索失败: {result.get('error')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_product_search():
    """测试商品搜索"""
    print("\n=== 测试商品搜索 ===")
    url = "http://127.0.0.1:5000/search"
    data = {
        "type": "product",
        "keyword": "手机壳"
    }
    
    try:
        # 增加超时时间以适应长延迟
        response = requests.post(url, json=data, timeout=180)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 商品搜索成功")
                print(f"找到 {len(result['products'])} 件商品")
                for product in result['products'][:3]:  # 只显示前3个
                    print(f"  {product['rank']}. {product['name']} - {product['price']} - {product['sales']}")
            else:
                print(f"❌ 商品搜索失败: {result.get('error')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("等待服务器启动...")
    time.sleep(2)
    
    test_shop_search()
    # 两次搜索之间增加间隔
    time.sleep(5)
    test_product_search()
    
    print("\n=== 测试完成 ===")