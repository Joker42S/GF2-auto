# -*- encoding=utf8 -*-
__author__ = "Administrator"

from airtest.core.api import *
from airtest.aircv import *
from airtest.core.settings import Settings as ST
from paddleocr import PaddleOCR
import time

auto_setup(__file__)

dev = device()
ST.OPDELAY = 2
ST.SNAPSHOT_QUALITY = 80

ocr = PaddleOCR(use_angle_cls=False)


def w_touch(target_word, confidence_threshold = 0.8, is_isolating_word = False, region = None):
    match_rect = w_exists(target_word, confidence_threshold, is_isolating_word, region)
    if match_rect:
        w_click(match_rect)
    else:
        print('Cannot find word: ' + target_word)
        raise

def w_click(rect):
    click(getcenter(rect))

def w_exists(target_word, confidence_threshold = 0.8, is_isolating_word = False, region = None, retry = 0):
    for i in range(retry + 1):
        res = find_word_by_ocr(target_word, confidence_threshold, is_isolating_word, region)
        if res:
            return res
        sleep(1)
    return False

def w_wait(target_word, confidence_threshold = 0.8, is_isolating_word = False, timeout = 60, interval = 0.5, region = None):
    sum_time = 0
    match_rect = None
    while sum_time < timeout:
        match_rect = w_exists(target_word, confidence_threshold, is_isolating_word, region)
        if match_rect:
            break
        sleep(interval)
        sum_time += interval
    if not match_rect:
        print(f'Cannot find word after {timeout}s: ' + target_word)
        raise
    return match_rect

def m_touch(*args):
#     dev.mouse_move((1900, 1000))
    return touch(*args)
def m_exists(*args):
#     dev.mouse_move((1900, 1000))
    return exists(*args)
def m_wait(*args):
#     dev.mouse_move((1900, 1000))
    return wait(*args)
def add_offset(rect, offset_x, offset_y):
    new_rect = []
    for i in range(4):
        new_x = rect[i][0] + offset_x
        new_y = rect[i][1] + offset_y
        new_rect.append([new_x, new_y])
    return new_rect
    
def getcenter(rect):
    x = (rect[0][0] + rect[2][0]) / 2
    y = (rect[0][1] + rect[2][1]) / 2
    return [x, y]

def get_ocr_result(region = None):
    screen = G.DEVICE.snapshot()
    if region != None:
        screen = crop_image(screen, region)
    filename = try_log_screen(screen)['screen']
#     filename = snapshot()['screen']
    img_dir = ST.LOG_DIR + '\\' + filename
    result = ocr.ocr(img_dir)[0]
    return result

def find_word_by_ocr(target_word, confidence_threshold = 0.8, is_isolating_word = False, region = None):
    result = get_ocr_result(region)
    match_rect = None
    match_confidence = 0
    if result == None:
        print('No words in image')
        return match_rect
    for ocr_res in result:
        confidence = ocr_res[1][1]
        if confidence < confidence_threshold:
            continue
        if is_isolating_word:
            if ocr_res[1][0] != target_word:
                continue
        elif not target_word in ocr_res[1][0]:
            continue
        #文字匹配成功
        if confidence > match_confidence:
            match_rect = ocr_res[0]
    if match_rect:
        if region is not None:
            match_rect = add_offset(match_rect, region[0], region[1])
        print(f'find word:{target_word}, confidence:{confidence}')
        print(match_rect)
    else:
        print(result)
        print('fail to find word: ' + target_word)
    return match_rect

#通用返回体力值
def get_stamia():
    region = (1415, 37, 1595, 93)
    result = get_ocr_result(region)
    full_text = result[0][1][0]
    print(f'Current stamia: {full_text}')
    stamia_num = int(full_text.split('/')[0])
    return stamia_num
            
#通用获得奖励 如果无奖励则返回false
def collect_reward():
    sleep(2)
    if w_exists('获得道具', retry = 2):
        backarrow_common()
        return True
    else:
        return False

