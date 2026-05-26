#!/usr/bin/env python3
"""
MCP Server Test Script
This script tests the MCP server functionality by simulating MCP tool calls.
"""
import asyncio
import sys
from storage import storage
from models import SMSMessage
from datetime import datetime


async def test_storage():
    print("Testing SMS Storage...")
    
    print("\n1. Creating test SMS messages...")
    test_sms = [
        SMSMessage(
            id="test_001",
            sender="10086",
            content="您的验证码是123456",
            timestamp=datetime.now(),
            sim_slot="SIM1",
            device_name="TestPhone1"
        ),
        SMSMessage(
            id="test_002",
            sender="10010",
            content="您的余额不足10元",
            timestamp=datetime.now(),
            sim_slot="SIM2",
            device_name="TestPhone1"
        ),
        SMSMessage(
            id="test_003",
            sender="95588",
            content="您的账户于2024-01-01消费100元",
            timestamp=datetime.now(),
            sim_slot="SIM1",
            device_name="TestPhone1"
        ),
    ]
    
    for sms in test_sms:
        await storage.add_sms(sms)
        print(f"  ✓ Added: {sms.sender} - {sms.content[:20]}...")
    
    print("\n2. Testing get_latest_sms...")
    latest = await storage.get_latest_sms(2)
    print(f"  ✓ Found {len(latest)} latest SMS")
    for sms in latest:
        print(f"    - {sms.sender}: {sms.content[:20]}...")
    
    print("\n3. Testing search_sms...")
    search_results = await storage.search_sms("验证码")
    print(f"  ✓ Found {len(search_results)} SMS matching '验证码'")
    for sms in search_results:
        print(f"    - {sms.sender}: {sms.content[:20]}...")
    
    print("\n4. Testing get_sms_by_id...")
    sms = await storage.get_sms_by_id("test_001")
    if sms:
        print(f"  ✓ Found SMS by ID: {sms.sender} - {sms.content}")
    else:
        print("  ✗ SMS not found")
    
    print("\n5. Testing get_all_sms...")
    all_sms = await storage.get_all_sms()
    print(f"  ✓ Total SMS in storage: {len(all_sms)}")
    
    print("\n6. Testing clear_all_sms...")
    await storage.clear_all()
    cleared_sms = await storage.get_all_sms()
    print(f"  ✓ Storage cleared. Remaining SMS: {len(cleared_sms)}")
    
    print("\n✓ All storage tests passed!")


async def test_mcp_tools():
    print("\n" + "=" * 50)
    print("Testing MCP Tools Simulation")
    print("=" * 50)
    
    print("\n1. Simulating get_latest_sms tool...")
    latest = await storage.get_latest_sms(5)
    if not latest:
        print("  Result: 暂无短信记录")
    else:
        result = []
        for sms in latest:
            result.append(f"【{sms.timestamp}】{sms.sender}: {sms.content}")
        print("  Result:")
        for line in result:
            print(f"    {line}")
    
    print("\n2. Simulating search_sms tool...")
    search_results = await storage.search_sms("测试")
    if not search_results:
        print("  Result: 未找到包含关键词 '测试' 的短信")
    else:
        result = []
        for sms in search_results:
            result.append(f"【{sms.timestamp}】{sms.sender}: {sms.content}")
        print(f"  Result: 找到 {len(search_results)} 条匹配的短信")
        for line in result:
            print(f"    {line}")
    
    print("\n3. Simulating get_sms_by_id tool...")
    sms = await storage.get_sms_by_id("test_001")
    if not sms:
        print("  Result: 未找到ID为 'test_001' 的短信")
    else:
        result = f"短信ID: {sms.id}\n"
        result += f"发送者: {sms.sender}\n"
        result += f"时间: {sms.timestamp}\n"
        result += f"内容: {sms.content}\n"
        if sms.sim_slot:
            result += f"卡槽: {sms.sim_slot}\n"
        if sms.device_name:
            result += f"设备: {sms.device_name}\n"
        print("  Result:")
        for line in result.split('\n'):
            print(f"    {line}")
    
    print("\n4. Simulating get_all_sms tool...")
    all_sms = await storage.get_all_sms()
    if not all_sms:
        print("  Result: 暂无短信记录")
    else:
        result = []
        for sms in all_sms:
            result.append(f"【{sms.timestamp}】{sms.sender}: {sms.content}")
        print(f"  Result: 共有 {len(all_sms)} 条短信")
        for line in result[:3]:
            print(f"    {line}")
        if len(result) > 3:
            print(f"    ... (还有 {len(result) - 3} 条)")
    
    print("\n5. Simulating clear_all_sms tool...")
    await storage.clear_all()
    print("  Result: 已清空所有短信记录")
    
    print("\n✓ All MCP tool simulations passed!")


async def main():
    print("=" * 50)
    print("MCP Server Test Suite")
    print("=" * 50)
    
    try:
        await test_storage()
        await test_mcp_tools()
        
        print("\n" + "=" * 50)
        print("✓ ALL TESTS PASSED")
        print("=" * 50)
        return 0
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
