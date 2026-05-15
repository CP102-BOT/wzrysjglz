import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from models.guide import ExplorationGuide, PvpTip

EXPLORATION_SEEDS = [
    {
        "title": "新手入门指南：从零开始的王者世界冒险",
        "slug": "newbie-guide",
        "description": "第一次踏足王者大陆？这篇指南带你快速上手，了解基础操作、资源系统和成长路线。",
        "category": "新手入门",
        "tags": json.dumps(["新手", "入门", "基础操作"], ensure_ascii=False),
        "difficulty": "入门",
        "is_hot": 1,
        "is_new": 1,
        "content": """<h3>欢迎来到王者大陆</h3>
<p>王者荣耀世界是一款开放世界动作RPG，你将以英雄身份踏足广袤的王者大陆，自由探索、战斗、收集、成长。</p>

<h3>基础操作</h3>
<p><strong>移动：</strong>WASD 或左摇杆控制角色移动</p>
<p><strong>攻击：</strong>鼠标左键普攻，右键重击</p>
<p><strong>技能：</strong>Q/E/R 释放英雄技能，每个英雄技能体系不同</p>
<p><strong>闪避：</strong>Shift 闪避，消耗体力</p>
<p><strong>交互：</strong>F 键与NPC对话、采集资源、开启宝箱</p>

<h3>前期必做</h3>
<p>1. 跟随主线任务推进，解锁地图区域</p>
<p>2. 顺手采集沿途资源（矿石、草药、食材）</p>
<p>3. 解锁传送点，方便后续跑图</p>
<p>4. 到达第一个城镇后，接取支线任务积累经验</p>
<p>5. 升级武器和防具，不要攒材料</p>

<h3>英雄选择建议</h3>
<p>新手推荐选择<strong>战士类英雄</strong>（如赵云、铠），生存能力强，操作相对简单。熟练后可尝试刺客（李白）或法师（小乔）等操作上限更高的英雄。</p>""",
    },
    {
        "title": "建木遗迹全探索攻略：隐藏宝箱+解密路线",
        "slug": "jianmu-ruins",
        "description": "建木遗迹是前期最重要的探索区域，内含多个隐藏宝箱和机关解密，完整路线带你拿完所有奖励。",
        "category": "地图探索",
        "tags": json.dumps(["建木", "遗迹", "宝箱", "解密"], ensure_ascii=False),
        "difficulty": "进阶",
        "is_hot": 1,
        "content": """<h3>建木遗迹概览</h3>
<p>建木遗迹位于王者峡谷北部，是游戏前中期最值得探索的区域之一。区域内共有<strong>8个隐藏宝箱</strong>、<strong>3处机关解密</strong>和<strong>1个隐藏BOSS</strong>。</p>

<h3>推荐等级</h3>
<p>建议英雄等级达到<strong>25级以上</strong>再前往，部分区域有30级精英怪巡逻。</p>

<h3>路线一：遗迹外层（4个宝箱）</h3>
<p>从传送点出发，沿右侧山路攀爬：</p>
<p>1. <strong>宝箱#1：</strong>入口左侧断柱后方，需要破坏藤蔓</p>
<p>2. <strong>宝箱#2：</strong>攀爬到中层平台，击败两只石像鬼后获得</p>
<p>3. <strong>宝箱#3：</strong>中层瀑布后方洞穴中，需游泳穿过瀑布</p>
<p>4. <strong>宝箱#4：</strong>顶层观星台上，需要先用火元素点燃周围四座火炬</p>

<h3>路线二：地下密室（4个宝箱 + 隐藏BOSS）</h3>
<p>从遗迹中央的升降机关进入地下：</p>
<p><strong>机关解密#1：</strong>按「星辰-月亮-太阳」顺序踩地板机关</p>
<p><strong>宝箱#5-6：</strong>解密后两侧密室开启</p>
<p><strong>机关解密#2：</strong>将三面镜子转向中央水晶</p>
<p><strong>隐藏BOSS「建木守护者」：</strong>位于最深处，击败后获得<strong>传说武器「建木之心」</strong></p>
<p><strong>宝箱#7-8：</strong>BOSS房两侧</p>

<h3>注意事项</h3>
<p>- 建议携带<strong>火元素</strong>和<strong>光元素</strong>道具</p>
<p>- 地下区域有瘴气，持续扣血，带足回复药</p>
<p>- 隐藏BOSS会范围攻击，注意闪避时机</p>""",
    },
    {
        "title": "王者峡谷全资源分布图：高效采集路线",
        "slug": "resource-routes",
        "description": "矿脉、草药、食材全标注！教你规划最优采集路线，每天10分钟拿满资源。",
        "category": "资源收集",
        "tags": json.dumps(["资源", "采集", "矿石", "草药", "路线"], ensure_ascii=False),
        "difficulty": "入门",
        "is_hot": 1,
        "content": """<h3>资源刷新机制</h3>
<p>王者大陆的资源每日凌晨4点刷新，不同品质的资源刷新CD不同：</p>
<p><strong>普通资源（白/绿）：</strong>每日刷新</p>
<p><strong>稀有资源（蓝/紫）：</strong>48小时刷新</p>
<p><strong>传说资源（金）：</strong>72小时刷新</p>

<h3>路线一：矿石专线（约8分钟）</h3>
<p>传送点「矿脉入口」→ 沿峡谷左壁前进 → 共采集：<strong>铁矿石×12、铜矿石×8、星陨矿×2</strong></p>

<h3>路线二：草药专线（约6分钟）</h3>
<p>传送点「林间空地」→ 沿海岸线往东 → 共采集：<strong>银叶草×15、月光菇×6、血荆棘×3</strong></p>

<h3>路线三：综合速刷（约12分钟）</h3>
<p>这是效率最高的综合路线，涵盖矿、草、食材：</p>
<p>传送「矿脉入口」→ 采矿 → 传送「林间空地」→ 采草 → 传送「渔村」→ 采集食材+钓鱼 → 结束</p>
<p>综合收益：矿石×20+、草药×18+、食材×10+、鱼×5+</p>""",
    },
    {
        "title": "世界BOSS「风暴龙王」讨伐完全攻略",
        "slug": "storm-dragon",
        "description": "风暴龙王是当前版本最强世界BOSS，掉落全职业毕业装备。详解机制、配队与打法。",
        "category": "BOSS攻略",
        "tags": json.dumps(["世界BOSS", "风暴龙王", "配队", "机制"], ensure_ascii=False),
        "difficulty": "精通",
        "is_new": 1,
        "content": """<h3>BOSS基本信息</h3>
<p><strong>位置：</strong>风暴之巅（需完成主线第5章解锁）</p>
<p><strong>刷新时间：</strong>每天12:00、18:00、22:00</p>
<p><strong>推荐等级：</strong>45级+</p>
<p><strong>推荐战力：</strong>15000+</p>

<h3>机制详解</h3>
<p><strong>阶段一（100%-70%HP）：</strong>龙王主要使用爪击和扫尾，坦克拉住面向，其他人站侧后方输出。</p>
<p><strong>阶段二（70%-40%HP）：</strong>龙王飞天后落地造成AOE伤害，需要全员散开，落地瞬间闪避无敌帧规避。</p>
<p><strong>狂暴阶段（40%-0%HP）：</strong>龙王召唤风暴领域，持续吸引玩家到中心。需要打破四角的<strong>风暴之眼</strong>来破除领域，同时对BOSS造成大量伤害。</p>

<h3>推荐配队</h3>
<p><strong>坦克：</strong>吕布（高减伤+控制）</p>
<p><strong>输出：</strong>李白（高机动+爆发）+ 孙尚香（远程持续输出）</p>
<p><strong>辅助：</strong>貂蝉（治疗+增伤）</p>

<h3>掉落列表</h3>
<p>- 风暴之心（传说材料，100%掉落）</p>
<p>- 龙王鳞甲（传说防具，30%掉落）</p>
<p>- 风暴之刃（传说武器，15%掉落）</p>
<p>- 风暴龙王坐骑碎片（5%掉落）</p>""",
    },
    {
        "title": "隐藏任务「东方来客」触发与全流程",
        "slug": "eastern-visitor",
        "description": "99%玩家不知道的隐藏任务！触发条件苛刻但奖励丰厚，包含限定称号和传说装备。",
        "category": "隐藏要素",
        "tags": json.dumps(["隐藏任务", "限定", "传说装备"], ensure_ascii=False),
        "difficulty": "进阶",
        "is_new": 1,
        "content": """<h3>触发条件</h3>
<p>必须在以下条件同时满足时，前往「东方客栈」与NPC「无名旅者」对话：</p>
<p>1. 主线完成第4章</p>
<p>2. 背包中携带<strong>「残破的信件」</strong>（在王者峡谷区域随机刷新）</p>
<p>3. 时间为游戏内<strong>夜晚（18:00-6:00）</strong></p>
<p>4. 天气为<strong>雨天</strong></p>

<h3>任务流程</h3>
<p><strong>第一步：</strong>与无名旅者对话，选择「我知道你在找什么」</p>
<p><strong>第二步：</strong>前往「龙骨沙漠」东南角，在沙暴中寻找隐藏入口（使用风元素驱散沙暴）</p>
<p><strong>第三步：</strong>进入地下遗迹，击败三波守护者</p>
<p><strong>第四步：</strong>在遗迹最深处的祭坛上放置「残破的信件」</p>
<p><strong>第五步：</strong>返回东方客栈与无名旅者对话，获得奖励</p>

<h3>奖励</h3>
<p>- 限定称号：「东方来客」</p>
<p>- 传说饰品：「旅者之戒」（暴击+15%）</p>
<p>- 大量经验与金币</p>""",
    },
]