#通用的返回主页
def return_home():
#     #委托 战役
#     try:
#         m_touch(Template(r"tpl1724043062335.png", record_pos=(-0.425, -0.254), resolution=(1600, 900)))
#     except:
#         #班组 公共区
#         m_touch(Template(r"tpl1724043144393.png", record_pos=(-0.422, -0.254), resolution=(1600, 900)))
#     else:
#         pass
    click((125, 75))

#通用战斗
def battle_common(esimated_time = 300, is_surrender = False):
    #等待加载
    for i in range(5):
        sleep(10)
        if not m_exists(Template(r"tpl1724929193896.png", rgb=True, record_pos=(0.101, -0.056), resolution=(1404, 900))):
            break
    for i in range(3):
        sleep(5)
        if m_exists(Template(r"tpl1724037341185.png", record_pos=(0.01, 0.235), resolution=(1569, 900))):
            break
    if is_surrender:
        sleep(2)
        keyevent("{ESC}")
        m_touch(Template(r"tpl1728711100189.png", rgb=True, record_pos=(-0.401, 0.313), resolution=(1270, 900)))
        m_touch(Template(r"tpl1724931266467.png", record_pos=(0.107, 0.111), resolution=(1600, 900)))
        m_touch(Template(r"tpl1724037860299.png", record_pos=(0.33, 0.231), resolution=(1600, 900))) 
        sleep(10)
        #直接失败退出
        return
    m_touch(Template(r"tpl1724037341185.png", record_pos=(0.01, 0.235), resolution=(1569, 900)))
    #跳出场动画
    click((800, 450))
    sleep(10)
    #自动战斗
    dev.key_press('o')
    dev.key_release('o')
    sleep(10)
    _timer_battle = 0
    while True:
        sleep(10)
        if _timer_battle > 5*60 + esimated_time:
            raise
        elif m_exists(Template(r"tpl1724037678163.png", record_pos=(0.331, -0.174), resolution=(1600, 792))):
            m_touch(Template(r"tpl1724037678163.png", record_pos=(0.331, -0.174), resolution=(1600, 792)))
            break
        elif m_exists(Template(r"tpl1724483714783.png", rgb=True, record_pos=(-0.001, -0.207), resolution=(1600, 900))):
            m_touch(Template(r"tpl1724483714783.png", rgb=True, record_pos=(-0.001, -0.207), resolution=(1600, 900)))
            break
        _timer_battle += 10
    #此处可能出现的页面： 段位晋升、
    click((800, 450))
    sleep(2)
    click((800, 450))
    m_touch(Template(r"tpl1724037860299.png", record_pos=(0.33, 0.231), resolution=(1600, 900)))
    sleep(10)

#通用的返回按钮
def backarrow_common():
    click((55, 75))
#     m_touch(Template(r"tpl1724037110631.png", record_pos=(-0.462, -0.324), resolution=(1255, 900)))

#检查是否有体力不足提示
def has_ap_alert():
    if w_exists('情报拼图补充'):
        m_touch(Template(r"tpl1724226645988.png", record_pos=(-0.108, 0.114), resolution=(1600, 900)))
        return True
    else:
        return False

#伤害统计按钮
# m_exists(Template(r"tpl1724037756810.png", record_pos=(-0.438, 0.325), resolution=(1140, 900)))
# m_touch(Template(r"tpl1724037404622.png", record_pos=(0.395, -0.263), resolution=(1569, 900)))
# #自动按钮的位置
# click((1413, 69))
#弹窗的关闭按钮
# m_touch(Template(r"tpl1724037909329.png", record_pos=(0.34, -0.153), resolution=(1600, 900)))

#购买限量商品
def buy_item(is_buyout = False, item_num = 0, item_list = []):
    v_range = 0
    if is_buyout:
        v_range = item_num
    else:
        v_range = len(item_list)
    for i in range(v_range):
        if is_buyout:
            #点击第一个商品的固定位置
            click((386,245))
        else:
            btn_item = w_exists(item_list[i])
            if not btn_item:
                continue
            else:
                w_click(btn_item)
        btn_max = m_exists(Template(r"tpl1742209087579.png", rgb=True, record_pos=(0.209, 0.051), resolution=(1610, 932)))
        btn_buy = m_exists(Template(r"tpl1742209177011.png", rgb=True, record_pos=(0.12, 0.132), resolution=(1610, 932)))
        if btn_max:
            m_touch(btn_max)
        if btn_buy:
            m_touch(btn_buy)
            if m_exists(Template(r"tpl1742209177011.png", rgb=True, record_pos=(0.12, 0.132), resolution=(1610, 932))):
                #购买失败
                backarrow_common()
                break
            collect_reward()
        else:
            backarrow_common()
            if is_buyout:
                #已经卖空
                break

