#!/usr/bin/env python3
"""王者荣耀世界攻略站 - 后端 + 管理后台"""

import json
import sqlite3
import csv
import io
import os
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, session, g, Response
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
ADMIN_USERNAME = 'site_admin_2026'
ADMIN_PASSWORD = 'K9xP!7qR#3zL@2sN$5aM'

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
        CREATE TABLE IF NOT EXISTS heroes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subtitle TEXT DEFAULT '',
            icon TEXT DEFAULT '🗡️',
            rarity TEXT DEFAULT 'R',
            badge TEXT DEFAULT '',
            description TEXT DEFAULT '',
            image_url TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            stats TEXT DEFAULT '{}',
            skills TEXT DEFAULT '[]',
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            icon TEXT DEFAULT '📦',
            rarity TEXT DEFAULT 'R',
            category TEXT DEFAULT 'material',
            tags TEXT DEFAULT '[]',
            details TEXT DEFAULT '',
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS guides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            content TEXT DEFAULT '',
            icon TEXT DEFAULT '📖',
            category TEXT DEFAULT 'general',
            tags TEXT DEFAULT '[]',
            badge TEXT DEFAULT '',
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS maps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            content TEXT DEFAULT '',
            icon TEXT DEFAULT '🗺️',
            tags TEXT DEFAULT '[]',
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
    ''')
    db.commit()

    # 种子数据
    if cur.execute("SELECT COUNT(*) FROM heroes").fetchone()[0] == 0:
        seed_data(db)
    db.close()

def seed_data(db):
    cur = db.cursor()
    heroes = [
        ('赵云', '龙胆将军', '🗡️', 'SSR', 'new',
         '常山赵子龙，枪出如龙。赵云的技能组合兼具位移与爆发，是战场上最灵活的战士之一。',
         json.dumps(['战士', '突进', '爆发'], ensure_ascii=False),
         json.dumps({'生命': 'A+', '攻击': 'S', '防御': 'B', '速度': 'S', '难度': 'A'}, ensure_ascii=False),
         json.dumps([
             {'name': '龙胆', 'desc': '被动：赵云每次释放技能后提升10%移动速度，持续2秒，可叠加2层。'},
             {'name': '惊雷之龙', 'desc': '赵云向前突刺，对路径上的敌人造成物理伤害，命中后减少该技能1秒冷却。'},
             {'name': '破云之龙', 'desc': '赵云连续刺击前方区域4次，每次造成物理伤害，最后一击附带击飞效果。'},
             {'name': '天翔之龙', 'desc': '赵云跃向空中，短暂延迟后轰击目标区域，造成大量物理伤害并击飞敌人。'}
         ], ensure_ascii=False)),
        ('孙尚香', '千金射手', '🏹', 'SSR', 'hot',
         '江东大小姐，火炮在手天下我有。远程物理输出天花板，拥有极强的单体爆发能力。',
         json.dumps(['射手', '爆发', '远程'], ensure_ascii=False),
         json.dumps({'生命': 'C', '攻击': 'SS', '防御': 'C', '速度': 'B', '难度': 'B'}, ensure_ascii=False),
         json.dumps([
             {'name': '千金弩', 'desc': '被动：孙尚香脱离战斗后，下一次普通攻击造成额外伤害并附带减速。'},
             {'name': '翻滚突袭', 'desc': '向前翻滚一段距离，强化下次普攻，增加射程和伤害。'},
             {'name': '红莲爆弹', 'desc': '投掷一枚爆弹，对目标区域敌人造成伤害并减速。'},
             {'name': '究极弩炮', 'desc': '蓄力后发射一枚超远程炮弹，对直线上的所有敌人造成巨额伤害。'}
         ], ensure_ascii=False)),
        ('李白', '青莲剑仙', '⚔️', 'SSR', '',
         '大河之剑天上来。李白拥有多段位移和高额爆发，是最具操作感的刺客英雄。',
         json.dumps(['刺客', '位移', '爆发'], ensure_ascii=False),
         json.dumps({'生命': 'C', '攻击': 'SS', '防御': 'D', '速度': 'SS', '难度': 'SS'}, ensure_ascii=False),
         json.dumps([
             {'name': '侠客行', 'desc': '被动：李白每4次普攻后进入侠客行状态，提升攻击力5秒。'},
             {'name': '将进酒', 'desc': '向指定方向突进两次，第三次回到原地。每次突进对路径敌人造成伤害。'},
             {'name': '神来之笔', 'desc': '以自身为中心释放剑气，对周围敌人造成伤害并减速。'},
             {'name': '青莲剑歌', 'desc': '化身剑气穿梭于战场，对范围内所有敌人造成5次伤害，期间不可选中。'}
         ], ensure_ascii=False)),
        ('貂蝉', '绝世舞姬', '💃', 'SR', '',
         '闭月羞花之貌，舞动倾城之姿。法术型辅助，拥有强大的控制能力和治疗能力。',
         json.dumps(['法师', '辅助', '控制'], ensure_ascii=False),
         json.dumps({'生命': 'B', '攻击': 'A', '防御': 'B', '速度': 'A', '难度': 'A'}, ensure_ascii=False),
         json.dumps([
             {'name': '闭月', 'desc': '被动：貂蝉对敌人造成法术伤害时，在敌人身上留下印记，队友攻击该敌人回复生命。'},
             {'name': '落雁', 'desc': '向指定方向抛出花瓣，对命中的第一个敌人造成伤害并魅惑。'},
             {'name': '沉鱼', 'desc': '在目标区域制造幻境，区域内敌人减速，队友加速。'},
             {'name': '羞花', 'desc': '翩翩起舞，持续为周围队友回复生命值，结束时对周围敌人造成伤害。'}
         ], ensure_ascii=False)),
        ('吕布', '无双战神', '🔱', 'SR', '',
         '马中赤兔，人中吕布。近战坦克型战士，拥有极高的生存能力和不俗的伤害。',
         json.dumps(['坦克', '战士', '生存'], ensure_ascii=False),
         json.dumps({'生命': 'SS', '攻击': 'A', '防御': 'S', '速度': 'D', '难度': 'B'}, ensure_ascii=False),
         json.dumps([
             {'name': '饕餮血统', 'desc': '被动：吕布生命值低于50%时，攻击力提升20%，并获得10%吸血。'},
             {'name': '方天画斩', 'desc': '挥动方天画戟横扫前方，造成物理伤害，命中回复生命。'},
             {'name': '无双之盾', 'desc': '获得一个吸收伤害的护盾，持续3秒，护盾结束时对周围敌人造成伤害。'},
             {'name': '魔神降世', 'desc': '跃向目标区域，落地造成范围伤害并击飞，自身获得伤害减免。'}
         ], ensure_ascii=False)),
        ('小乔', '恋之微风', '🌸', 'R', '',
         '江东二乔之一，温柔可人。法术远程输出，拥有极强的范围伤害能力。',
         json.dumps(['法师', '远程', '爆发'], ensure_ascii=False),
         json.dumps({'生命': 'D', '攻击': 'S', '防御': 'D', '速度': 'B', '难度': 'C'}, ensure_ascii=False),
         json.dumps([
             {'name': '治愈微笑', 'desc': '被动：小乔技能命中敌人后，提升自身2%移动速度，可叠加5层。'},
             {'name': '绽放之舞', 'desc': '向前方扇形区域释放飞舞的花瓣，造成法术伤害。'},
             {'name': '甜蜜恋风', 'desc': '在指定位置召唤旋风，对范围内敌人造成持续伤害。'},
             {'name': '星华缭乱', 'desc': '召唤流星雨攻击大范围区域内的敌人，连续降落5波。'}
         ], ensure_ascii=False)),
    ]
    for h in heroes:
        cur.execute("INSERT INTO heroes (name,subtitle,icon,rarity,badge,description,tags,stats,skills) VALUES (?,?,?,?,?,?,?,?,?)", h)

    guides = [
        ('新手入门指南', '从零开始的王者之旅', '📖', 'beginner', json.dumps(['新手', '入门', '必读'], ensure_ascii=False), '',
         '<h3>欢迎来到王者荣耀世界！</h3><p>这篇指南将帮助你快速上手游戏。</p><h3>一、选择你的第一个英雄</h3><p>建议新手优先选择操作难度较低的英雄，如<strong>小乔</strong>或<strong>吕布</strong>。</p><h3>二、熟悉基本操作</h3><p>移动、普攻和技能释放是游戏的核心操作，建议在训练模式中多加练习。</p><h3>三、了解装备系统</h3><p>合理出装是获胜的关键，前期优先发育，中期补输出，后期补防御。</p>'),
        ('赵云深度攻略', '七进七出的龙胆将军', '📖', 'hero', json.dumps(['赵云', '战士', '进阶'], ensure_ascii=False), 'hot',
         '<h3>赵云 — 战场上的常胜将军</h3><p>赵云是游戏中最为灵活的战士英雄，拥有极高的操作上限。</p><h3>技能解析</h3><p><strong>核心技能：惊雷之龙</strong> — 赵云的核心位移技能，可用于追击、逃生和躲避关键技能。</p><h3>连招技巧</h3><p>基础连招：1技能突进 → 2技能输出 → 1技能二段追击 → 大招收割</p><p>进阶连招：1技能穿越 → 大招开团 → 2技能输出 → 1技能调整位置</p><h3>装备推荐</h3><p>核心装备：暗影战斧 + 宗师之力 + 破军</p>'),
        ('资源获取全攻略', '快速养成你的英雄', '📖', 'resource', json.dumps(['养成', '资源', '必读'], ensure_ascii=False), '',
         '<h3>资源获取途径大全</h3><p>合理规划资源获取是快速提升战力的关键。</p><h3>每日必做</h3><p>1. 日常任务：每天完成所有日常任务，获取金币和经验。</p><p>2. 活动副本：每日限时活动副本必刷，掉落稀有材料。</p><h3>周常必做</h3><p>1. 排位赛：每周完成足够的排位场次获取赛季奖励。</p><p>2. 公会战：参与公会战获取大量公会贡献。</p>'),
    ]
    for g in guides:
        cur.execute("INSERT INTO guides (title,description,icon,category,tags,badge,content) VALUES (?,?,?,?,?,?,?)", g)

    resources = [
        ('金币', '游戏中的通用货币，可用于购买英雄和基础装备', '🪙', 'R', 'currency', json.dumps(['货币', '通用'], ensure_ascii=False), '获取途径：日常任务、对战奖励、活动赠送'),
        ('钻石', '稀有货币，可用于购买特殊道具和皮肤', '💎', 'SR', 'currency', json.dumps(['货币', '稀有'], ensure_ascii=False), '获取途径：排位奖励、成就系统、活动赠送'),
        ('经验书', '用于提升英雄等级的基础道具', '📘', 'R', 'material', json.dumps(['养成', '基础'], ensure_ascii=False), '获取途径：副本掉落、日常任务'),
        ('进阶石', '英雄突破等级上限的必需材料', '💠', 'SR', 'material', json.dumps(['养成', '进阶'], ensure_ascii=False), '获取途径：精英副本、活动兑换'),
        ('皮肤精华', '兑换限定皮肤的珍贵材料', '✨', 'SSR', 'material', json.dumps(['皮肤', '珍贵'], ensure_ascii=False), '获取途径：活动赠送、排位商店兑换'),
    ]
    for r in resources:
        cur.execute("INSERT INTO resources (name,description,icon,rarity,category,tags,details) VALUES (?,?,?,?,?,?,?)", r)

    maps_data = [
        ('王者峡谷', '最经典的5v5对战地图，三条兵线加野区', '🗺️', json.dumps(['PVP', '经典'], ensure_ascii=False), '<h3>地图概览</h3><p>王者峡谷是游戏中最核心的对战地图，分为三条主路和四片野区。</p><h3>上路（对抗路）</h3><p>适合战士/坦克英雄，主要任务是稳住兵线和支援团战。</p><h3>中路</h3><p>适合法师英雄，兵线最短，便于快速清线后支援两路。</p><h3>下路（发育路）</h3><p>适合射手英雄，有额外金币加成，是团队的核心输出位置。</p><h3>野区</h3><p>适合刺客/打野英雄，通过击杀野怪获取经验和buff。</p>'),
        ('长平攻防战', '非对称攻城地图，守城与攻城的较量', '🏰', json.dumps(['PVP', '攻城'], ensure_ascii=False), '<h3>地图概览</h3><p>长平攻防战是攻城模式专属地图，分为攻方和守方。</p><h3>攻城方</h3><p>目标：在规定时间内摧毁守方城堡。策略：集中火力突破防线，利用攻城器械。</p><h3>守城方</h3><p>目标：坚守至时间结束。策略：合理分配防守力量，利用城墙优势消耗敌人。</p>'),
    ]
    for m in maps_data:
        cur.execute("INSERT INTO maps (name,description,icon,tags,content) VALUES (?,?,?,?,?)", m)

    codes_data = [
        ('WZRY2025', '周年庆礼包', '金币*500 + 钻石*100 + 经验书*10', '2025年12月31日'),
        ('VIP666', '新手专属礼包', '英雄体验卡*3 + 金币*200', '长期有效'),
        ('SVIP888', '超值礼包', '钻石*300 + 皮肤精华*5', '2025年6月30日'),
    ]
    for c in codes_data:
        cur.execute("INSERT INTO codes (code,description,reward,expiry) VALUES (?,?,?,?)", c)

    quickref_data = [
        ('日常必做清单', '📋', json.dumps([
            '完成所有日常任务（金币+经验）',
            '刷3次精英副本（进阶石）',
            '参加1场排位赛（赛季积分）',
            '领取免费宝箱（随机奖励）',
            '公会签到（公会贡献）'
        ], ensure_ascii=False)),
        ('装备优先级', '⚡', json.dumps([
            '第一件：核心输出装（根据英雄定位）',
            '第二件：鞋子（增加移速）',
            '第三件：补充输出或防御',
            '第四件：破甲/法穿装备',
            '第五件：保命装备（复活甲/名刀）',
            '第六件：根据局势灵活选择'
        ], ensure_ascii=False)),
        ('常见术语', '💬', json.dumps([
            'Gank - 游走抓人',
            'AD - 物理输出',
            'AP - 法术输出',
            'CD - 技能冷却时间',
            'CC - 控制技能',
            'DPS - 每秒伤害输出',
            'Buff - 增益效果',
            'Debuff - 减益效果'
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
    allowed = ['heroes', 'resources', 'guides', 'maps', 'codes', 'quickref']
    if table not in allowed:
        return jsonify({'error': 'Invalid table'}), 400
    db = get_db()
    rows = db.execute(f"SELECT * FROM {table} ORDER BY sort_order, id").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        for key in ['tags', 'stats', 'skills', 'items']:
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
    data = request.get_json()
    if data.get('username') == ADMIN_USERNAME and data.get('password') == ADMIN_PASSWORD:
        session['logged_in'] = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '账号或密码错误'}), 401

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('logged_in', None)
    return jsonify({'success': True})

@app.route('/api/admin/check')
def admin_check():
    return jsonify({'logged_in': bool(session.get('logged_in'))})

# ==================== 管理后台 CRUD ====================

ADMIN_TABLES = ['heroes', 'resources', 'guides', 'maps', 'codes', 'quickref']
JSON_FIELDS = ['tags', 'stats', 'skills', 'items']

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
    return jsonify({'success': True})

@app.route('/api/admin/<table>/<int:id>', methods=['DELETE'])
@login_required
def admin_delete(table, id):
    if table not in ADMIN_TABLES:
        return jsonify({'error': 'Invalid table'}), 400
    db = get_db()
    db.execute(f"DELETE FROM {table} WHERE id=?", [id])
    db.commit()
    return jsonify({'success': True})

# ==================== 批量导入 ====================

IMPORT_FIELDS = {
    'heroes': ['name', 'subtitle', 'icon', 'rarity', 'badge', 'description', 'image_url', 'tags', 'stats', 'skills', 'sort_order'],
    'resources': ['name', 'description', 'icon', 'rarity', 'category', 'tags', 'details', 'sort_order'],
    'guides': ['title', 'description', 'content', 'icon', 'category', 'tags', 'badge', 'sort_order'],
    'maps': ['name', 'description', 'content', 'icon', 'tags', 'sort_order'],
    'codes': ['code', 'description', 'reward', 'expiry', 'is_active', 'sort_order'],
    'quickref': ['title', 'icon', 'items', 'sort_order'],
}

TEMPLATE_EXAMPLES = {
    'heroes': ['赵云', '龙胆将军', '🗡️', 'SSR', 'new', '常山赵子龙，枪出如龙。', '', '战士|突进|爆发', '生命:A+|攻击:S|防御:B|速度:S|难度:A', '龙胆::被动描述|惊雷之龙::向前突刺', '0'],
    'resources': ['金币', '通用货币，可用于购买英雄和基础装备', '🪙', 'R', 'currency', '货币|通用', '获取途径：日常任务、对战奖励', '0'],
    'guides': ['新手入门指南', '从零开始的王者之旅', '<h3>内容</h3>', '📖', 'beginner', '新手|入门|必读', '', '0'],
    'maps': ['王者峡谷', '最经典的5v5对战地图', '<h3>地图详情</h3>', '🗺️', 'PVP|经典', '0'],
    'codes': ['WZRY2025', '周年庆礼包', '金币*500', '2025-12-31', '1', '0'],
    'quickref': ['日常必做', '📋', '完成日常任务|刷副本|公会签到', '0'],
}

JSON_ARRAYS = ['tags', 'items']
JSON_OBJECTS = ['stats']
JSON_SKILLS = ['skills']

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
                elif field in JSON_OBJECTS:
                    obj = {}
                    for pair in val.split(';'):
                        pair = pair.strip()
                        if ':' in pair:
                            k, v = pair.split(':', 1)
                            obj[k.strip()] = v.strip()
                    val = json.dumps(obj, ensure_ascii=False) if obj else '{}'
                elif field in JSON_SKILLS:
                    arr = []
                    for item in val.split('|'):
                        item = item.strip()
                        if '::' in item:
                            name, desc = item.split('::', 1)
                            arr.append({'name': name.strip(), 'desc': desc.strip()})
                    val = json.dumps(arr, ensure_ascii=False) if arr else '[]'
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

# ==================== 静态文件 ====================

@app.route('/')
def index():
    # 前台页面在 GitHub Pages，这里可选跳转
    return '<h2>API 服务运行中</h2><p>前台页面请访问 GitHub Pages。后台管理：<a href="/admin">/admin</a></p>'

@app.route('/admin')
def admin():
    with open('admin.html', 'r', encoding='utf-8') as f:
        return f.read()

# ==================== 启动 ====================

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("  王者荣耀世界攻略站 API 已启动")
    print(f"  后台: http://localhost:5000/admin")
    print(f"  账号: {ADMIN_USERNAME}")
    print("=" * 50)
    # Render 用 gunicorn app:app，本地用 Flask 内置服务器
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
