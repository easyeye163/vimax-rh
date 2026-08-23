# 老者教武功 / Elder Teaching Kung Fu

> 使用 RunningHub MiniMax H3 多图多音频工作流生成的 30 秒中国武侠短片。  
> A 30-second Chinese wuxia short film generated via RunningHub MiniMax H3 multi-image multi-audio workflow.

## 概览 / Overview

| 项目 | 详情 |
|------|------|
| 时长 / Duration | 30s (3 x 10s) |
| 分辨率 / Resolution | 16:9 Widescreen |
| 工作流 / Workflow | MiniMax H3 (App ID: `2090774740146413570`) |
| 参考图1 / Picture 1 | 老者三视图（角色造型）Old master three-view turnaround (character design) |
| 参考图2 / Picture 2 | 古武场院环境（空间光线）Temple courtyard (environment & lighting) |
| 文生图 / Text-to-Image | App ID: `2088920592350277634` |
| 总消耗 / Total Cost | ~162 RH coins |

## 三段内容 / Three Segments

| 段落 | 内容 | 音乐 |
|------|------|------|
| Segment 1 (0-10s) | 白发宗师示范太极起手式 | 静默 → 古琴 → 钵磬 |
| Segment 2 (10-20s) | 老者纠正弟子姿势 | 静默 → 古筝 → 竹笛 |
| Segment 3 (20-30s) | 夕阳下师徒推手对练 | 静默 → 二胡 → 二胡+古筝 → 钟声 |

## 提示词 / Prompts

---

### 🇨🇳 中文版 / Chinese Version

---

#### 参考图生成提示词 / Reference Image Prompts

**老者三视图（文生图）：**

```
Character design sheet, three-view turnaround reference (front view, side view, back view), 
an elderly Chinese martial arts master, approximately 70 years old. Long white beard flowing to 
chest, white eyebrows, weathered face with deep wrinkles, wise and kind eyes. Lean but muscular 
build, posture upright and dignified. Wearing traditional Chinese martial arts clothing: 
loose-fitting dark grey changshan (long gown) with subtle dark patterns, a black sash tied at 
the waist, black cloth shoes with white soles. White hair tied in a neat bun at the back. Arms 
slightly extended showing practiced martial stance, hands with visible calluses. The three views 
arranged horizontally: front view (center, facing camera, standing in natural Wuji stance), 
left side view (left), back view (right). Clean white background, character concept art style, 
high detail, full body, consistent proportions across all views. No text, no watermark.
```

**古武场院环境（文生图）：**

```
Ancient Chinese temple courtyard martial arts training ground, wide establishing shot. 
Stone-paved courtyard surrounded by traditional Chinese architecture with curved tile roofs 
and wooden pillars painted dark red. A large ancient tree with sprawling branches provides 
dappled shade on the left side. Stone steps leading up to a wooden pavilion in the background. 
Wooden weapon racks holding staffs and swords against the far wall. Moss-covered stone lion 
statues flanking the entrance. Late afternoon golden sunlight casting long shadows across the 
courtyard. Photorealistic, cinematic composition, warm golden hour lighting, 16:9 aspect ratio, 
no text, no watermark, no people.
```

---

#### 第1段提示词 / Segment 1 Prompt（0s-10s 起手式示范）

```
subject_definitions:
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
10秒配乐，无歌词。0-3s无BGM；3-7s古琴单音渗出，极弱泛音垫底；7-10s古琴渐起，一声钵磬收束。
```

---

#### 第2段提示词 / Segment 2 Prompt（10s-20s 纠正弟子）

```
subject_definitions:
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
10秒配乐，无歌词。0-4s无BGM；4-7s古筝泛音拨响，极弱pad垫底；7-10s竹笛长音进入，余韵未散。
```

---

#### 第3段提示词 / Segment 3 Prompt（20s-30s 夕阳推手）

```
subject_definitions:
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
10秒配乐，无歌词。0-3s无BGM；3-6s二胡长音缓缓拉起，极弱；6-10s二胡上扬加入古筝和声，渐强但克制温暖，最后以一声悠远钟声收束全片。
```

---

### 🇬🇧 English Version

---

#### Reference Image Prompts

**Old Master Three-View Turnaround (Text-to-Image):**

```
Character design sheet, three-view turnaround reference (front view, side view, back view),
an elderly Chinese martial arts master, approximately 70 years old. Long white beard flowing to
chest, white eyebrows, weathered face with deep wrinkles, wise and kind eyes. Lean but muscular
build, posture upright and dignified. Wearing traditional Chinese martial arts clothing:
loose-fitting dark grey changshan (long gown) with subtle dark patterns, a black sash tied at
the waist, black cloth shoes with white soles. White hair tied in a neat bun at the back. Arms
slightly extended showing practiced martial stance, hands with visible calluses. The three views
arranged horizontally: front view (center, facing camera, standing in natural Wuji stance),
left side view (left), back view (right). Clean white background, character concept art style,
high detail, full body, consistent proportions across all views. No text, no watermark.
```