"""
---
邮箱
---
"""
def mailbox():
    if not m_exists(Template(r"tpl1737028627007.png", threshold=0.9000000000000001, record_pos=(-0.443, 0.125), resolution=(1610, 932))):
        return
    m_touch(Template(r"tpl1737028627007.png", threshold=0.9000000000000001, record_pos=(-0.443, 0.125), resolution=(1610, 932)))
    m_touch(Template(r"tpl1737028977397.png", threshold=0.9500000000000002, record_pos=(-0.283, 0.257), resolution=(1610, 932)))

    collect_reward()
    return_home()
    
"""
---
公会战
---
"""
def ally_area():
    w_touch('班组')
    m_touch(Template(r"tpl1724037004746.png", record_pos=(0.188, 0.237), resolution=(1600, 900)))
    try:
        w_touch('领取全部')
        collect_reward()
    except:
        pass
    finally:
        backarrow_common()
        sleep(5)

    m_touch(Template(r"tpl1724037196811.png", record_pos=(0.326, 0.264), resolution=(1467, 900)))
    if w_exists('每日要务已完成'):
        pass
    else:
        m_touch(Template(r"tpl1724037235890.png", record_pos=(0.31, 0.176), resolution=(1467, 900)))
        battle_common(300)
    backarrow_common()
    #公会本入口
    m_touch(Template(r"tpl1724927792450.png", record_pos=(0.384, 0.21), resolution=(1600, 900)))
    if m_exists(Template(r"tpl1724038051306.png", record_pos=(0.367, 0.236), resolution=(1600, 900))) and not m_exists(Template(r"tpl1724927792450.png", record_pos=(0.384, 0.21), resolution=(1600, 900))):
        for i in range(2):
            m_touch(Template(r"tpl1724038051306.png", record_pos=(0.367, 0.236), resolution=(1600, 900)))
            if not m_exists(Template(r"tpl1724927868702.png", record_pos=(0.294, 0.244), resolution=(1600, 900))):
                break
#             m_touch(Template(r"tpl1724930408405.png", rgb=True, record_pos=(-0.445, 0.326), resolution=(1222, 900)))
#             try:
#                 m_touch(Template(r"tpl1724928831936.png", rgb=True, record_pos=(0.204, -0.121), resolution=(1134, 900)))
#                 m_touch(Template(r"tpl1724040944534.png", record_pos=(0.107, 0.12), resolution=(1600, 900)))
#             except:
#                 pass
            m_touch(Template(r"tpl1724038855595.png", record_pos=(0.226, 0.25), resolution=(1564, 900)))
            # #重置后直接选最前面的4个
            click((110, 384))
            click((110+115, 384))
            click((110+115*2, 384))
            click((110+115*3, 384))
            m_touch(Template(r"tpl1724039182987.png", record_pos=(0.422, 0.193), resolution=(1600, 900)))
            zhuzhan_region = (260, 175, 1340, 900)
            w_touch('电导', region = zhuzhan_region)
            w_touch('莱娅', region = zhuzhan_region)
            m_touch(Template(r"tpl1724039310900.png", record_pos=(0.32, 0.187), resolution=(1408, 900)))
            if m_exists(Template(r"tpl1724931239978.png", record_pos=(0.0, -0.126), resolution=(1600, 900))) and w_exists('队伍中有相同角色'):
                m_touch(Template(r"tpl1724931266467.png", record_pos=(0.107, 0.111), resolution=(1600, 900)))
                #补空位
                click((110+115*4, 384))
            m_touch(Template(r"tpl1724038095179.png", record_pos=(0.384, 0.244), resolution=(1600, 900)))