PVP_SEEDS = [
    {
        "title": "PVP新手入门：基础连招与走位技巧",
        "slug": "pvp-basics",
        "description": "刚接触PVP？这篇攻略帮你快速掌握基础连招逻辑、走位预判和反制时机。",
        "category": "对战策略",
        "tags": json.dumps(["新手", "PVP", "连招", "走位"], ensure_ascii=False),
        "difficulty": "入门",
        "is_hot": 1,
        "is_new": 1,
        "content": """<h3>PVP基础知识</h3>
<p>王者荣耀世界的PVP采用实时动作对战，考验操作、意识和配招。核心要素：</p>
<p><strong>霸体：</strong>释放特定技能时免疫控制</p>
<p><strong>硬直：</strong>被重击或技能命中后短暂无法行动</p>
<p><strong>无敌帧：</strong>闪避动作中的短暂无敌时间</p>
<p><strong>体力管理：</strong>闪避和重击消耗体力，体力归零后无法闪避</p>

<h3>基础连招逻辑</h3>
<p>所有英雄的连招都遵循一个基本框架：</p>
<p><strong>轻击×3 → 重击（击飞）→ 技能 → 闪避追击 → 大招收尾</strong></p>
<p>这是最基础的连招模板，熟悉后可根据各英雄特性调整。</p>

<h3>走位技巧</h3>
<p>1. <strong>侧向走位：</strong>不要直线后退，侧向移动更容易躲开直线技能</p>
<p>2. <strong>骗技能：</strong>假意靠近逼对手交技能，然后闪避回撤</p>
<p>3. <strong>抢体力差：</strong>逼迫对手频繁闪避，等其体力见底时发起进攻</p>
<p>4. <strong>地形利用：</strong>利用柱子、墙壁卡对手视野和走位</p>""",
    },
    {
        "title": "李白PVP深度教学：七进七出的剑仙之道",
        "slug": "libai-pvp",
        "description": "李白是PVP中操作上限最高的英雄之一。详解技能机制、连招组合和对局思路。",
        "category": "角色技巧",
        "tags": json.dumps(["李白", "刺客", "高阶", "连招"], ensure_ascii=False),
        "difficulty": "精通",
        "is_hot": 1,
        "content": """<h3>李白PVP定位</h3>
<p>李白是典型的<strong>高机动刺客</strong>，特点是多段位移、高爆发、低容错。一套打完必须脱战，否则容易被反杀。</p>

<h3>技能机制</h3>
<p><strong>被动·侠客行：</strong>连续4次普攻后进入侠客行状态，攻击力+30%，持续5秒。PVP核心：开战前先A小兵叠被动。</p>
<p><strong>技能1·将进酒：</strong>向指定方向突进三次，第三次回到起点。PVP核心位移技，可用于进场、追击、逃生。</p>
<p><strong>技能2·神来之笔：</strong>以自身为中心释放剑气圈，敌人触碰圈边缘受伤害并减速。</p>
<p><strong>大招·青莲剑歌：</strong>化身剑气穿梭，5次伤害且不可选中，但需要解锁（叠被动或技能命中5次）。</p>

<h3>核心连招</h3>
<p><strong>基础连招：</strong>将进酒(1段)→ 普攻×2 → 将进酒(2段)→ 神来之笔 → 普攻×2 → 青莲剑歌 → 将进酒(3段)回到原位</p>
<p><strong>速杀连招：</strong>A小兵叠好被动 → 将进酒(1段)进场 → 青莲剑歌 → 神来之笔 → 将进酒(2段)追击 → 普攻 → 将进酒(3段)撤离</p>
<p><strong>骗技能连招：</strong>将进酒(1段)假进场 → 闪避回撤骗对手技能 → 将进酒(2段)真进场 → 青莲剑歌收尾</p>

<h3>对局思路</h3>
<p>1. 不要正面开团，等队友先手或对手关键技能交完再进场</p>
<p>2. 利用将进酒的一段和二段调整切入角度，不要无脑冲正面</p>
<p>3. 大招期间不可选中，可以用来躲对手大招</p>
<p>4. 残局李白最强，收割阶段优先切脆皮</p>""",
    },
    {
        "title": "当前版本T0阵容推荐：排位上分利器",
        "slug": "t0-team-comp",
        "description": "基于当前版本数据分析，推荐三套高胜率PVP阵容及配合打法。",
        "category": "阵容搭配",
        "tags": json.dumps(["阵容", "T0", "排位", "上分"], ensure_ascii=False),
        "difficulty": "进阶",
        "is_new": 1,
        "content": """<h3>阵容一：双战核体系（胜率58%）</h3>
<p><strong>配置：</strong>吕布（控制+前排）+ 赵云（突进+爆发）</p>
<p><strong>打法：</strong>吕布先手开团吸收伤害和控制，赵云侧翼切入收割后排。吕布护盾+吸血续航极强，赵云残局能力拉满。</p>
<p><strong>克制：</strong>双脆皮阵容</p>
<p><strong>被克制：</strong>风筝型阵容（孙尚香+貂蝉）</p>

<h3>阵容二：法术压制流（胜率55%）</h3>
<p><strong>配置：</strong>小乔（远程爆发）+ 貂蝉（控制+辅助）</p>
<p><strong>打法：</strong>貂蝉魅惑控场，小乔远程无脑输出。对方近身时貂蝉开大招群体治疗+反打。</p>
<p><strong>克制：</strong>近战突脸阵容</p>
<p><strong>被克制：</strong>李白+赵云双刺客</p>

<h3>阵容三：双刺速攻（胜率53%）</h3>
<p><strong>配置：</strong>李白（进场爆发）+ 兰陵王（隐身偷袭）</p>
<p><strong>打法：</strong>兰陵王隐身探视野，找到脆皮位置后李白直接切入秒杀。兰陵王补控制和追击。</p>
<p><strong>克制：</strong>单前排阵容</p>
<p><strong>被克制：</strong>双坦阵容（吕布+项羽）</p>""",
    },
    {
        "title": "1v1对战心理博弈：预判、骗招与反制",
        "slug": "1v1-mindgames",
        "description": "1v1不仅是操作的对决，更是心理的博弈。掌握预判技巧和骗招心法。",
        "category": "进阶技巧",
        "tags": json.dumps(["1v1", "心理", "预判", "骗招"], ensure_ascii=False),
        "difficulty": "进阶",
        "content": """<h3>1v1核心心法</h3>
<p>1v1对战中，<strong>信息差</strong>是关键。谁能预判对方的下一步行动，谁就掌握了主动权。</p>

<h3>预判技巧</h3>
<p><strong>观察对手习惯：</strong>开局前30秒不要全力进攻，观察对手的闪避习惯、技能释放节奏和走位偏好。</p>
<p><strong>读技能CD：</strong>记住对手关键技能的CD时间，在其技能真空期发起进攻。</p>
<p><strong>看体力条：</strong>对手体力低于30%时，是其最脆弱的时候，果断进攻。</p>

<h3>骗招心法</h3>
<p>1. <strong>假闪避：</strong>做闪避动作假动作，引诱对手交技能后原地反击</p>
<p>2. <strong>蓄力取消：</strong>蓄力重击后取消，骗对手闪避</p>
<p>3. <strong>假装走位失误：</strong>故意露背身引诱对手追击，然后反打</p>

<h3>常见反制场景</h3>
<p><strong>被李白进场：</strong>不要追，直接远离李白进场位置，断他的将进酒(3段)回路</p>
<p><strong>被吕布大招砸：</strong>往吕布<strong>身后</strong>闪避，而不是远离</p>
<p><strong>被小乔远程消耗：</strong>利用地形卡视野靠近，不要直线接近</p>""",
    },
    {
        "title": "全英雄PVP强度排名（当前版本）",
        "slug": "pvp-tier-list",
        "description": "基于实战胜率和赛事数据，整理当前版本全英雄PVP强度排名及简要分析。",
        "category": "对战策略",
        "tags": json.dumps(["强度排名", "T0", "版本"], ensure_ascii=False),
        "difficulty": "入门",
        "is_hot": 1,
        "content": """<h3>T0（版本答案，非Ban必选）</h3>
<p><strong>李白：</strong>高机动+高爆发+不可选中大招，操作上限极高，熟练后几乎无解。</p>
<p><strong>吕布：</strong>超强生存能力+吸血+控制，能打能扛，配任何阵容都稳。</p>

<h3>T1（强势英雄，可稳定上分）</h3>
<p><strong>赵云：</strong>灵活战士，连招流畅，残局收割能力强。</p>
<p><strong>孙尚香：</strong>远程持续输出，装备成型后伤害恐怖。</p>
<p><strong>貂蝉：</strong>最强辅助之一，控场+治疗+增伤，组队首选。</p>

<h3>T2（中规中矩，看操作）</h3>
<p><strong>小乔：</strong>范围输出高但自保能力差，需要有前排保护。</p>
<p><strong>铠：</strong>攻防兼备但机动性不足，容易被风筝。</p>

<h3>排名说明</h3>
<p>此排名基于3v3和1v1综合表现，高分段（钻石以上）数据为主。低分段部分英雄排名可能不同。</p>""",
    },
]


async def seed_exploration(session: AsyncSession) -> None:
    result = await session.execute(text("SELECT COUNT(*) FROM exploration_guides"))
    if result.scalar() > 0:
        return
    for data in EXPLORATION_SEEDS:
        session.add(ExplorationGuide(**data))
    await session.commit()


async def seed_pvp(session: AsyncSession) -> None:
    result = await session.execute(text("SELECT COUNT(*) FROM pvp_tips"))
    if result.scalar() > 0:
        return
    for data in PVP_SEEDS:
        session.add(PvpTip(**data))
    await session.commit()


async def seed_all(session: AsyncSession) -> None:
    await seed_exploration(session)
    await seed_pvp(session)
