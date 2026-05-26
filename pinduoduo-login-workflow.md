# 拼多多登录流程文档

## 概述
本文档记录通过浏览器自动化完成拼多多移动端网站登录的完整流程。

## 前提条件
- 手机号码
- 短信验证码（需要用户手动提供）
- 已启动的浏览器会话（OpenClaw browser工具）

## 登录步骤

### 1. 打开登录页面
```javascript
browser({
  action: "open",
  profile: "openclaw",
  targetUrl: "https://mobile.pinduoduo.com/login.html"
})
```

### 2. 点击"手机登录"标签
```javascript
browser({
  action: "act",
  profile: "openclaw",
  targetId: "<page_id>",
  request: {
    kind: "click",
    ref: "e8"  // 手机登录按钮
  }
})
```

### 3. 检查并选择国家/地区
**重要**：默认可能是"中国香港"或其他地区，需要切换到"中国大陆"

```javascript
// 点击国家/地区选择器
browser({
  action: "act",
  profile: "openclaw",
  targetId: "<page_id>",
  request: {
    kind: "click",
    ref: "e20"  // 国家/地区选择器
  }
})

// 在弹出的国家列表中选择"中国大陆"
browser({
  action: "act",
  profile: "openclaw",
  targetId: "<page_id>",
  request: {
    kind: "click",
    ref: "e282"  // 中国大陆（ref可能变化，需要根据实际snapshot）
  }
})
```

### 4. 输入手机号码
```javascript
browser({
  action: "act",
  profile: "openclaw",
  targetId: "<page_id>",
  request: {
    kind: "type",
    ref: "e27",  // 手机号输入框
    text: "<手机号码>"
  }
})
```

### 5. 点击"发送验证码"
```javascript
browser({
  action: "act",
  profile: "openclaw",
  targetId: "<page_id>",
  request: {
    kind: "click",
    ref: "e30"  // 发送验证码按钮
  }
})
```

**等待**：此时验证码会发送到手机，按钮会显示倒计时（如"重新发送(59)"）

### 6. 输入验证码
```javascript
// 需要用户提供收到的验证码
browser({
  action: "act",
  profile: "openclaw",
  targetId: "<page_id>",
  request: {
    kind: "type",
    ref: "e29",  // 验证码输入框
    text: "<验证码>"
  }
})
```

### 7. 勾选"同意服务协议与隐私政策"
```javascript
browser({
  action: "act",
  profile: "openclaw",
  targetId: "<page_id>",
  request: {
    kind: "click",
    ref: "e32"  // 协议勾选框
  }
})
```

### 8. 点击"同意协议并登录"
```javascript
browser({
  action: "act",
  profile: "openclaw",
  targetId: "<page_id>",
  request: {
    kind: "click",
    ref: "e33"  // 登录按钮
  }
})
```

### 9. 验证登录成功
登录成功后会跳转到拼多多首页，可以snapshot验证：
- 显示商品分类列表（推荐、医药、食品等）
- 显示商品列表
- 底部导航栏（首页、直播、分类、聊天、个人中心）

## 关键ref说明

页面元素的ref可能随着页面更新而变化，需要通过snapshot获取当前ref：

| 元素 | 典型ref | 说明 |
|------|---------|------|
| 手机登录标签 | e8 | 登录方式切换 |
| 国家/地区选择器 | e20 | 选择区号 |
| 手机号输入框 | e27 | 输入11位手机号 |
| 验证码输入框 | e29 | 输入6位验证码 |
| 发送验证码按钮 | e30 | 点击后倒计时 |
| 协议勾选框 | e32 | 需要勾选才能登录 |
| 登录按钮 | e33 | 提交登录 |
| 中国大陆 | e282 | 在国家列表中的ref |

## 注意事项

### 1. 国家/地区默认值问题
- 页面可能默认选择"中国香港"（+852）或其他地区
- 中国大陆手机号必须选择"中国大陆"（+86）
- 否则会提示"请输入正确的手机号码"

### 2. 验证码识别
- **无法自动识别**验证码
- 必须由用户从手机短信中查看并手动提供
- 验证码通常6位数字，有效期约60秒

### 3. 倒计时机制
- 发送验证码后按钮会变成"重新发送(59)"
- 倒计时结束后才能再次发送

### 4. 协议勾选
- 必须勾选"同意服务协议与隐私政策"
- 否则点击登录会失败

### 5. 页面状态检查
- 每次操作前建议snapshot获取当前页面状态
- ref值可能变化，需要根据实际snapshot调整

## 完整代码示例

```javascript
// 1. 打开页面
const openResult = await browser({
  action: "open",
  profile: "openclaw",
  targetUrl: "https://mobile.pinduoduo.com/login.html"
});
const pageId = openResult.targetId;

// 2. 点击手机登录
await browser({
  action: "act",
  profile: "openclaw",
  targetId: pageId,
  request: { kind: "click", ref: "e8" }
});

// 3. 选择中国大陆
await browser({
  action: "act",
  profile: "openclaw",
  targetId: pageId,
  request: { kind: "click", ref: "e20" }
});
await browser({
  action: "act",
  profile: "openclaw",
  targetId: pageId,
  request: { kind: "click", ref: "e282" }
});

// 4. 输入手机号
await browser({
  action: "act",
  profile: "openclaw",
  targetId: pageId,
  request: {
    kind: "type",
    ref: "e27",
    text: "15691721290"  // 替换为实际手机号
  }
});

// 5. 发送验证码
await browser({
  action: "act",
  profile: "openclaw",
  targetId: pageId,
  request: { kind: "click", ref: "e30" }
});

// 6. 等待用户提供验证码并输入
await browser({
  action: "act",
  profile: "openclaw",
  targetId: pageId,
  request: {
    kind: "type",
    ref: "e29",
    text: "597471"  // 替换为实际验证码
  }
});

// 7. 勾选协议
await browser({
  action: "act",
  profile: "openclaw",
  targetId: pageId,
  request: { kind: "click", ref: "e32" }
});

// 8. 点击登录
await browser({
  action: "act",
  profile: "openclaw",
  targetId: pageId,
  request: { kind: "click", ref: "e33" }
});

// 9. 验证登录成功
const result = await browser({
  action: "snapshot",
  profile: "openclaw",
  targetId: pageId
});
// 检查是否显示首页元素
```

## 故障排查

### 问题：提示"请输入正确的手机号码"
- **原因**：国家/地区选择错误
- **解决**：点击国家/地区选择器，选择"中国大陆"

### 问题：验证码无法输入
- **原因**：验证码输入框可能未激活
- **解决**：点击验证码输入框后再输入

### 问题：登录按钮点击无效
- **原因**：可能未勾选协议或验证码为空
- **解决**：确认已勾选协议并输入验证码

### 问题：ref值找不到
- **原因**：页面元素ref可能变化
- **解决**：使用snapshot查看当前ref值，更新代码

## 记录

- 创建日期：2026-03-08
- 测试URL：https://mobile.pinduoduo.com/login.html
- 测试手机号：15691721290（示例）
- 状态：✅ 流程验证通过