#             if m_exists(Template(r"tpl1724931239978.png", record_pos=(0.0, -0.126), resolution=(1600, 900))) and w_exists('仍有可上阵的位置'):
#                 m_touch(Template(r"tpl1724931266467.png", record_pos=(0.107, 0.111), resolution=(1600, 900)))
            sleep(2)
#             if not m_exists(Template(r"tpl1724927868702.png", record_pos=(0.294, 0.244), resolution=(1600, 900))):
            battle_common(360)
#             else:
#                 break
        w_touch('前线补给')
        try:
            m_touch(Template(r"tpl1739433596338.png", record_pos=(-0.002, 0.132), resolution=(1610, 932)))
            collect_reward()
        except:
            pass
        w_touch('班组表现', region = (400, 100, 1200, 800))
        try:
            m_touch(Template(r"tpl1739433596338.png", record_pos=(-0.002, 0.132), resolution=(1610, 932)))
            collect_reward()
        except:
            pass
        backarrow_common()
    #返回主页
    return_home()


"""
---
公共区
---
"""
def public_area():
    w_touch('公共区')
    w_touch('调度室')
    try:
        w_touch('键领取')
        w_touch('再次派遣')
    except:
        pass
    try:
        touch(Template(r"tpl1742922535723.png", record_pos=(-0.234, 0.18), resolution=(1610, 932)))
        if w_exists('本周派遣收益'):
            btn_collect = w_exists('领取')
            if btn_collect:
                w_click(btn_collect)
                collect_reward()
            backarrow_common()
        else:
            collect_reward()
    except:
        pass
    w_touch('调度收益')
    m_touch(Template(r"tpl1724042868258.png", record_pos=(0.106, 0.221), resolution=(1600, 900)))
    w_touch('资源生产')
    m_touch(Template(r"tpl1724042910758.png", record_pos=(0.308, 0.248), resolution=(1430, 900)))
    collect_reward()
    backarrow_common()
    #返回主页
    return_home()

"""
---
清体力
---
"""
def daily_battle():
    w_touch('战役推进')
    #切回初始页
#     if not m_exists(Template(r"tpl1724237282638.png", threshold=0.6, rgb=True, record_pos=(0.072, -0.254), resolution=(1600, 900))):
#         m_touch(Template(r"tpl1724236408766.png", record_pos=(0.069, -0.256), resolution=(1600, 900)))
    w_touch('模拟作战')
#     click((1468, 76))
    #实兵演习
    w_touch('实兵演习')
    #每周的结算页面
    click((800, 450))
    sleep(1)
    click((800, 450))
    sleep(1)
    click((800, 450))
    sleep(1)
    click((800, 450))
    sleep(1)
    click((800, 450))
    sleep(1)
    click((800, 450))
    m_touch(Template(r"tpl1724040492694.png", record_pos=(0.38, 0.245), resolution=(1600, 900)))
    #每天3次 打1次退2次
    first_battle = True
    for i in range(3):
        m_touch(Template(r"tpl1724225312105.png", record_pos=(0.441, 0.249), resolution=(1600, 900)))
        #刷新次数用尽了
        if m_exists(Template(r"tpl1724236208525.png", record_pos=(0.001, -0.127), resolution=(1600, 900))):
            m_touch(Template(r"tpl1724236220728.png", record_pos=(-0.107, 0.113), resolution=(1600, 900)))
        #直接选中间的对手
        click((800, 450))
        if w_exists('基础防守演习'):
            m_touch(Template(r"tpl1724224751372.png", record_pos=(0.261, 0.124), resolution=(1600, 900)))
            sleep(2)
            #检查次数是否用完
            if w_exists('基础防守演习'):
                backarrow_common()
                break
            else:
                battle_common(10, not first_battle)
                first_battle = False
        else:
            pass
    #关闭选择对手页面
    backarrow_common()
    #领奖励（不领会发邮件，可以跳过）