**Temple Courtyard Environment (Text-to-Image):**

```
Ancient Chinese temple courtyard martial arts training ground, wide establishing shot.
Stone-paved courtyard surrounded by traditional Chinese architecture with curved tile roofs
and wooden pillars painted dark red. A large ancient tree with sprawling branches provides
dappled shade on the left side. Stone steps leading up to a wooden pavilion in the background.
Wooden weapon racks holding staffs and swords against the far wall. Moss-covered stone lion
statues flanking the entrance. Late afternoon golden sunlight casting long shadows across the
courtyard. Photorealistic, cinematic composition, warm golden hour lighting, 16:9 aspect ratio,
no text, no watermark, no people.
```

---

#### Segment 1 Prompt (0s-10s — Tai Chi Opening Stance Demonstration)

```
subject_definitions:
<Picture 1> Strictly defines the old master's identity and appearance: a Chinese martial arts grandmaster around 70 years old, long white beard flowing to chest, thick white eyebrows, weathered face but spirited and sharp-eyed, gaze deep and compassionate. Lean but sinewy build, wearing a dark grey traditional martial arts changshan (long gown), black waist sash, black cloth shoes. White hair tied in a bun at the back. Picture 1 three-view turnaround determines face, hairstyle, clothing, and body proportions — must remain consistent throughout.
<Picture 2> Defines only the training courtyard spatial environment: ancient Chinese temple courtyard, stone-paved ground, traditional architecture with curved eaves, dark red wooden pillars, ancient tree, weapon racks. Picture 2 determines courtyard depth and lighting source — does not affect character design.

summary:
A 10-second live-action cinematic wuxia TV drama teaching scene. A white-haired martial arts grandmaster slowly demonstrates the Tai Chi opening stance in an ancient temple courtyard. Warm-toned period film aesthetic. No text or subtitles.

retention_analysis:
Character invariants: Picture 1 master's face, white beard and eyebrows, dark grey gown, hair bun must stay consistent. Scene invariants: Picture 2 courtyard layout, stone ground, eaves remain stable. Style invariants: Live-action look, wuxia film aesthetic, warm golden lighting. Absolutely forbidden: subtitles, logos, watermarks.

detailed_description:
[Shot 1] (0s-10s) Courtyard medium shot, static camera, slight low angle. Left side shows ancient tree trunk and foliage edge, right side shows dark red pillar and eaves corner. Stone pavement texture clearly visible. The old master stands center-back of courtyard, feet shoulder-width apart, facing camera. He begins in natural stance, hands at sides, gaze calm; then slowly inhales, raising both hands to shoulder height, palms down, fingers slightly spread — as if lifting objects from water; hands slowly turn to palms-up while bending knees, sinking into Tai Chi embracing-ball posture; he shifts slightly, right foot stepping half a pace to the right, hands tracing an arc in front of chest, forming a complete opening stance freeze. Robe sleeves flow naturally with arm movements. Dialogue (old master, calm and steady tone): "Tai Chi — intent comes first, breath follows. The opening stance is the root of all forms."

overall_soundscape:
Gentle wind rustling tree leaves, distant birdsong, subtle fabric rustling from sleeve movements, faint footsteps on stone. Master's voice clear and resonant with slight natural reverb.

non_diegetic_music:
10-second music track, no lyrics. 0-3s no BGM; 3-7s guqin single note emerges from silence, extremely soft harmonic pad underneath, like a morning bell; 7-10s guqin melody builds, ending with a crisp singing bowl strike synchronized with the stance freeze.
```

---

#### Segment 2 Prompt (10s-20s — Correcting the Student's Posture)

