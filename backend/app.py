#!/usr/bin/env python3
"""王者荣耀世界攻略站 - 后端 + 管理后台（PVP + 自由探索）"""

import json
import sqlite3
import csv
import io
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session, send_from_directory, g, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'wzrysj_admin_2026_secret'

RENDER_DATA = '/opt/render/project/data'
if os.environ.get('RENDER'):
    os.makedirs(RENDER_DATA, exist_ok=True)
    DATABASE = os.path.join(RENDER_DATA, 'data.db')
else:
    DATABASE = 'data.db'
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'site_admin_2026')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'K9xP!7qR#3zL@2sN$5aM')

login_attempts = {}

# ==================== 数据库 ====================

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db

@app.teardown_appcontext
def close_db(e):
    db = g.pop('db', None)
    if db: db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    cur = db.cursor()
    cur.executescript('''
        CREATE TABLE IF NOT EXISTS pvp_guides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            content TEXT DEFAULT '',
            icon TEXT DEFAULT '⚔️',
            image_url TEXT DEFAULT '',
            category TEXT DEFAULT 'general',
            tags TEXT DEFAULT '[]',
            badge TEXT DEFAULT '',
            video_url TEXT DEFAULT '',
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS explore_guides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            content TEXT DEFAULT '',
            icon TEXT DEFAULT '🗺️',
            image_url TEXT DEFAULT '',
            category TEXT DEFAULT 'map',
            tags TEXT DEFAULT '[]',
            badge TEXT DEFAULT '',
            video_url TEXT DEFAULT '',
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            description TEXT DEFAULT '',
            reward TEXT DEFAULT '',
            expiry TEXT DEFAULT '长期有效',
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS quickref (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            icon TEXT DEFAULT '📌',
            items TEXT DEFAULT '[]',
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS op_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            detail TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    db.commit()

    # 迁移：给已有数据库添加 image_url 列
    for table in ['pvp_guides', 'explore_guides']:
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN image_url TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # 列已存在

    if cur.execute("SELECT COUNT(*) FROM pvp_guides").fetchone()[0] == 0:
        seed_data(db)
    db.close()

def seed_data(db):
    # 种子数据已清空，数据库从空白开始
    # 通过管理后台（/admin）手动添加内容
    pass

def _seed_data_old(db):
    """旧种子数据，已弃用，仅保留供参考"""
    cur = db.cursor()
    pvp_guides = [
        ('武道对决上分指南', '1v1排位赛上分全攻略，从青铜到巅峰', '⚔️', '1v1',
         json.dumps(['武道对决','1v1','排位','上分'], ensure_ascii=False), 'hot',
         '<h3>武道对决 — 1v1排位赛</h3><p>武道对决是带自身装备铭文的1v1排位模式，有完整段位系统，最高段位可获得<strong>限定皮肤</strong>。</p><h3>核心机制</h3><p>1. 装备和铭文带入对局，赛前配装至关重要</p><p>2. 段位从青铜到巅峰，每赛季结算奖励</p><p>3. 地图小，节奏快，考验个人操作</p><h3>推荐英雄</h3><p><strong>铠</strong> — 魔铠继承者，近战爆发高，对线压制力强</p><p><strong>花木兰</strong> — 双形态切换，灵活多变</p><p><strong>东方曜</strong> — 星辰之力，多段位移，操作上限极高</p><h3>配装思路</h3><p>核心输出装 + 韧性鞋 + 保命装（复活甲/名刀），根据对手灵活调整。</p>',
         ''),
        ('孤身论决 — 公平1v1竞技', '统一配置纯操作对决，真正的技术较量', '🤺', '1v1',
         json.dumps(['孤身论决','1v1','公平竞技','操作'], ensure_ascii=False), 'new',
         '<h3>孤身论决 — 公平1v1</h3><p>孤身论决是真正的公平竞技，所有玩家<strong>统一配置</strong>，纯靠操作和意识取胜。</p><h3>与武道对决的区别</h3><p>1. 无装备差异，无铭文差异</p><p>2. 所有英雄属性平衡</p><p>3. 纯粹的技术较量</p><h3>核心技巧</h3><p><strong>走位</strong> — 利用地形和距离控制，躲避关键技能</p><p><strong>时机</strong> — 抓住对手技能CD空档期反击</p><p><strong>心理</strong> — 预判对手走位和技能释放</p><h3>推荐练习英雄</h3><p>铠、花木兰等操作上限高的英雄在公平模式下更能发挥技术优势。</p>',
         ''),
        ('协战争魁 — 4v4团队攻略', '四人组队争夺中立资源，摧毁对方基地', '🛡️', '4v4',
         json.dumps(['协战争魁','4v4','团队','配合'], ensure_ascii=False), '',
         '<h3>协战争魁 — 4v4团队竞技</h3><p>4v4模式核心是<strong>中立资源争夺</strong>和团队配合，最终摧毁对方基地获胜。</p><h3>阵容搭配</h3><p>推荐阵容：1对抗（前排）+ 2强攻（输出）+ 1辅助（治疗/控制）</p><p>对抗类：铠、花木兰 — 前线承伤，嘲讽控制</p><p>强攻类：东方曜、伽罗 — 高爆发输出</p><p>辅助类：冷春 — 增益、治疗</p><h3>战术要点</h3><p>1. 开局抢占中立资源点</p><p>2. 辅助保护输出位，对抗位吸引火力</p><p>3. 控制技能链配合，打出控制衔接</p><p>4. 注意小地图，防止被偷家</p>',
         ''),
        ('PK模式全解析', '1v1/3v3/5v5多种规模对战', '🏟️', 'general',
         json.dumps(['PK模式','1v1','3v3','5v5'], ensure_ascii=False), '',
         '<h3>PK模式 — 多种规模对战</h3><p>PK模式支持<strong>1v1、3v3、5v5</strong>三种规模，节奏紧凑以摧毁水晶定胜负。</p><h3>1v1 PK</h3><p>快速单挑，考验个人操作，适合练习英雄和热身</p><h3>3v3 PK</h3><p>小规模团队战，需要基本的配合意识</p><h3>5v5 PK</h3><p>完整团队对抗，需要明确分工和战术执行</p><h3>通用技巧</h3><p>1. 熟悉所有英雄技能，知己知彼</p><p>2. 元素反应（冰+火+雷）可触发额外伤害</p><p>3. 格挡反击和精准闪避是高手分水岭</p>',
         ''),
        ('PVP通用战斗技巧', '从基础到进阶的PVP操作指南', '💡', 'general',
         json.dumps(['通用','战斗','技巧','进阶'], ensure_ascii=False), 'hot',
         '<h3>PVP通用战斗技巧</h3><h3>基础操作</h3><p><strong>浮空连击</strong>：轻攻击接重击触发浮空，空中接技能打出完整连段</p><p><strong>格挡反击</strong>：在对手攻击瞬间格挡，反击造成额外伤害</p><p><strong>精准闪避</strong>：闪避时机正确可触发完美闪避，获得短暂无敌帧</p><h3>进阶技巧</h3><p><strong>破势连招</strong>：连续攻击积累破势值，满值触发处决终结</p><p><strong>牵云索</strong>：空中位移工具，用于规避范围伤害和调整位置</p><p><strong>元素反应</strong>：冰+火=融化（增伤），火+雷=超载（AOE），冰+雷=超导（减防）</p><h3>意识提升</h3><p>1. 时刻关注小地图</p><p>2. 记住对手关键技能CD</p><p>3. 控制视野和资源点</p>',
         ''),
    ]
    for g in pvp_guides:
        cur.execute("INSERT INTO pvp_guides (title,description,icon,category,tags,badge,content,video_url) VALUES (?,?,?,?,?,?,?,?)", g)

    explore_guides = [
        ('稷下学院全探索指南', '稷下新生必读，学院区域完整攻略', '🏫', 'map',
         json.dumps(['稷下','学院','新手','入门'], ensure_ascii=False), 'hot',
         '<h3>稷下学院 — 王者大陆核心区域</h3><p>稷下是三大学院环<strong>通天塔</strong>而建的核心求学圣地，也是玩家初入王者大陆的第一站。</p><h3>重要地点</h3><p><strong>通天塔</strong> — 学院地标，顶楼有观景台和隐藏宝箱</p><p><strong>三大学院</strong> — 武道院、墨家院、阴阳院，各有专属任务和收集品</p><p><strong>学院广场</strong> — 每日任务接取点，NPC商人聚集地</p><h3>收集要点</h3><p>1. 通天塔每层都有隐藏宝箱，需要牵云索到达高层</p><p>2. 三大学院图书馆各有古籍残卷</p><p>3. 学院后山有秘密洞穴，需要完成前置任务开启</p>',
         ''),
        ('观星群山解密攻略', '观星台星象解密，隐藏宝箱位置', '🌟', 'map',
         json.dumps(['观星群山','解密','宝箱','星象'], ensure_ascii=False), 'new',
         '<h3>观星群山 — 星象解密区域</h3><p>观星台是诸葛亮的修行之地，月升时星象最为清晰。</p><h3>星象解密</h3><p>1. 观星台顶部有星象盘，需要按照特定顺序点亮星位</p><p>2. 星象线索散落在群山各处石碑上</p><p>3. 完成解密可获得隐藏共鸣英雄和稀有武器</p><h3>关键位置</h3><p><strong>观星台顶层</strong> — 星象盘所在地</p><p><strong>星陨谷</strong> — 三块星象石碑</p><p><strong>月隐潭</strong> — 水下洞穴藏有宝箱</p>',
         ''),
        ('奇门秘境 — 奇门水榭攻略', '诸葛亮毕业大作，机关解密全流程', '🏯', 'map',
         json.dumps(['奇门秘境','奇门水榭','解密','机关'], ensure_ascii=False), '',
         '<h3>奇门秘境 — 诸葛亮的毕业大作</h3><p>奇门水榭是诸葛亮在稷下的毕业作品，藏于溪谷深处，布满机关和谜题。</p><h3>核心机关</h3><p>1. <strong>水门机关</strong> — 需要按照水位高低依次开启</p><p>2. <strong>八卦阵</strong> — 八个方位的石台需按正确顺序激活</p><p>3. <strong>水镜谜题</strong> — 利用水面反射找到隐藏通道</p><h3>奖励</h3><p>通关获得<strong>奇门武器图纸</strong>和大量环金</p>',
         ''),
        ('秘禁之地BOSS攻略', '秘禁阁精英怪与BOSS打法详解', '💀', 'boss',
         json.dumps(['秘禁之地','BOSS','战斗','组队'], ensure_ascii=False), 'hot',
         '<h3>秘禁之地 — 高难度战斗区域</h3><p>秘禁阁所在的神秘危险之地，盘踞着强大的精英怪和BOSS。</p><h3>主要BOSS</h3><p><strong>禁阁守卫</strong> — 拥有韧性条和可破坏部位，优先攻击头部弱点</p><p><strong>深渊魔将</strong> — 二阶段狂暴，需要辅助及时给盾</p><h3>组队配置建议</h3><p>1对抗（拉仇恨）+ 2强攻（输出）+ 1辅助（治疗解控）</p><h3>机制要点</h3><p>1. BOSS韧性条打空前免疫控制，用破势连招快速削减</p><p>2. 可破坏部位破坏后BOSS进入虚弱状态</p><p>3. 注意躲避范围AOE，牵云索可规避</p>',
         ''),
        ('织梦原野探索路线', '丰云野→织梦原→界北→梦语湖最优路线', '🌾', 'map',
         json.dumps(['织梦原野','路线','收集','探索'], ensure_ascii=False), '',
         '<h3>织梦原野 — 田园牧歌与商业枢纽</h3><p>织梦原野包含丰云野、织梦原、界北、梦语湖四个子区域，是稷下的商业中心和交通枢纽。</p><h3>推荐路线</h3><p><strong>丰云野</strong>（起点）→ 完成商人支线 → <strong>织梦原</strong>（商业区补给）→ <strong>梦语湖</strong>（湖底宝箱）→ <strong>界北</strong>（边境探索）</p><h3>不可错过</h3><p>1. 丰云野的风车顶宝箱（牵云索上去）</p><p>2. 织梦原市集有稀有材料商人</p><p>3. 梦语湖水下有隐藏洞穴</p>',
         ''),
        ('地下世界 — 沧渊迷踪', '天柱墟与沧渊迷踪全探索', '🕳️', 'map',
         json.dumps(['地下世界','天柱墟','沧渊迷踪','遗迹'], ensure_ascii=False), '',
         '<h3>地下世界 — 埋藏于地下的秘密</h3><p>地下世界分为<strong>天柱墟</strong>和<strong>沧渊迷踪</strong>两大区域，遍布溶洞与青铜遗迹。</p><h3>天柱墟</h3><p>巨大的地下溶洞群，天柱石支撑穹顶。关键收集：青铜器碎片（5片合成古器）</p><h3>沧渊迷踪</h3><p>更深层的青铜遗迹，机关和谜题难度更高。需要完成天柱墟前置任务才能进入。</p><h3>注意事项</h3><p>1. 带足照明道具（部分区域漆黑）</p><p>2. 地下敌人等级较高，建议满级后探索</p><p>3. 沧渊深处有隐藏BOSS</p>',
         ''),
        ('春溪漫滩探索指南', '春溪原与古战场试炼攻略', '🌿', 'map',
         json.dumps(['春溪漫滩','试炼','新手','入门'], ensure_ascii=False), '',
         '<h3>春溪漫滩 — 稷下门户</h3><p>春溪漫滩是稷下的入口区域，包含<strong>春溪原</strong>和<strong>春溪古战场</strong>，是学子入学试炼之地。</p><h3>入学试炼</h3><p>1. 基础战斗试炼 — 通过后解锁共鸣系统</p><p>2. 探索试炼 — 在春溪原找到三件遗失的古物</p><p>3. 古战场试炼 — 击败试炼傀儡</p><h3>收集</h3><p>春溪原的花海中有隐藏的唤灵生物可捕捉</p>',
         ''),
        ('唤灵系统捕获指南', '野外唤灵生物位置与捕捉技巧', '🐉', 'collection',
         json.dumps(['唤灵','捕捉','伙伴','收集'], ensure_ascii=False), 'new',
         '<h3>唤灵系统 — 野外生物伙伴</h3><p>玩家可在野外捕捉生物作为战斗伙伴，提供护盾、治疗等辅助效果。</p><h3>可捕捉唤灵</h3><p><strong>春溪狐</strong>（春溪原）— 提供移速加成</p><p><strong>星陨灵</strong>（观星群山）— 提供护盾</p><p><strong>水镜蝶</strong>（梦语湖）— 提供治疗</p><p><strong>岩甲龟</strong>（地下世界）— 提供减伤</p><h3>捕捉技巧</h3><p>1. 先削弱目标生物（不能击杀）</p><p>2. 使用唤灵索进行捕捉</p><p>3. 稀有唤灵有刷新时间，需要等待</p>',
         ''),
        ('武器锻造与配装攻略', '枪剑锤弓四类武器深度解析', '🔨', 'collection',
         json.dumps(['武器','锻造','配装','装备'], ensure_ascii=False), 'hot',
         '<h3>武器系统 — 四类武器深度解析</h3><p>武器分为<strong>枪、剑、锤、弓</strong>四类，各有独立打法路线。</p><h3>枪</h3><p>中距离，突刺和位移能力强，适合灵活打法。推荐英雄：东方曜</p><h3>剑</h3><p>近战均衡，连招流畅，适用面最广。推荐英雄：铠、花木兰</p><h3>锤</h3><p>重武器，高伤害低攻速，附带击飞和破防。适合对抗类英雄</p><h3>弓</h3><p>远程物理，高爆发低防御，需要走位。推荐英雄：伽罗</p><h3>锻造建议</h3><p>优先升级主武器到当前等级上限，材料优先投入主力英雄的武器。</p>',
         ''),
    ]
    for g in explore_guides:
        cur.execute("INSERT INTO explore_guides (title,description,icon,category,tags,badge,content,video_url) VALUES (?,?,?,?,?,?,?,?)", g)

    codes_data = [
        ('WZRY2026', '开服庆典礼包', '环金*500 + 云游金*100 + 进阶石*5', '2026年12月31日'),
        ('YS666', '新手专属礼包', '共鸣英雄体验卡*3 + 环金*200', '长期有效'),
        ('YS888', '探索助力礼包', '云游金*300 + 唤灵索*10', '2026年8月31日'),
        ('SVIP999', '豪华开服礼', '晶珀*300 + 环金*1000 + 武器强化石*20', '2026年6月30日'),
    ]
    for c in codes_data:
        cur.execute("INSERT INTO codes (code,description,reward,expiry) VALUES (?,?,?,?)", c)

    quickref_data = [
        ('每日必做清单', '📋', json.dumps([
            '完成所有日常任务（环金+经验）',
            '挑战秘禁之地BOSS（装备材料）',
            '参加1场武道对决（段位积分）',
            '探索一个区域收集品（云游金）',
            '唤灵喂食（提升唤灵等级）',
            '查看商店刷新（稀有材料）'
        ], ensure_ascii=False)),
        ('PVP段位等级', '🏆', json.dumps([
            '青铜 → 白银 → 黄金 → 铂金 → 钻石 → 星耀 → 巅峰',
            '每个大段位分3个小段',
            '赛季结算按最高段位发放奖励',
            '巅峰段位获得限定皮肤'
        ], ensure_ascii=False)),
        ('元素反应表', '🔥', json.dumps([
            '冰 + 火 = 融化（额外50%伤害）',
            '火 + 雷 = 超载（范围爆炸）',
            '冰 + 雷 = 超导（降低防御30%）',
            '水 + 雷 = 感电（持续伤害）',
            '水 + 冰 = 冻结（控制敌人）'
        ], ensure_ascii=False)),
        ('常用术语', '💬', json.dumps([
            '共鸣 — 切换操控英雄的系统',
            '唤灵 — 野外捕捉的战斗伙伴',
            '牵云索 — 空中位移工具',
            '破势 — 连续攻击积累的终结技',
            '韧性条 — 精英/BOSS的控制免疫条',
            '环金 — 养成通用货币',
            '云游金 — 养成通用货币',
            '晶珀 — 外观货币（免费获取）',
            '璇晶 — 外观货币（仅付费）'
        ], ensure_ascii=False)),
    ]
    for q in quickref_data:
        cur.execute("INSERT INTO quickref (title,icon,items) VALUES (?,?,?)", q)

    db.commit()

# ==================== 认证装饰器 ====================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': '未登录'}), 401
            return app.send_static_file('admin.html')
        return f(*args, **kwargs)
    return decorated

# ==================== API 数据接口 ====================

@app.route('/api/data/<table>')
def api_get_data(table):
    allowed = ['pvp_guides', 'explore_guides', 'codes', 'quickref']
    if table not in allowed:
        return jsonify({'error': 'Invalid table'}), 400
    db = get_db()
    rows = db.execute(f"SELECT * FROM {table} ORDER BY sort_order, id").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        for key in ['tags', 'items']:
            if key in item and item[key] and isinstance(item[key], str):
                try:
                    item[key] = json.loads(item[key])
                except:
                    pass
        result.append(item)
    return jsonify(result)

# ==================== 管理后台认证 ====================

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    ip = request.remote_addr
    now = datetime.now()
    if ip in login_attempts:
        attempts, lock_until = login_attempts[ip]
        if lock_until and now < lock_until:
            remaining = int((lock_until - now).total_seconds())
            return jsonify({'success': False, 'error': f'登录过于频繁，请{remaining}秒后重试'}), 429
    data = request.get_json()
    if data.get('username') == ADMIN_USERNAME and data.get('password') == ADMIN_PASSWORD:
        login_attempts.pop(ip, None)
        session['logged_in'] = True
        op_log('login', '管理员登录')
        return jsonify({'success': True})
    attempts, _ = login_attempts.get(ip, [0, None])
    attempts += 1
    if attempts >= 5:
        login_attempts[ip] = [attempts, now + timedelta(minutes=5)]
        return jsonify({'success': False, 'error': '登录失败次数过多，请5分钟后再试'}), 429
    login_attempts[ip] = [attempts, None]
    return jsonify({'success': False, 'error': '账号或密码错误'}), 401

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('logged_in', None)
    return jsonify({'success': True})

@app.route('/api/admin/check')
def admin_check():
    return jsonify({'logged_in': bool(session.get('logged_in'))})

# ==================== 管理后台 CRUD ====================

ADMIN_TABLES = ['pvp_guides', 'explore_guides', 'codes', 'quickref']
JSON_FIELDS = ['tags', 'items']

@app.route('/api/admin/<table>', methods=['POST'])
@login_required
def admin_create(table):
    if table not in ADMIN_TABLES:
        return jsonify({'error': 'Invalid table'}), 400
    data = request.get_json()
    db = get_db()
    columns = [k for k in data.keys() if k != 'id']
    for col in columns:
        if col in JSON_FIELDS and isinstance(data[col], (list, dict)):
            data[col] = json.dumps(data[col], ensure_ascii=False)
    placeholders = ','.join(['?'] * len(columns))
    cols_sql = ','.join(columns)
    vals = [data[k] for k in columns]
    cur = db.execute(f"INSERT INTO {table} ({cols_sql}) VALUES ({placeholders})", vals)
    db.commit()
    op_log('create', f'{table}: {data.get("title", data.get("code", data.get("name", "")))}')
    return jsonify({'success': True, 'id': cur.lastrowid})

@app.route('/api/admin/<table>/<int:id>', methods=['PUT'])
@login_required
def admin_update(table, id):
    if table not in ADMIN_TABLES:
        return jsonify({'error': 'Invalid table'}), 400
    data = request.get_json()
    db = get_db()
    for col in list(data.keys()):
        if col in JSON_FIELDS and isinstance(data[col], (list, dict)):
            data[col] = json.dumps(data[col], ensure_ascii=False)
    sets = ','.join([f"{k}=?" for k in data.keys()])
    vals = list(data.values())
    db.execute(f"UPDATE {table} SET {sets} WHERE id=?", vals + [id])
    db.commit()
    op_log('update', f'{table} id={id}')
    return jsonify({'success': True})

@app.route('/api/admin/<table>/<int:id>', methods=['DELETE'])
@login_required
def admin_delete(table, id):
    if table not in ADMIN_TABLES:
        return jsonify({'error': 'Invalid table'}), 400
    db = get_db()
    db.execute(f"DELETE FROM {table} WHERE id=?", [id])
    db.commit()
    op_log('delete', f'{table} id={id}')
    return jsonify({'success': True})

# ==================== 批量导入 ====================

IMPORT_FIELDS = {
    'pvp_guides': ['title', 'description', 'content', 'icon', 'image_url', 'category', 'tags', 'badge', 'video_url', 'sort_order'],
    'explore_guides': ['title', 'description', 'content', 'icon', 'image_url', 'category', 'tags', 'badge', 'video_url', 'sort_order'],
    'codes': ['code', 'description', 'reward', 'expiry', 'is_active', 'sort_order'],
    'quickref': ['title', 'icon', 'items', 'sort_order'],
}

TEMPLATE_EXAMPLES = {
    'pvp_guides': ['攻略标题', '简介描述', '<h3>内容</h3>', '⚔️', '', 'general', 'PVP|技巧', '', '', '0'],
    'explore_guides': ['探索标题', '简介描述', '<h3>内容</h3>', '🗺️', '', 'map', '探索|收集', '', '', '0'],
    'codes': ['CODE123', '兑换码描述', '奖励内容', '2026-12-31', '1', '0'],
    'quickref': ['速查标题', '📋', '条目1|条目2|条目3', '0'],
}

JSON_ARRAYS = ['tags', 'items']

@app.route('/api/admin/template/<table>')
@login_required
def download_template(table):
    if table not in IMPORT_FIELDS:
        return jsonify({'error': 'Invalid table'}), 400
    output = io.StringIO()
    writer = csv.writer(output)
    fields = IMPORT_FIELDS[table]
    writer.writerow(fields)
    writer.writerow(TEMPLATE_EXAMPLES.get(table, [''] * len(fields)))
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename={table}_template.csv'}
    )

@app.route('/api/admin/import', methods=['POST'])
@login_required
def admin_import():
    table = request.form.get('table')
    if table not in IMPORT_FIELDS:
        return jsonify({'error': 'Invalid table'}), 400
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file'}), 400
    try:
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        fields = IMPORT_FIELDS[table]
    except Exception as e:
        return jsonify({'error': f'CSV解析失败: {str(e)}'}), 400

    db = get_db()
    success = 0
    errors = []
    for i, row in enumerate(reader):
        try:
            data = {}
            for field in fields:
                val = (row.get(field, '') or '').strip()
                if field in JSON_ARRAYS:
                    val = json.dumps([v.strip() for v in val.split('|') if v.strip()], ensure_ascii=False) if val else '[]'
                elif field in ('sort_order', 'is_active'):
                    val = int(val) if val else 0
                data[field] = val
            cols = ','.join(data.keys())
            placeholders = ','.join(['?'] * len(data))
            db.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(data.values()))
            success += 1
        except Exception as e:
            errors.append(f'第{i+1}行: {str(e)}')
    db.commit()
    return jsonify({'success': True, 'inserted': success, 'errors': errors})

# ==================== 批量删除 ====================

@app.route('/api/admin/batch-delete', methods=['POST'])
@login_required
def admin_batch_delete():
    data = request.get_json()
    table = data.get('table')
    ids = data.get('ids', [])
    if table not in ADMIN_TABLES:
        return jsonify({'error': 'Invalid table'}), 400
    if not ids or not isinstance(ids, list):
        return jsonify({'error': 'No ids'}), 400
    db = get_db()
    ph = ','.join(['?'] * len(ids))
    db.execute(f"DELETE FROM {table} WHERE id IN ({ph})", ids)
    db.commit()
    op_log('batch_delete', f'{table} ({len(ids)}条)')
    return jsonify({'success': True, 'deleted': len(ids)})

# ==================== 文件上传 / 媒体库 ====================

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_TYPES = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'mp4', 'webm', 'mov', 'mp3', 'wav'}

def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/api/admin/upload', methods=['POST'])
@login_required
def admin_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file'}), 400
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_TYPES:
        return jsonify({'error': f'不支持: .{ext}'}), 400
    ensure_upload_dir()
    import uuid
    fname = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(UPLOAD_DIR, fname))
    return jsonify({'success': True, 'url': f'/uploads/{fname}', 'filename': fname})

@app.route('/api/admin/media')
@login_required
def admin_media():
    ensure_upload_dir()
    files = []
    for f in sorted(os.listdir(UPLOAD_DIR), reverse=True):
        fp = os.path.join(UPLOAD_DIR, f)
        if os.path.isfile(fp):
            ext = f.rsplit('.', 1)[-1].lower() if '.' in f else ''
            files.append({
                'filename': f,
                'url': f'/uploads/{f}',
                'size': os.path.getsize(fp),
                'type': 'video' if ext in ('mp4', 'webm', 'mov') else 'image'
            })
    return jsonify(files)

@app.route('/api/admin/media/<filename>', methods=['DELETE'])
@login_required
def admin_media_delete(filename):
    fp = os.path.join(UPLOAD_DIR, os.path.basename(filename))
    if os.path.isfile(fp):
        os.remove(fp)
    return jsonify({'success': True})

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ==================== 数据导出 / 恢复 ====================

@app.route('/api/admin/export')
@login_required
def admin_export():
    db = get_db()
    backup = {}
    for t in ADMIN_TABLES:
        rows = db.execute(f"SELECT * FROM {t} ORDER BY id").fetchall()
        backup[t] = [dict(r) for r in rows]
    return jsonify(backup)

@app.route('/api/admin/import-data', methods=['POST'])
@login_required
def admin_import_data():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    try:
        backup = json.loads(file.read().decode('utf-8'))
    except Exception as e:
        return jsonify({'error': f'JSON解析失败: {str(e)}'}), 400
    db = get_db()
    restored = 0
    for table, rows in backup.items():
        if table not in ADMIN_TABLES or not rows:
            continue
        db.execute(f"DELETE FROM {table}")
        for row in rows:
            item = {k: v for k, v in row.items() if k != 'id' and k != 'created_at'}
            cols = ','.join(item.keys())
            ph = ','.join(['?'] * len(item))
            db.execute(f"INSERT INTO {table} ({cols}) VALUES ({ph})", list(item.values()))
            restored += 1
    db.commit()
    return jsonify({'success': True, 'restored': restored})

# ==================== 操作日志 ====================

def op_log(action, detail=''):
    try:
        db = get_db()
        db.execute("INSERT INTO op_log (action, detail) VALUES (?, ?)", [action, detail])
        db.commit()
    except:
        pass

# ==================== 统计 API ====================

@app.route('/api/admin/stats')
@login_required
def admin_stats():
    db = get_db()
    stats = {}
    for t in ADMIN_TABLES:
        row = db.execute(f"SELECT COUNT(*) as cnt, MAX(created_at) as latest FROM {t}").fetchone()
        stats[t] = {'count': row['cnt'], 'latest': row['latest']}
    logs = db.execute("SELECT * FROM op_log ORDER BY id DESC LIMIT 20").fetchall()
    stats['logs'] = [dict(r) for r in logs]
    return jsonify(stats)

# ==================== 复制条目 ====================

@app.route('/api/admin/<table>/<int:id>/duplicate', methods=['POST'])
@login_required
def admin_duplicate(table, id):
    if table not in ADMIN_TABLES:
        return jsonify({'error': 'Invalid table'}), 400
    db = get_db()
    row = db.execute(f"SELECT * FROM {table} WHERE id=?", [id]).fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    item = dict(row)
    item.pop('id', None)
    item.pop('created_at', None)
    for name_field in ['title', 'code']:
        if name_field in item and item[name_field]:
            item[name_field] = str(item[name_field]) + ' (副本)'
            break
    columns = list(item.keys())
    placeholders = ','.join(['?'] * len(columns))
    cols_sql = ','.join(columns)
    vals = [item[k] for k in columns]
    cur = db.execute(f"INSERT INTO {table} ({cols_sql}) VALUES ({placeholders})", vals)
    db.commit()
    op_log('duplicate', f'{table} id={id} → {cur.lastrowid}')
    return jsonify({'success': True, 'id': cur.lastrowid})

# ==================== 批量排序 ====================

@app.route('/api/admin/<table>/sort', methods=['POST'])
@login_required
def admin_batch_sort(table):
    if table not in ADMIN_TABLES:
        return jsonify({'error': 'Invalid table'}), 400
    data = request.get_json()
    items = data.get('items', [])
    db = get_db()
    for item in items:
        db.execute(f"UPDATE {table} SET sort_order=? WHERE id=?", [item['sort_order'], item['id']])
    db.commit()
    op_log('sort', f'{table} 排序更新 ({len(items)}条)')
    return jsonify({'success': True})

# ==================== 置顶/取消置顶 ====================

@app.route('/api/admin/<table>/<int:id>/toggle-top', methods=['POST'])
@login_required
def admin_toggle_top(table, id):
    if table not in ADMIN_TABLES:
        return jsonify({'error': 'Invalid table'}), 400
    db = get_db()
    row = db.execute(f"SELECT sort_order FROM {table} WHERE id=?", [id]).fetchone()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    new_val = 0 if row['sort_order'] else 9999
    db.execute(f"UPDATE {table} SET sort_order=? WHERE id=?", [new_val, id])
    db.commit()
    op_log('toggle_top', f'{table} id={id} sort_order={new_val}')
    return jsonify({'success': True, 'sort_order': new_val})

# ==================== 静态文件 ====================

@app.route('/')
def index():
    return '<h2>API 服务运行中</h2><p>前台页面请访问 GitHub Pages。后台管理：<a href="/admin">/admin</a></p>'

@app.route('/admin')
def admin():
    with open('admin.html', 'r', encoding='utf-8') as f:
        return f.read()

# ==================== 启动 ====================

init_db()

if __name__ == '__main__':
    print("=" * 50)
    print("  王者荣耀世界攻略站 API 已启动")
    pri