#     try:
#         m_touch(Template(r"tpl1724040669915.png", record_pos=(-0.191, 0.269), resolution=(1387, 900)))
#         if w_exists('演习补给'):
#             backarrow_common()
#         else:
#             collect_reward()
#     except:
#         pass
    #返回模拟作战页面
    backarrow_common()

    # #首领挑战
    # m_touch(Template(r"tpl1724042286132.png", record_pos=(-0.23, -0.172), resolution=(1365, 900)))
    # # m_touch(Template(r"tpl1724042318400.png", record_pos=(0.339, 0.281), resolution=(1365, 900)))
    # # click((1250, 864))
    # m_touch(Template(r"tpl1724042454950.png", record_pos=(0.215, 0.239), resolution=(1600, 900)))
    # #需要判断是否到达上限
    # m_touch(Template(r"tpl1724040820485.png", record_pos=(0.139, 0.02), resolution=(1600, 900)))
    # m_touch(Template(r"tpl1724040820485.png", record_pos=(0.139, 0.02), resolution=(1600, 900)))
    # m_touch(Template(r"tpl1724042530923.png", record_pos=(0.107, 0.118), resolution=(1600, 900)))


    w_touch('补给作战')
    #金条本
#     m_touch(Template(r"tpl1724040775324.png", record_pos=(0.371, -0.061), resolution=(1600, 900)))
#     for i in range(4):
#         m_touch(Template(r"tpl1724040793103.png", record_pos=(0.261, 0.239), resolution=(1600, 900)))
#         #检查体力
#         if has_ap_alert():
#             pass
#         #判断是否到达上限
#         elif not m_exists(Template(r"tpl1724225998770.png", record_pos=(0.0, -0.134), resolution=(1600, 900))):
#             pass
#         else:
#             m_touch(Template(r"tpl1724040944534.png", record_pos=(0.107, 0.12), resolution=(1600, 900)))
#             collect_reward()
#     backarrow_common()
    #配件本
#     m_touch(Template(r"tpl1724041079905.png", record_pos=(0.186, -0.064), resolution=(1600, 900)))
    #重复刷配件本 直到体力不足30或仓库满 最多十次
#     for i in range(10):
#         m_touch(Template(r"tpl1724040793103.png", record_pos=(0.261, 0.239), resolution=(1600, 900)))
#         #检查体力
#         if has_ap_alert():
#             break
#         elif m_exists(Template(r"tpl1724227350706.png", record_pos=(-0.001, -0.147), resolution=(1600, 900))) and m_exists(Template(r"tpl1725702785010.png", record_pos=(-0.001, -0.1), resolution=(1600, 900))):
#             m_touch(Template(r"tpl1724226363040.png", record_pos=(0.108, 0.166), resolution=(1600, 900)))
#             m_touch(Template(r"tpl1724040944534.png", record_pos=(0.107, 0.12), resolution=(1600, 900)))
#             collect_reward()
#         #配件超过上限
#         elif m_exists(Template(r"tpl1724226299872.png", record_pos=(0.001, -0.127), resolution=(1600, 900))):
#             m_touch(Template(r"tpl1724226323564.png", record_pos=(-0.107, 0.113), resolution=(1600, 900)))
#             break
#         else:
#             raise
#     backarrow_common()

    #经验本
    m_touch(Template(r"tpl1724041440458.png", record_pos=(-0.327, -0.082), resolution=(1214, 900))) 
    def repeat_battle(battle_times, multi_factor = 1):
        if multi_factor < 1:
            return
        for i in range(battle_times):
            m_touch(Template(r"tpl1724040793103.png", record_pos=(0.261, 0.239), resolution=(1600, 900)))
            #检查体力
            if has_ap_alert():
                backarrow_common()
                break
            elif w_exists('自律准备'):
                if multi_factor > 1:
                    btn_plus = m_exists(Template(r"tpl1749024786440.png", record_pos=(0.139, 0.019), resolution=(1610, 932)))
                    for j in range(multi_factor - 1):
                        m_touch(btn_plus)
                m_touch(Template(r"tpl1724040944534.png", record_pos=(0.107, 0.12), resolution=(1600, 900)))
                if has_ap_alert():
                    backarrow_common()
                    break
                sleep(3)
                collect_reward()
            else:
                raise
    cur_stamia = get_stamia()
    multi_ten, remainder = divmod(cur_stamia, 100)
    multi_single, remainder = divmod(remainder, 10)
    repeat_battle(multi_ten, 10)
    repeat_battle(1, multi_single)
    #返回主页
    return_home()

