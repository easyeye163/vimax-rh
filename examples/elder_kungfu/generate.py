#!/usr/bin/env python3
"""
老者教武功 30秒视频生成脚本 / Elder Teaching Kung Fu 30s Video Generator
使用 RunningHub App ID 2090774740146413570（MiniMax H3 多图多音频工作流）
三段 x 10秒 = 30秒 | 3 segments x 10s = 30s

用法 / Usage:
  1. 先用文生图生成老者三视图和场景环境图，上传到 RunningHub 获取 fileName
  2. 填入下方 PICTURE1_FILENAME 和 PICTURE2_FILENAME
  3. python generate.py
"""

import json
import os
import time
import requests
import subprocess

# ============ 配置 / Configuration ============
API_KEY = os.environ.get("RUNNINGHUB_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://www.runninghub.cn/openapi/v2"
APP_ID = "2090774740146413570"  # MiniMax H3 multi-image + multi-audio workflow

# 参考图 fileName（需先上传到 RunningHub）
# Reference image fileNames (upload to RunningHub first via POST /openapi/v2/media/upload/binary)
PICTURE1_FILENAME = "openapi/YOUR_THREE_VIEW_IMAGE.jpg"   # 老者三视图 / Old master three-view
PICTURE2_FILENAME = "openapi/YOUR_ENVIRONMENT_IMAGE.jpg"   # 古武场院环境 / Temple courtyard

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# ============ 三段 MiniMax H3 提示词 / Three Segment Prompts ============
# 完整中英文提示词见同目录下的 README.md

PROMPT_1 = """subject_definitions:
<Picture 1> 严格负责老者的身份与造型：约七十岁的中国武术宗师，白色长须垂至胸前，浓白长眉，面容苍老但精神矍铄，眼神深邃而慈祥。体态精瘦但筋骨有力，身穿深灰色传统武术长衫，腰系黑色腰带，脚蹬黑色布鞋。白发在脑后束成发髻。以图1三视图为准确定面部、发型、服装、体态比例，全片不得漂移。
<Picture 2> 仅负责训练场院空间环境：中国古代寺庙庭院，石板铺地，传统中式建筑，飞檐翘角，红漆木柱，古树，兵器架。以图2为准确定庭院纵深与光线来源，不参与人物造型。

summary:
一段10秒真人实拍质感的中国武侠电视剧教学场景。白发武术宗师在古寺庭院中缓缓示范太极拳起手式。暖调古风电影质感。全片无字幕。

retention_analysis:
人物不变量：图1老者的面部、白须白眉、深灰长衫、发髻全程一致。场景不变量：图2庭院布局、石板地面、建筑飞檐稳定。风格不变量：真人实拍，古风武侠审美，暖调金色光线。绝对禁止：字幕、LOGO、水印。

detailed_description:
[Shot 1]（0s-10s）庭院中景，固定机位，微仰角度。画面左侧古树枝叶，右侧红漆木柱飞檐一角。老者站在庭院中央，双脚与肩同宽，面朝镜头。自然站立，双手垂于体侧，目光平和；随即缓缓吸气，双手徐徐抬起至与肩平齐，掌心向下，十指微张，如水中托物；双掌缓缓翻转为掌心朝上，同时屈膝下沉，进入太极抱球姿态；微微侧身，右脚迈出半步，双手在胸前画弧，形成完整起手式定格。衣袖随手臂自然飘动。对白（老者，语气平和）：「太极拳，意在先，气在后。起手式，是万法之宗。」

overall_soundscape:
微风轻拂树叶沙沙声，远处鸟鸣，衣袖摩擦细微声，石板地面踏步回响。老者说话清晰沉稳，带轻微回响。

non_diegetic_music:
10秒配乐，无歌词。0-3s无BGM；3-7s古琴单音渗出，极弱泛音垫底；7-10s古琴渐起，一声钵磬收束。"""

PROMPT_2 = """subject_definitions:
<Picture 1> 严格负责老者的身份与造型：约七十岁的中国武术宗师，白色长须垂至胸前，浓白长眉，面容苍老但精神矍铄。身穿深灰色传统武术长衫，腰系黑色腰带，脚蹬黑色布鞋。白发在脑后束成发髻。以图1三视图为准确定面部、发型、服装、体态比例，全片不得漂移。
<Picture 2> 仅负责训练场院空间环境：中国古代寺庙庭院，石板铺地，传统中式建筑，飞檐翘角，红漆木柱，古树，兵器架。以图2为准确定庭院纵深与光线来源，不参与人物造型。

summary:
一段10秒真人实拍质感的中国武侠电视剧教学场景。在古寺庭院中，老者观察弟子动作后出手纠正其姿势。暖调古风电影质感。全片无字幕。

retention_analysis:
人物不变量：图1老者的面部、白须白眉、深灰长衫、发髻全程一致。弟子为辅助角色，着白色练功服。场景不变量：图2庭院布局、石板地面、建筑稳定。风格不变量：真人实拍，古风武侠审美。绝对禁止：字幕、LOGO、水印。

detailed_description:
[Shot 1]（0s-10s）庭院双人中景，固定机位，平视角度。画面左侧为老者，深灰长衫白须飘逸，双手背后，面带审视而温和的表情，侧头观察身旁的年轻弟子；右侧为约二十岁的弟子，穿白色练功服，正在模仿太极起手式——肩膀略耸，右肘外翻，重心偏高。弟子做完定住，不确定地看向老者。老者走到弟子身旁，右手轻按弟子右肩向下压，左手托其右肘向内收，动作轻柔精准。对白（老者，温和耐心）：「肩要沉，肘要坠。」老者松手后退，弟子重新调整，肩膀放松下沉，肘部内收，老者满意颔首。对白（弟子，恭敬）：「师父，这样对了吗？」对白（老者，含笑）：「嗯，有悟性。」

overall_soundscape:
庭院微风、鸟鸣、树叶沙沙。老者脚步声，触碰弟子肩肘的衣料声。对白清晰，老者声音低沉温和，弟子声音年轻清亮。

non_diegetic_music:
10秒配乐，无歌词。0-4s无BGM；4-7s古筝泛音拨响，极弱pad垫底；7-10s竹笛长音进入，余韵未散。"""

PROMPT_3 = """subject_definitions:
<Picture 1> 严格负责老者的身份与造型：约七十岁的中国武术宗师，白色长须垂至胸前，浓白长眉，面容苍老但精神矍铄。身穿深灰色传统武术长衫，腰系黑色腰带，脚蹬黑色布鞋。白发在脑后束成发髻。以图1三视图为准确定面部、发型、服装、体态比例，全片不得漂移。
<Picture 2> 仅负责训练场院空间环境：中国古代寺庙庭院，石板铺地，传统中式建筑，飞檐翘角，红漆木柱，古树。以图2为准确定庭院纵深与光线来源，不参与人物造型。

summary:
一段10秒真人实拍质感的中国武侠电视剧场景。夕阳西下的古寺庭院中，老者与弟子进行太极拳推手对练，动作行云流水。金色暖调画面如流动古风油画。全片无字幕。

retention_analysis:
人物不变量：图1老者的面部、白须白眉、深灰长衫、发髻全程一致。弟子着白色练功服。场景不变量：图2庭院布局稳定，光线变为夕阳金色调。风格不变量：真人实拍，古风武侠审美，夕阳金色逆光轮廓光。绝对禁止：字幕、LOGO、水印。

detailed_description:
[Shot 1]（0s-10s）庭院双人全景，固定机位，微仰角度。夕阳从右后方低角度照射，老者与弟子身上形成金色轮廓光，影子投射在石板地面。背景古树染成金红色，飞檐剪影在暖色天空中。画面左侧老者，右侧年轻弟子，两人面对面双手前伸搭在一起呈推手姿势。老者双掌搭在弟子前臂上，顺势后引转身，衣袖飘动如行云流水；弟子用力推去，老者四两拨千斤化开，轻轻一送，弟子前倾一步稳稳站住；两人你来我往，动作连贯。夕阳金光在衣衫边缘闪烁，影子缓缓移动。对白（老者，从容）：「太极者，借力打力，以柔克刚。」对白（弟子，笑意）：「师父，我还是推不动您。」老者松手大笑，白须轻颤。对白（老者，笑着）：「等你悟透了，就懂了。」

overall_soundscape:
傍晚虫鸣，微风穿树叶沙沙声，石板脚步声，推手手掌接触声。老者笑声浑厚爽朗回荡，弟子声音年轻充满活力。

non_diegetic_music:
10秒配乐，无歌词。0-3s无BGM；3-6s二胡长音缓缓拉起，极弱；6-10s二胡上扬加入古筝和声，渐强但克制温暖，最后以一声悠远钟声收束全片。"""

PROMPTS = [PROMPT_1, PROMPT_2, PROMPT_3]


def build_payload(prompt: str) -> dict:
    """Build the nodeInfoList payload for the RunningHub workflow."""
    return {
        "nodeInfoList": [
            {"nodeId": "132", "fieldName": "value", "fieldValue": "10", "description": "duration"},
            {"nodeId": "115", "fieldName": "aspect_ratio",
             "fieldData": ("[\"COMBO\", {\"default\": \"1:1 (Square)\", \"options\": "
                            "[\"1:1 (Square)\", \"2:3 (Portrait Photo)\", \"3:2 (Photo)\", "
                            "\"3:4 (Portrait Standard)\", \"4:3 (Standard)\", "
                            "\"9:16 (Portrait Widescreen)\", \"16:9 (Widescreen)\", "
                            "\"21:9 (Ultrawide)\"], \"tooltip\": \"Aspect ratio.\", "
                            "\"multiselect\": false}]"),
             "fieldValue": "16:9 (Widescreen)", "description": "ratio"},
            {"nodeId": "115", "fieldName": "megapixels", "fieldValue": "0.7000000000000001", "description": "res"},
            {"nodeId": "137", "fieldName": "image", "fieldValue": PICTURE1_FILENAME, "description": "picture1-character"},
            {"nodeId": "138", "fieldName": "value", "fieldValue": prompt, "description": "prompt"},
            {"nodeId": "166", "fieldName": "image", "fieldValue": PICTURE2_FILENAME, "description": "picture2-environment"},
            {"nodeId": "167", "fieldName": "image", "fieldValue": "example.png", "description": "picture3"},
            {"nodeId": "168", "fieldName": "image", "fieldValue": "example.png", "description": "picture4"},
            {"nodeId": "165", "fieldName": "audio", "fieldValue": "61f85bd94e99ac11ae7d62d0c9655a093cc3a596ea94e843e1b12d6504c13236.flac", "description": "audio1"},
            {"nodeId": "169", "fieldName": "audio", "fieldValue": "ffc133718aa6119fa7538413581a64da5754e3405d1d4ef1ba3edbbe09c06ccd.flac", "description": "audio2"},
        ],
        "instanceType": "default",
        "usePersonalQueue": "false"
    }


def submit_task(prompt: str, idx: int) -> str:
    """Submit a video generation task with retry on 421 rate limit."""
    payload = build_payload(prompt)
    for attempt in range(10):
        try:
            resp = requests.post(
                f"{BASE_URL}/run/ai-app/{APP_ID}",
                headers=HEADERS, json=payload, timeout=30
            )
            data = resp.json()
            task_id = data.get("taskId", "") or data.get("data", {}).get("taskId", "")
            err_code = str(data.get("errorCode", ""))
            print(f"[{idx+1}] attempt {attempt+1}: code={resp.status_code} err={err_code} tid={task_id}", flush=True)
            if task_id:
                return task_id
            if resp.status_code == 421 or err_code == "421":
                wait = 60 * (attempt + 1)
                print(f"  421 rate limit, wait {wait}s", flush=True)
                time.sleep(wait)
            else:
                print(f"  no taskId, wait 30s", flush=True)
                time.sleep(30)
        except Exception as e:
            print(f"  Error: {e}", flush=True)
            time.sleep(10)
    raise Exception(f"Segment {idx+1} failed after 10 attempts")


def poll_result(task_id: str, idx: int, timeout: int = 600) -> str:
    """Poll task until SUCCESS or FAILED."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            resp = requests.post(f"{BASE_URL}/query", headers=HEADERS,
                                 json={"taskId": task_id}, timeout=30)
            data = resp.json()
            status = data.get("status", "")
            print(f"[{idx+1}] poll: {status} ({int(time.time()-t0)}s)", flush=True)
            if status == "SUCCESS":
                url = data["results"][0]["url"]
                print(f"  URL: {url[:80]}", flush=True)
                return url
            if status == "FAILED":
                reason = data.get("failedReason", {})
                print(f"  FAILED: {json.dumps(reason, ensure_ascii=False)[:300]}", flush=True)
                raise Exception(f"Task {task_id} failed")
        except requests.exceptions.RequestException as e:
            print(f"  Poll error: {e}", flush=True)
        time.sleep(30)
    raise Exception(f"Segment {idx+1} polling timeout")


def download_video(url: str, filepath: str):
    """Download video from URL."""
    resp = requests.get(url, timeout=180, stream=True)
    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)
    print(f"  Saved: {filepath} ({os.path.getsize(filepath)/1024/1024:.1f}MB)", flush=True)


def merge_videos(segment_files: list, output_path: str):
    """Merge video segments with ffmpeg concat."""
    concat_file = os.path.join(OUTPUT_DIR, "concat_list.txt")
    with open(concat_file, "w") as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
         "-c", "copy", output_path],
        capture_output=True, text=True, check=True
    )
    size = os.path.getsize(output_path)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", output_path],
        capture_output=True, text=True
    )
    print(f"Merged: {output_path} ({size/1024/1024:.1f}MB, {float(probe.stdout.strip()):.1f}s)", flush=True)


def upload_image(filepath: str) -> str:
    """Upload a local image to RunningHub, returns fileName."""
    with open(filepath, "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/media/upload/binary",
            headers={"Authorization": f"Bearer {API_KEY}"},
            files={"file": f}, timeout=60
        )
    data = resp.json()
    file_name = data["data"]["fileName"]
    print(f"Uploaded: {filepath} -> {file_name}", flush=True)
    return file_name


def main():
    print("=" * 60)
    print("老者教武功 30秒视频 / Elder Teaching Kung Fu 30s")
    print(f"Workflow App ID: {APP_ID}")
    print("=" * 60)

    # Step 1: Submit all 3 segments serially
    print("\n--- Submitting 3 segments ---")
    task_ids = []
    for i, prompt in enumerate(PROMPTS):
        print(f"\n[Segment {i+1}/3] Submitting...", flush=True)
        tid = submit_task(prompt, i)
        task_ids.append(tid)
        print(f"  Task ID: {tid}", flush=True)
        if i < 2:
            print("  Wait 30s to avoid rate limit...", flush=True)
            time.sleep(30)

    print(f"\nAll submitted: {task_ids}")

    # Step 2: Poll and download
    print("\n--- Polling and downloading ---")
    segment_files = []
    for i, tid in enumerate(task_ids):
        print(f"\n[Segment {i+1}/3] Waiting... (task: {tid})", flush=True)
        url = poll_result(tid, i)
        filepath = os.path.join(OUTPUT_DIR, f"segment_{i+1}.mp4")
        download_video(url, filepath)
        segment_files.append(filepath)

    # Step 3: Merge
    print("\n--- Merging ---")
    output_path = os.path.join(OUTPUT_DIR, "elder_kungfu_final.mp4")
    merge_videos(segment_files, output_path)

    print("\n" + "=" * 60)
    print(f"Done! Output: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