```
subject_definitions:
<Picture 1> Strictly defines the old master's identity and appearance: a Chinese martial arts grandmaster around 70 years old, long white beard flowing to chest, thick white eyebrows, weathered face but spirited and sharp-eyed. Lean but sinewy build, wearing a dark grey traditional martial arts changshan, black waist sash, black cloth shoes. White hair tied in a bun at the back. Picture 1 three-view turnaround determines face, hairstyle, clothing, and body proportions — must remain consistent throughout.
<Picture 2> Defines only the training courtyard spatial environment: ancient Chinese temple courtyard, stone-paved ground, traditional architecture with curved eaves, dark red wooden pillars, ancient tree, weapon racks. Picture 2 determines courtyard depth and lighting source — does not affect character design.

summary:
A 10-second live-action cinematic wuxia TV drama teaching scene. In an ancient temple courtyard, the old master observes his young student's movements then gently corrects his posture with precise, gentle hands. Warm-toned period film aesthetic. No text or subtitles.

retention_analysis:
Character invariants: Picture 1 master's face, white beard and eyebrows, dark grey gown, hair bun must stay consistent. The student is a supporting character, wearing white practice clothes. Scene invariants: Picture 2 courtyard layout, stone ground, architecture remain stable. Style invariants: Live-action look, wuxia film aesthetic. Absolutely forbidden: subtitles, logos, watermarks.

detailed_description:
[Shot 1] (0s-10s) Courtyard two-shot medium, static camera, eye-level angle. Left side: the old master in dark grey gown, white beard flowing, hands behind back, expression observant yet gentle, head slightly turned watching the young student beside him. Right side: a student around 20 years old in white practice clothes, attempting to mimic the Tai Chi opening stance — shoulders slightly hunched, right elbow flaring outward, center of gravity too high. Student freezes after completing the form, looking at the master uncertainly. The master nods slightly, walks to the student's side, places his right hand gently on the student's right shoulder pressing it down, while his left hand supports under the right elbow guiding it inward — movement light and precise, touching only for a moment. Dialogue (old master, warm and patient): "Shoulders must sink, elbows must drop." Master releases and steps back half a pace; student readjusts — this time shoulders visibly relax downward, elbows naturally tuck in. Master gives a satisfied nod. Dialogue (student, respectfully): "Master, is this correct?" Dialogue (old master, smiling): "Yes, you have good instincts."

overall_soundscape:
Courtyard ambient sounds continue: breeze, distant birds, leaf rustling. Master's light footsteps approaching the student, soft fabric contact when touching shoulder and elbow. Dialogue clear throughout — master's voice deep and warm with natural reverb, student's voice young and bright.

non_diegetic_music:
10-second music track, no lyrics. 0-4s no BGM, preserving natural ambient and dialogue for authentic teaching feel; 4-7s a single guzheng harmonic plucks, extremely soft pad underneath, like a spring breeze; 7-10s bamboo flute long tone enters, a single note floating like an echo from distant mountains, synchronized with the master's approving nod, lingering gently.
```

---

#### Segment 3 Prompt (20s-30s — Sunset Push-Hand Sparring)

```
subject_definitions:
<Picture 1> Strictly defines the old master's identity and appearance: a Chinese martial arts grandmaster around 70 years old, long white beard flowing to chest, thick white eyebrows, weathered face but spirited and sharp-eyed. Lean but sinewy build, wearing a dark grey traditional martial arts changshan, black waist sash, black cloth shoes. White hair tied in a bun at the back. Picture 1 three-view turnaround determines face, hairstyle, clothing, and body proportions — must remain consistent throughout.
<Picture 2> Defines only the training courtyard spatial environment: ancient Chinese temple courtyard, stone-paved ground, traditional architecture with curved eaves, dark red wooden pillars, ancient tree. Picture 2 determines courtyard depth and lighting source — does not affect character design.

summary:
A 10-second live-action cinematic wuxia TV drama scene. At sunset in an ancient temple courtyard, the old master and student engage in flowing Tai Chi push-hand sparring. Golden warm-tone imagery like a moving classical Chinese painting. No text or subtitles.

retention_analysis:
Character invariants: Picture 1 master's face, white beard and eyebrows, dark grey gown, hair bun must stay consistent. Student in white practice clothes. Scene invariants: Picture 2 courtyard layout stable, but lighting shifts to sunset golden tones. Style invariants: Live-action look, wuxia film aesthetic, sunset golden backlighting creating rim light on figures. Absolutely forbidden: subtitles, logos, watermarks.

detailed_description:
[Shot 1] (0s-10s) Courtyard two-shot wide, static camera, slight low angle. Sunset illuminates from the lower right behind, casting golden rim light on both master and student, with long shadows stretching across the stone pavement. Background ancient tree leaves are dyed gold-red, eaves silhouettes form elegant outlines against the warm sky. Master on the left, young student on the right, standing face-to-face about an arm's length apart, hands extended forward touching in push-hand position. They begin slow, fluid push-hand flow — master's palms rest lightly on student's forearms, yielding and turning with the incoming force, sleeves billowing like flowing water; student pushes hard, master defuses with minimal effort (four ounces deflecting a thousand pounds), then gently sends the student forward — student lunges one step but catches himself steadily. The two flow back and forth in continuous exchange. Sunset golden light shimmers along the edges of their garments, shadows shift slowly on the ground. Dialogue (old master, unhurried): "Tai Chi — borrow the opponent's force to strike back. Overcome hardness with softness." Dialogue (student, amused): "Master, I still can't push you." Master releases hands and laughs heartily, white beard trembling slightly. Dialogue (old master, smiling): "Once you truly understand, you will."

overall_soundscape:
Evening insects beginning to chirp, gentle wind through ancient tree leaves, soft footstep sounds on stone, subtle hand contact sounds during push-hand. Master's laugh resonant and hearty, echoing through the courtyard. Student's voice young and vigorous.

non_diegetic_music:
10-second music track, no lyrics. 0-3s no BGM, only push-hand movement sounds and dialogue establishing realism; 3-6s erhu long tone slowly rises, melody flowing like a mountain spring, matching the rhythm of push-hand exchange, extremely soft; 6-10s erhu melody ascends, joined by guzheng harmony, music swells but remains restrained and warm, intertwined with the master's laughter and sunset golden light, concluding with a single distant bell chime that closes the entire film.
```

