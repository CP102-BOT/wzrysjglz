import asyncio, json
from database import init_db, async_session
from models import PvPGuide, PvEGuide, CodeItem, QuickRef


async def seed():
    await init_db()
    async with async_session() as s:
        s.add_all([
            PvPGuide(
                title="上官婉儿", description="飞天连招与团战切入时机", icon="🪶",
                category="hero", tags='["刺客","法师","连招"]', badge="hot",
                content="1. 基础连招：2技能起手接3技能冲刺\n2. 飞天技巧：利用3技能五段位移触发被动\n3. 团战思路：侧翼切入，优先切后排",
                video_url="", sort_order=0
            ),
            PvPGuide(
                title="李白", description="野区节奏与技能连招详解", icon="🗡",
                category="hero", tags='["刺客","打野"]', badge="new",
                content="1. 打野路线：红开→反蓝→抓上路\n2. 连招：1A1A23\n3. 核心装备：暗影战斧、破军",
                sort_order=1
            ),
            PvPGuide(
                title="花木兰连招", description="光暗双形态连招与切换节奏", icon="⚡",
                category="combo", tags='["连招","战士"]',
                content="轻剑形态快速接近+沉默，重剑形态霸体输出\n核心：轻剑1技能突进→普攻→2技能→切重剑→2技能推→1技能蓄力",
                video_url="", sort_order=2
            ),
            PvPGuide(
                title="射手出装指南", description="S32赛季射手通用出装与变阵", icon="🏹",
                category="item", tags='["出装","射手"]',
                content="核心装：无尽战刃、破晓、逐日之弓\n防御装：纯净苍穹（防刺客）\n鞋子选择：攻速鞋或抵抗鞋",
                sort_order=3
            ),
            PvPGuide(
                title="4保1战术体系", description="围绕核心射手的战术配合", icon="🛡",
                category="tactic", tags='["战术","团队"]', badge="new",
                content="阵容：边路坦克+辅助+中单工具人+射手+打野\n核心：射手吃所有资源，4人保1人输出\n适用英雄：黄忠、伽罗",
                sort_order=4
            ),
            PvPGuide(
                title="貂蝉", description="被动真伤与灵活位移的进阶打法", icon="💃",
                category="hero", tags='["法师","真伤"]',
                content="核心思路：叠满4层被动触发真实伤害\n2技能无敌帧：躲避关键技能\n出装：圣杯+时之预言+帽子",
                sort_order=5
            ),
        ])
        s.add_all([
            PvEGuide(
                title="世界BOSS·炎龙", description="团队配合与机制破解", icon="🐉",
                category="boss", tags='["BOSS","团队"]', badge="hot",
                content="阶段1：远程输出躲避火焰吐息\n阶段2：地面出现熔岩区域，需分散站位\n阶段3：狂暴状态，集火输出",
                sort_order=0
            ),
            PvEGuide(
                title="隐藏任务·古墓迷踪", description="触发条件与解谜步骤", icon="🏛",
                category="quest", tags='["隐藏","解谜"]',
                content="触发：在落日沙漠地图坐标(320,180)处挖掘\n步骤1：收集3块碎片\n步骤2：在古墓门口按顺序激活石碑",
                sort_order=1
            ),
            PvEGuide(
                title="弱水之源探索", description="全收集与隐藏宝箱位置", icon="💧",
                category="explore", tags='["探索","收集"]',
                content="区域共有24个收集点\n隐藏宝箱：瀑布后面的洞穴中\n建议携带：火把+钩索",
                sort_order=2
            ),
        ])
        s.add_all([
            CodeItem(code="WZRY666", title="WZRY666", description="钻石×88 + 英雄碎片×5", expiry="2026-07-01", sort_order=0),
            CodeItem(code="HAPPY2026", title="HAPPY2026", description="皮肤体验卡×3 + 金币×888", expiry="2026-08-01", sort_order=1),
            CodeItem(code="WZRYSJ888", title="WZRYSJ888", description="限定头像框 + 改名卡", expiry="2026-06-30", sort_order=2),
        ])
        s.add_all([
            QuickRef(title="装备合成表", content="暗影战斧：日冕+陨星\n破军：风暴巨剑+铁剑\n无尽战刃：风暴巨剑+铁剑+冲能拳套", sort_order=0),
            QuickRef(title="段位对应表", content="青铜→白银→黄金→铂金→钻石→星耀→王者→无双王者→荣耀王者→传奇王者", sort_order=1),
            QuickRef(title="铭文推荐", content="通用物理：10隐匿 10鹰眼 10异变\n通用法术：10狩猎 10心眼 10梦魇", sort_order=2),
        ])
        await s.commit()
    print("Seed complete!")

asyncio.run(seed())