"""
---
每日任务
---
"""
def daily_task():
    w_touch('委托')
    if w_exists('已全部领取'):
        pass
    else:
        try:
            m_touch(Template(r"tpl1724041727519.png", record_pos=(0.367, 0.232), resolution=(1600, 900)))
        except:
            pass
        finally:
            try:
                m_touch(Template(r"tpl1724041750798.png", record_pos=(-0.346, 0.152), resolution=(1219, 900)))
                collect_reward()
            except:
                pass
    return_home()
    
    if w_exists('巡录'):
        w_touch('巡录')
        #TODO: 添加通行证未开放或第一次打开时的情况
        w_touch('沿途行动')
        try:
            m_touch(Template(r"tpl1724042132942.png", record_pos=(0.367, 0.249), resolution=(1600, 900)))
        except:
            pass
        #等升级动画结束
        sleep(5)
        w_touch('远航巡录')
        if m_exists(Template(r"tpl1724228593870.png", record_pos=(0.411, 0.065), resolution=(1600, 900))):
            m_touch(Template(r"tpl1724228593870.png", record_pos=(0.411, 0.065), resolution=(1600, 900)))
            m_touch(Template(r"tpl1724228701339.png", record_pos=(0.107, 0.134), resolution=(1600, 900)))
            while select_bp_reward():
                pass
            collect_reward()
        return_home()

#如果没有找到需要选择的通行证奖励 返回False
def select_bp_reward():
    if not m_exists(Template(r"tpl1724555019676.png", rgb=True, record_pos=(-0.071, 0.133), resolution=(1600, 900))):
        return False
    if w_exists('拂晓之光补给包'):
#         w_touch('坍塌晶条')
        touch(Template(r"tpl1742921042606.png", threshold=0.8, rgb=True, record_pos=(-0.237, -0.072), resolution=(1610, 932)))
        touch(Template(r"tpl1724237055401.png", record_pos=(0.107, 0.133), resolution=(1600, 900)))
        return True
    elif w_exists('标准武器自选礼箱'):
        w_touch('复仇女神')
        touch(Template(r"tpl1724237055401.png", record_pos=(0.107, 0.133), resolution=(1600, 900)))
        return True
    else:
        return False

"""
---
每周任务
---
"""
def weekly_task():
    w_touch('战役推进')
    #切回初始页
#     if not m_exists(Template(r"tpl1724237282638.png", threshold=0.6, rgb=True, record_pos=(0.072, -0.254), resolution=(1600, 900))):
#         m_touch(Template(r"tpl1724236408766.png", record_pos=(0.069, -0.256), resolution=(1600, 900)))
    w_touch('模拟作战')
    m_touch(Template(r"tpl1724648488359.png", rgb=True, record_pos=(0.103, -0.147), resolution=(1600, 900)))
    if not w_exists('一键领取'):
        w_touch('周期报酬')

    if not w_exists('已领取本周期内全部报酬') and w_exists('一键领取'):
        w_touch('一键领取')
        collect_reward()
    backarrow_common()
    backarrow_common()
    #首领
    swipe((300,450), (1300, 450))
    w_touch('首领挑战')
    _v_btn_zilv = m_exists(Template(r"tpl1724648945638.png", rgb=True, record_pos=(0.345, 0.283), resolution=(1350, 900)))
    if not _v_btn_zilv:
        return_home()
        return
    for i in range(3):
        m_touch(_v_btn_zilv)
        if w_exists('自律准备', is_isolating_word = True):
            m_touch(Template(r"tpl1724649003384.png", rgb=True, record_pos=(0.219, 0.141), resolution=(1350, 900)))
            collect_reward()
        else:
            break
    return_home()