---

## 使用方法 / How to Use

### 前置条件 / Prerequisites

- RunningHub API Key
- Python 3.8+ with `requests`
- `ffmpeg` (for merging segments)

### 步骤 / Steps

```bash
# 1. 克隆项目 / Clone the repo
git clone https://github.com/easyeye163/vimax-rh.git
cd vimax-rh/examples/elder_kungfu

# 2. 设置 API Key / Set API Key
export RUNNINGHUB_API_KEY="your_api_key_here"

# 3. 编辑 generate.py，填入已上传的参考图 fileName / Edit generate.py, fill in uploaded reference image fileNames
#    (或使用脚本中的 upload_image() 函数上传本地图片)
#    (Or use the upload_image() function in the script to upload local images)

# 4. 运行 / Run
python generate.py

# 5. 输出文件 / Output files:
#    output/segment_1.mp4
#    output/segment_2.mp4
#    output/segment_3.mp4
#    output/elder_kungfu_final.mp4  (30s merged)
```

## 技术要点 / Technical Notes

### 三视图参考 vs 首帧衔接 / Three-View Reference vs First-Frame Chaining

传统多段视频常用"首帧衔接"（提取上一段尾帧作为下一段首帧）。本例使用**三视图参考**替代：

- `<Picture 1>` = 角色三视图（正面/侧面/背面），全程负责角色造型一致性
- `<Picture 2>` = 环境参考图，负责空间纵深和光线方向
- 每段独立生成，不依赖上段尾帧，避免了误差累积

Traditional multi-segment videos often use "first-frame chaining" (extracting the last frame of the previous segment as the first frame of the next). This example uses **three-view reference** instead:

- `<Picture 1>` = Character three-view turnaround (front/side/back), responsible for character consistency throughout
- `<Picture 2>` = Environment reference image, responsible for spatial depth and lighting direction
- Each segment is generated independently, avoiding error accumulation from frame chaining

### MiniMax H3 六段式提示词结构 / Six-Section Prompt Structure

| 段落 | 作用 | Section | Purpose |
|------|------|---------|--------|
| subject_definitions | 定义图片引用角色 | Define image reference roles |
| summary | 全局概述 | Global overview |
| retention_analysis | 不变量约束 | Invariant constraints |
| detailed_description | 分镜时间线描述 | Shot-by-shot timeline |
| overall_soundscape | 环境声与对白 | Ambient sound & dialogue |
| non_diegetic_music | 配乐时间点 | Music timing points |

### 421 限流处理 / Rate Limit Handling

RunningHub 对视频生成有并发限制（HTTP 421）。解决方案：

- 串行提交（每段间隔30秒）
- 指数退避重试（60s x attempt）

RunningHub enforces concurrency limits on video generation (HTTP 421). Solutions:

- Serial submission (30s gap between segments)
- Exponential backoff retry (60s x attempt)

## 工作流节点配置 / Workflow Node Configuration

```
App ID: 2090774740146413570

nodeId: 132  fieldName: value          — Duration (10s)
nodeId: 115  fieldName: aspect_ratio   — 16:9 (Widescreen)
nodeId: 115  fieldName: megapixels     — 0.7
nodeId: 137  fieldName: image          — <Picture 1> Character reference
nodeId: 138  fieldName: value          — Prompt (MiniMax H3 six-section)
nodeId: 166  fieldName: image          — <Picture 2> Environment reference
nodeId: 167  fieldName: image          — <Picture 3> (optional)
nodeId: 168  fieldName: image          — <Picture 4> (optional)
nodeId: 165  fieldName: audio          — <Audio 1> (optional)
nodeId: 169  fieldName: audio          — <Audio 2> (optional)
```

## License

MIT
