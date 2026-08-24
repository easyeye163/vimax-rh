# vimax-rh

> MiniMax 视频生成 × RunningHub ComfyUI API 的完整工作流工具

基于 [RunningHub](https://www.runninghub.cn) 云端 ComfyUI 平台调用 MiniMax 视频生成模型，实现从**结构化提示词 + 参考图**到**15秒AI视频**的端到端生成。

---

## 目录

- [核心能力](#核心能力)
- [前置准备](#前置准备)
- [快速开始](#快速开始)
- [API 详解](#api-详解)
  - [文生图（生成参考图）](#文生图生成参考图)
  - [图片/视频上传](#图片视频上传)
  - [文生视频（MiniMax）](#文生视频minimax)
  - [任务轮询](#任务轮询)
  - [结果下载](#结果下载)
- [完整示例](#完整示例)
- [提示词规范](#提示词规范)
- [常见问题](#常见问题)
- [成本参考](#成本参考)

---

## 核心能力

| 能力 | 说明 |
|------|------|
| 文生图 | 基于文本描述生成角色三视图/场景参考图 |
| 图片上传 | 将本地图片/视频上传至 RunningHub 云端 |
| 文生视频 | 基于 MiniMax 模型 + 参考图生成 15 秒视频 |
| 多图参考 | 支持 1-4 张参考图同时输入 |
| 任务管理 | 提交、轮询、下载完整生命周期 |

---

## 前置准备

### 1. 获取 API Key

- 注册 [RunningHub](https://www.runninghub.cn) 账号
- 在控制台获取 API Key

### 2. 确认工作流 App ID

| 用途 | App ID | 说明 |
|------|--------|------|
| 文生图 | `2088920592350277634` | Kolors 模型，生成参考图 |
| 文生视频 | `2090774740146413570` | MiniMax H3，生成 15s 视频 |

### 3. 认证方式

所有 API 请求需在 Header 中携带 Bearer Token：

```
Authorization: Bearer <YOUR_API_KEY>
Content-Type: application/json
```

---

## 快速开始

```bash
# 1. 生成一张角色三视图
SUBMIT=$(curl -s -X POST 'https://www.runninghub.cn/openapi/v2/run/ai-app/2088920592350277634' \
  -H 'Authorization: Bearer <KEY>' \
  -H 'Content-Type: application/json' \
  -d '{"nodeInfoList":[{"nodeId":"17","fieldName":"prompt","fieldValue":"一个年轻女性的三视图，正面侧面背面，白色背景"}],"instanceType":"default","usePersonalQueue":"false"}')

TASK_ID=$(echo $SUBMIT | python3 -c "import json,sys;print(json.load(sys.stdin)['taskId'])")

# 2. 等待并获取结果
sleep 60
curl -s -X POST 'https://www.runninghub.cn/openapi/v2/query' \
  -H 'Authorization: Bearer <KEY>' \
  -H 'Content-Type: application/json' \
  -d "{\"taskId\":\"$TASK_ID\"}"
```

---

## API 详解

### 文生图（生成参考图）

**端点**: `POST https://www.runninghub.cn/openapi/v2/run/ai-app/2088920592350277634`

**请求体**:

```json
{
  "nodeInfoList": [
    {
      "nodeId": "17",
      "fieldName": "prompt",
      "fieldValue": "图片描述提示词（中英文均可）"
    }
  ],
  "instanceType": "default",
  "usePersonalQueue": "false"
}
```

| 参数 | 说明 |
|------|------|
| `nodeId` | 固定为 `17` |
| `fieldName` | 固定为 `prompt` |
| `fieldValue` | 图片描述，支持中英文，建议50-200字 |

**响应**:

```json
{
  "taskId": "2091769373810446337",
  "status": "RUNNING"
}
```

**耗时**: 30-90 秒 | **成本**: 7-11 RH 币

---

### 图片/视频上传

> ⚠️ **这是最关键的步骤**。生成的参考图和最终视频都需要先上传到 RunningHub 云端，才能在后续的视频生成任务中引用。

#### 上传端点

```
POST https://www.runninghub.cn/openapi/v2/media/upload/binary
```

#### 请求格式

使用 `multipart/form-data`，通过 `-F` 参数上传文件：

```bash
curl -s -X POST 'https://www.runninghub.cn/openapi/v2/media/upload/binary' \
  -H 'Authorization: Bearer <YOUR_API_KEY>' \
  -F 'file=@/path/to/your/image.png' \
  --max-time 60
```

#### 上传的文件类型与限制

| 文件类型 | 支持格式 | 大小限制 | 说明 |
|----------|---------|---------|------|
| 参考图 | PNG, JPG, WEBP | 建议 < 10MB | 角色三视图、场景参考等 |
| 视频 | MP4 | 建议 < 50MB | 最终生成的视频成果 |

#### 响应结构

```json
{
  "code": 0,
  "data": {
    "fileName": "openapi/c6d439a4103f6fbb622823c51c7bd166fa9f4a41019b77043b741926154abe3e.png",
    "download_url": "https://rh-images-switch-1252422369.cos.ap-guangzhou.myqcloud.com/input/openapi/c6d439a4103f6fbb622823c51c7bd166fa9f4a41019b77043b741926154abe3e.png?q-sign-algorithm=sha1&q-ak=AKIDv56FISEJUsKsMeELk0gm...",
    "size": "1832058",
    "type": "image"
  },
  "message": "success"
}
```

#### 响应字段说明

| 字段 | 说明 | 使用方式 |
|------|------|----------|
| `data.fileName` | **RH 内部文件标识**，提交视频任务时使用此值 | 作为 `image` 节点的 `fieldValue` |
| `data.download_url` | 文件的下载链接（带签名） | 可用于预览/下载，**24小时有效** |
| `data.size` | 文件大小（字节） | 仅用于信息确认 |
| `data.type` | 文件类型（image/video） | 仅用于信息确认 |

#### ⚠️ 上传关键注意事项

**1. fileName 才是你在提交任务时要传的值**

```bash
# ✅ 正确：使用 fileName
"fieldValue": "openapi/c6d439a4103f6fbb622823c51c7bd166fa9f4a41019b77043b741926154abe3e.png"

# ❌ 错误：使用完整 URL
"fieldValue": "https://rh-images-switch-1252422369.cos.ap-guangzhou.myqcloud.com/input/openapi/..."

# ❌ 错误：使用本地文件路径
"fieldValue": "/home/user/image.png"
```

**2. 上传与使用的时间间隔**

上传后的 `fileName` **长期有效**（不存在24小时过期问题），可以随时在提交任务时引用。过期的只是 `download_url`（签名链接）。因此如果你需要反复使用同一张参考图，**只需上传一次，保存 fileName 即可复用**。

**3. 批量上传脚本**

```bash
# 批量上传多张参考图并提取 fileName
for f in /path/to/images/*.png; do
  echo "=== $(basename $f) ==="
  curl -s -X POST 'https://www.runninghub.cn/openapi/v2/media/upload/binary' \
    -H 'Authorization: Bearer <YOUR_API_KEY>' \
    -F "file=@$f" --max-time 60 \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('fileName:', d['data']['fileName'])"
done
```

**4. 上传后验证**

上传完成后，建议立即验证 `code` 是否为 `0`，并保存 `fileName`：

```bash
RESULT=$(curl -s -X POST 'https://www.runninghub.cn/openapi/v2/media/upload/binary' \
  -H 'Authorization: Bearer <YOUR_API_KEY>' \
  -F 'file=@image.png' --max-time 60)

echo $RESULT | python3 -c "
import json, sys
d = json.load(sys.stdin)
if d['code'] == 0:
    print('上传成功! fileName:', d['data']['fileName'])
else:
    print('上传失败:', d)
"
```

**5. 重新上传已有文件**

如果你需要获取新的下载链接（旧链接过期了），直接重新上传同一个文件即可，会得到一个新的 `fileName` 和新的 `download_url`。旧 `fileName` 仍然可用。

---

### 文生视频（MiniMax）

**端点**: `POST https://www.runninghub.cn/openapi/v2/run/ai-app/2090774740146413570`

#### 完整节点配置

```json
{
  "nodeInfoList": [
    {"nodeId": "132", "fieldName": "value", "fieldValue": "15", "description": "时长（必须与提示词一致）"},
    {"nodeId": "115", "fieldName": "aspect_ratio", "fieldValue": "16:9 (Widescreen)", "description": "画幅比"},
    {"nodeId": "115", "fieldName": "megapixels", "fieldValue": "0.7", "description": "分辨率"},
    {"nodeId": "137", "fieldName": "image", "fieldValue": "<上传后返回的fileName>", "description": "picture1"},
    {"nodeId": "166", "fieldName": "image", "fieldValue": "<上传后返回的fileName>", "description": "picture2（可选）"},
    {"nodeId": "167", "fieldName": "image", "fieldValue": "<上传后返回的fileName>", "description": "picture3（可选）"},
    {"nodeId": "168", "fieldName": "image", "fieldValue": "<上传后返回的fileName>", "description": "picture4（可选）"},
    {"nodeId": "138", "fieldName": "value", "fieldValue": "<完整的minimax结构化提示词>", "description": "提示词"}
  ],
  "instanceType": "default",
  "usePersonalQueue": "false"
}
```

#### 节点详细说明

| nodeId | fieldName | 说明 | 必填 | 关键规则 |
|--------|-----------|------|------|----------|
| 132 | value | 视频时长（秒） | ✅ | **必须与提示词中的时长一致**（通常为15） |
| 115 | aspect_ratio | 画幅比 | ✅ | 固定 `16:9 (Widescreen)` |
| 115 | megapixels | 分辨率 | ✅ | 固定 `0.7`（对应 1152×640） |
| 137 | image | Picture 1 | 视情况 | 第1张参考图，**使用上传返回的 fileName** |
| 166 | image | Picture 2 | 可选 | 第2张参考图 |
| 167 | image | Picture 3 | 可选 | 第3张参考图 |
| 168 | image | Picture 4 | 可选 | 第4张参考图，最多4张 |
| 138 | value | 提示词 | ✅ | 完整的 MiniMax 结构化提示词 |

#### ⚠️ 视频生成关键规则

**1. 时长必须一致**

`nodeId=132` 的 `fieldValue` 必须与提示词 `detailed_description` 中描述的时长一致。例如提示词写的是15秒（0s-15s），则 `fieldValue` 必须为 `"15"`。

**2. 每张图用独立节点**

```bash
# ✅ 正确：每张图一个 nodeId
{"nodeId": "137", "fieldName": "image", "fieldValue": "openapi/abc.png"},
{"nodeId": "166", "fieldName": "image", "fieldValue": "openapi/def.png"},
{"nodeId": "167", "fieldName": "image", "fieldValue": "openapi/ghi.png"}

# ❌ 错误：一个节点传多张图
{"nodeId": "137", "fieldName": "image", "fieldValue": "openapi/abc.png"},
{"nodeId": "137", "fieldName": "image", "fieldValue": "openapi/def.png"}
```

**3. 图片数量决定节点数量**

提示词中定义了几个 `<Picture N>`，就传几个图片节点（137/166/167/168）。不多不少。

**4. fileName 直接使用，不带路径前缀**

```bash
# ✅ 正确
"fieldValue": "openapi/c6d439a4103f6fbb622823c51c7bd166fa9f4a41019b77043b741926154abe3e.png"

# ❌ 错误
"fieldValue": "/home/user/image.png"
"fieldValue": "https://cdn.example.com/image.png"
```

---

### 任务轮询

**端点**: `POST https://www.runninghub.cn/openapi/v2/query`

```bash
curl -s -X POST 'https://www.runninghub.cn/openapi/v2/query' \
  -H 'Authorization: Bearer <YOUR_API_KEY>' \
  -H 'Content-Type: application/json' \
  -d '{"taskId": "<TASK_ID>"}' --max-time 30
```

**状态流转**: `QUEUED` → `RUNNING` → `SUCCESS` / `FAILED`

| 状态 | 说明 | 建议操作 |
|------|------|----------|
| `QUEUED` | 排队中 | 等待30秒再查 |
| `RUNNING` | 生成中 | 等待60-120秒再查 |
| `SUCCESS` | 完成 | 从 `results[0].url` 下载 |
| `FAILED` | 失败 | 检查 `failedReason` |

#### 推荐轮询策略

```bash
# 分次轮询，避免长 sleep 超时
for i in $(seq 1 10); do
  RESULT=$(curl -s -X POST 'https://www.runninghub.cn/openapi/v2/query' \
    -H 'Authorization: Bearer <KEY>' \
    -H 'Content-Type: application/json' \
    -d '{"taskId": "'$TASK_ID'"}' --max-time 30)
  
  STATUS=$(echo $RESULT | python3 -c "import json,sys;print(json.load(sys.stdin)['status'])")
  
  if [ "$STATUS" = "SUCCESS" ]; then
    URL=$(echo $RESULT | python3 -c "import json,sys;print(json.load(sys.stdin)['results'][0]['url'])")
    echo "完成! 下载链接: $URL"
    break
  elif [ "$STATUS" = "FAILED" ]; then
    echo "失败: $RESULT"
    break
  else
    echo "状态: $STATUS，等待中..."
    sleep 120
  fi
done
```

#### 预期等待时间

| 任务类型 | 典型耗时 | 成本 |
|----------|---------|------|
| 文生图 | 30-90 秒 | 7-11 币 |
| 文生视频（1张图） | 5-7 分钟 | 76-81 币 |
| 文生视频（4张图） | 6-8 分钟 | 80-85 币 |

---

### 结果下载

```bash
curl -sL -o output.mp4 '<RESULT_URL>' --max-time 300
```

验证结果：

```bash
ffprobe -v quiet -print_format json -show_format -show_streams output.mp4 | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('时长:', round(float(d['format']['duration']), 1), '秒')
print('大小:', round(int(d['format']['size'])/1024/1024, 1), 'MB')
s = d['streams'][0]
print('分辨率:', s['width'], 'x', s['height'])
print('编码:', s['codec_name'])
"
```

**结果 URL 24 小时有效**，请及时下载。如需长期保存，下载后重新上传到 RunningHub 或其他存储。

---

## 完整示例

以下是一个完整的端到端流程：生成角色参考图 → 上传 → 提交视频生成 → 下载结果。

```bash
#!/bin/bash
set -e

API_KEY="your_api_key_here"
AUTH="Authorization: Bearer $API_KEY"

# ====== Step 1: 文生图 - 生成角色三视图 ======
echo "Step 1: 生成角色参考图..."
IMG_RESULT=$(curl -s --connect-timeout 15 -X POST \
  'https://www.runninghub.cn/openapi/v2/run/ai-app/2088920592350277634' \
  -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{
    "nodeInfoList": [{
      "nodeId": "17",
      "fieldName": "prompt",
      "fieldValue": "A young warrior in ancient Chinese armor, front side back three-quarter view turnaround sheet, white background, character design reference, 8K quality"
    }],
    "instanceType": "default",
    "usePersonalQueue": "false"
  }' --max-time 30)

IMG_TASK_ID=$(echo $IMG_RESULT | python3 -c "import json,sys;print(json.load(sys.stdin)['taskId'])")
echo "图片任务已提交: $IMG_TASK_ID"

# ====== Step 2: 等待图片生成完成 ======
echo "等待图片生成..."
sleep 70

IMG_URL=$(curl -s -X POST 'https://www.runninghub.cn/openapi/v2/query' \
  -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"taskId\": \"$IMG_TASK_ID\"}" --max-time 30 \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['results'][0]['url'])")

# 下载图片
curl -sL -o character_ref.png "$IMG_URL" --max-time 60
echo "参考图已下载: character_ref.png"

# ====== Step 3: 上传参考图到 RunningHub ======
echo "上传参考图..."
UPLOAD_RESULT=$(curl -s -X POST 'https://www.runninghub.cn/openapi/v2/media/upload/binary' \
  -H "$AUTH" \
  -F 'file=@character_ref.png' --max-time 60)

FILE_NAME=$(echo $UPLOAD_RESULT | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['fileName'])")
echo "上传成功! fileName: $FILE_NAME"

# ====== Step 4: 提交视频生成 ======
echo "提交视频生成任务..."
PROMPT="subject_definitions:
<Picture 1> 古代武士角色参考，身穿中国古代铠甲。
summary:
一段15秒的古代战士战斗视频。
retention_analysis:
角色不变量：武士的铠甲、发型、武器全程一致。
风格不变量：电影级写实摄影质感。
绝对禁止：字幕、LOGO、水印。
detailed_description:
[Shot 1]（0s-5s）武士站在山崖之上，风吹动铠甲披风，远处云海翻涌。
[Shot 2]（5s-10s）武士拔剑，剑刃泛起寒光，向前冲锋。
[Shot 3]（10s-15s）武士挥剑斩击，剑气划破空气，镜头快速推进。
overall_soundscape:
风声、铠甲碰撞声、剑刃出鞘声。
non_diegetic_music:
无。"

VIDEO_RESULT=$(curl -s --connect-timeout 15 -X POST \
  'https://www.runninghub.cn/openapi/v2/run/ai-app/2090774740146413570' \
  -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{
    "nodeInfoList": [
      {"nodeId": "132", "fieldName": "value", "fieldValue": "15", "description": "时长"},
      {"nodeId": "115", "fieldName": "aspect_ratio", "fieldValue": "16:9 (Widescreen)", "description": "画幅比"},
      {"nodeId": "115", "fieldName": "megapixels", "fieldValue": "0.7", "description": "分辨率"},
      {"nodeId": "137", "fieldName": "image", "fieldValue": "'$FILE_NAME'", "description": "picture1"},
      {"nodeId": "138", "fieldName": "value", "fieldValue": "'$PROMPT'", "description": "提示词"}
    ],
    "instanceType": "default",
    "usePersonalQueue": "false"
  }' --max-time 30)

VIDEO_TASK_ID=$(echo $VIDEO_RESULT | python3 -c "import json,sys;print(json.load(sys.stdin)['taskId'])")
echo "视频任务已提交: $VIDEO_TASK_ID"

# ====== Step 5: 轮询等待视频完成 ======
echo "等待视频生成（预计6-7分钟）..."
for i in $(seq 1 10); do
  sleep 120
  STATUS=$(curl -s -X POST 'https://www.runninghub.cn/openapi/v2/query' \
    -H "$AUTH" -H 'Content-Type: application/json' \
    -d "{\"taskId\": \"$VIDEO_TASK_ID\"}" --max-time 30 \
    | python3 -c "import json,sys;print(json.load(sys.stdin)['status'])")
  
  echo "  [$i] 状态: $STATUS"
  
  if [ "$STATUS" = "SUCCESS" ]; then
    break
  elif [ "$STATUS" = "FAILED" ]; then
    echo "视频生成失败!"
    exit 1
  fi
done

# ====== Step 6: 下载视频 ======
VIDEO_URL=$(curl -s -X POST 'https://www.runninghub.cn/openapi/v2/query' \
  -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"taskId\": \"$VIDEO_TASK_ID\"}" --max-time 30 \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['results'][0]['url'])")

curl -sL -o output_15s.mp4 "$VIDEO_URL" --max-time 300
echo "视频已下载: output_15s.mp4"

# 验证
ffprobe -v quiet -print_format json -show_format -show_streams output_15s.mp4 | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f'时长: {round(float(d["format"]["duration"]),1)}秒, 大小: {round(int(d["format"]["size"])/1024/1024,1)}MB, 分辨率: {d["streams"][0]["width"]}x{d["streams"][0]["height"]}')
"
```

---

## 提示词规范

MiniMax 视频生成使用 **六段式结构化提示词**：

```
1. subject_definitions:   定义每个 Picture 是什么
2. summary:              一句话概括视频内容
3. retention_analysis:   什么保持不变、什么禁止出现
4. detailed_description: 按镜头(Shot)描述画面和动作
5. overall_soundscape:   环境音效
6. non_diegetic_music:   背景音乐
```

### 参考图引用规则

- 提示词中的 `<Picture 1>` 对应 `nodeId=137` 的图片
- 提示词中的 `<Picture 2>` 对应 `nodeId=166` 的图片
- 依此类推
- **不要引用 `<Audio 1>`**（该工作流音频节点未连接，会导致报错）

---

## 常见问题

### Q: 提交任务返回 503 no available server
A: 后端无可用实例，等待1-2分钟后重试。

### Q: 提示词报错 `<Audio 1> is not connected`
A: 提示词中引用了 `<Audio 1>` 但工作流未连接音频节点。删除音频相关文本即可。

### Q: 视频时长不对（只有10秒）
A: `nodeId=132` 的 `fieldValue` 必须为 `"15"`，与提示词时长一致。

### Q: 角色与参考图不一致
A: 检查 `subject_definitions` 中对每个 Picture 的描述是否准确，`retention_analysis` 中是否明确写了保持一致的属性。

### Q: 域名解析失败
A: 使用 `www.runninghub.cn` 而不是 `openapi.runninghub.cn`。

---

## 成本参考

| 操作 | 单次成本 | 耗时 |
|------|---------|------|
| 文生图（参考图） | 7-11 币 | 30-90 秒 |
| 图片上传 | 免费 | 5-15 秒 |
| 文生视频（15秒） | 76-85 币 | 5-8 分钟 |
| 结果下载 | 免费 | 10-60 秒 |

一条完整视频（含1张参考图）约 **85-95 币**，含4张参考图约 **110-125 币**。