"""
---
边界推进
---
"""
def frontline_activity():
    w_touch('限时开启')
    w_touch('边界推进')
    w_touch('晶源采集')
    if w_exists('前往探索'):
        return_home()
        return
    try:
        touch(Template(r"tpl1742834854161.png", rgb=True, record_pos=(0.193, 0.256), resolution=(1620, 964)))
    except:
        pass
    try:
        w_touch('领取')
        w_touch('获得道具')
        sleep(2)
    except:
        pass
    return_home()

"""
---
重复活动
---
"""
def reusable_activity():
    w_touch('活动')
    btn_zhanqianbuji = w_exists('战前补给')
    if btn_zhanqianbuji:
        w_click(btn_zhanqianbuji)
        btn_lingqu = w_exists('领取', is_isolating_word = True)
        if btn_lingqu:
            w_click(btn_lingqu)
            collect_reward()
    btn_qingbaobuji = w_exists('情报补给')
    if btn_qingbaobuji:
        w_click(btn_qingbaobuji)
        try:
            w_touch('领取', is_isolating_word = True)
            collect_reward()
        except:
            pass
        try:
            w_touch('领取', is_isolating_word = True)
            collect_reward()
        except:
            pass
    return_home()
        


"""
---
限时活动
---
"""
def temporary_activity():
    w_touch('限时开启')
    click((150, 750))
    w_touch('物资模式')
    w_touch('1-5')
    m_touch(Template(r"tpl1732055215502.png", record_pos=(0.291, 0.253), resolution=(1610, 932)))
    m_touch(Template(r"tpl1732055226926.png", record_pos=(0.138, 0.02), resolution=(1610, 932)))
    m_touch(Template(r"tpl1732055226926.png", record_pos=(0.138, 0.02), resolution=(1610, 932)))
    m_touch(Template(r"tpl1732055268161.png", record_pos=(0.106, 0.12), resolution=(1610, 932)))
    if m_exists(Template(r"tpl1732055268161.png", record_pos=(0.106, 0.12), resolution=(1610, 932))):
        sleep(2)
        keyevent("{ESC}")
    else:
        collect_reward()
    backarrow_common()
    return_home()
    
"""
---
商店
---
"""
def shopping():
    w_touch('商城')
    w_touch('品质甄选')
    w_touch('限时礼包')
    try:
        w_touch('周周乐补给箱')
        w_touch('购买', is_isolating_word = True)
        collect_reward()
    except:
        pass
    w_touch('周期礼包')
    w_touch('每日补给箱')
    if w_exists('购买', is_isolating_word = True):
        w_touch('购买', is_isolating_word = True)
        collect_reward()
    else:
        backarrow_common()
    w_touch('易物所')
    w_touch('冬日礼品铺')
    buy_item(True, 22)
    backarrow_common()
    w_touch('调度商店')
    buy_item(item_list = ['访问许可', '紫色心意礼盒·一', '紫色心意礼盒·二', '紫色心意礼盒·三', '紫色心意礼盒·四', '紫色心意礼盒·五'])
    backarrow_common()
    w_touch('班组商店')
    buy_item(item_list = ['波波沙心智存档', '火控校准芯片'])
    backarrow_common()
    if w_exists('讯段交易'):
        w_touch('讯段交易')
        buy_item(item_list = ['塞布丽娜心智存档', '访问许可', '基原信息核', '萨狄斯金', '次世代内存条'])
        backarrow_common()
    w_touch('人形堆栈')
    buy_item(item_list = ['火控校准芯片', '访问许可', '专访许可', '大容量内存条'])
    backarrow_common()

def ocr_test():
    img_dir = ST.LOG_DIR + '\\' + snapshot()['screen']
    result = ocr.ocr(img_dir)[0]
    print(result)

#开始

# ocr_test()
reusable_activity()
mailbox()
ally_area()
public_area()
daily_battle()
daily_task()
weekly_task()
frontline_activity()
temporary_activity()
shopping()

#TODO: 2. 实现后台截图、点击功能，并替换原生的截图、点击方法（或重写m_x和w_x方法）
#TODO: 3. 读取配置功能，可视化配置UI


 
