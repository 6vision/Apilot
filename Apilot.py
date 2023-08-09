
import plugins
import requests
import re
import json
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel import channel
from common.log import logger
from plugins import *
from PIL import Image

ZODIAC_MAPPING = {
        '白羊座': 'aries',
        '金牛座': 'taurus',
        '双子座': 'gemini',
        '巨蟹座': 'cancer',
        '狮子座': 'leo',
        '处女座': 'virgo',
        '天秤座': 'libra',
        '天蝎座': 'scorpio',
        '射手座': 'sagittarius',
        '摩羯座': 'capricorn',
        '水瓶座': 'aquarius',
        '双鱼座': 'pisces'
    }

@plugins.register(
    name="Apilot",
    desire_priority=-1,
    hidden=True,
    desc="A plugin to handle specific keywords",
    version="0.1",
    author="vision",
)
class Apilot(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Hello] inited")

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type not in [
            ContextType.TEXT
        ]:
            return
        content = e_context["context"].content
        logger.debug("[Hello] on_handle_context. content: %s" % content)

        if content == "早报":
            reply = Reply()
            reply.type = ReplyType.IMAGE_URL
            reply.content = self.get_morning_news()
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

        if content == "摸鱼":
            reply = Reply()
            reply.type = ReplyType.IMAGE_URL
            reply.content = self.get_moyu_calendar()
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

        match = re.match(r'^([\u4e00-\u9fa5]{2}座)$', content)
        if match:
            reply = Reply()
            reply.type = ReplyType.TEXT
            if content in ZODIAC_MAPPING:
                zodiac_english = ZODIAC_MAPPING[content]
                reply.content = self.get_horoscope(zodiac_english)
            else: reply.content = "请重新输入星座名称"
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑
    def get_help_text(self, **kwargs):
        help_text = "发送早报、摸鱼、星座名称，会有惊喜！"
        return help_text

    def get_morning_news(self):
        url = "https://api.vvhan.com/api/60s?type=json"
        payload = "format=json"
        headers = {'Content-Type': "application/x-www-form-urlencoded"}

        try:
            response = requests.request("POST", url, data=payload, headers=headers)
            morning_news_info = response.json()
            if morning_news_info.get('success') and morning_news_info['success'] == True:
                return morning_news_info['imgUrl']
            else:
                logger.error(f"get_morning_news失败，错误信息：{morning_news_info}")
                return None
        except Exception as e:
            logger.error(f"get_morning_news失败，错误信息：{e}")
            return None

    def get_moyu_calendar(self):
        url = "https://api.vvhan.com/api/moyu?type=json"
        payload = "format=json"
        headers = {'Content-Type': "application/x-www-form-urlencoded"}

        try:
            response = requests.request("POST", url, data=payload, headers=headers)
            moyu_calendar_info = response.json()

            # 验证请求是否成功
            if moyu_calendar_info.get('success') and moyu_calendar_info['success'] == True:
                return moyu_calendar_info['url']
            else:
                logger.error(f"moyu_calendar请求失败，错误信息：{moyu_calendar_info}")
                return None
        except Exception as e:
            logger.error(f"获取moyu_calendar信息失败，错误信息：{e}")
            return None






    def get_horoscope(self, astro_sign: str, time_period: str = "today"):
        base_url = "https://api.vvhan.com/api/horoscope"
        params = {
            'type': astro_sign,
            'time': time_period
        }
        try:
            response = requests.get(base_url, params=params)
            horoscope_data = response.json()
            if horoscope_data.get('success'):
                data = horoscope_data['data']

                # 基本信息
                title = data['title']
                time_period = data['time']

                # 每日建议
                todo_yi = data['todo']['yi']
                todo_ji = data['todo']['ji']

                # 运势百分比
                index_all = data['index']['all']
                index_love = data['index']['love']
                index_work = data['index']['work']
                index_money = data['index']['money']
                index_health = data['index']['health']

                # 幸运数字、颜色和星座
                luckynumber = data['luckynumber']
                luckycolor = data['luckycolor']
                luckyconstellation = data['luckyconstellation']

                # 运势简评和详细评论
                short_comment = data['shortcomment']
                fortune_all = data['fortunetext']['all']
                fortune_love = data['fortunetext']['love']
                fortune_work = data['fortunetext']['work']
                fortune_money = data['fortunetext']['money']
                fortune_health = data['fortunetext']['health']

                result = (
                    f"{title} ({time_period}):\n\n"
                    f"💡【每日建议】\n宜：{todo_yi}\n忌：{todo_ji}\n\n"
                    f"📊【运势指数】\n"
                    f"总运势：{index_all}\n"
                    f"爱情：{index_love}\n"
                    f"工作：{index_work}\n"
                    f"财运：{index_money}\n"
                    f"健康：{index_health}\n\n"
                    f"🍀【幸运提示】\n数字：{luckynumber}\n"
                    f"颜色：{luckycolor}\n"
                    f"星座：{luckyconstellation}\n\n"
                    f"✍【简评】\n{short_comment}\n\n"
                    f"📜【详细运势】\n"
                    f"总运：{fortune_all}\n\n"
                    f"爱情：{fortune_love}\n\n"
                    f"工作：{fortune_work}\n\n"
                    f"财运：{fortune_money}\n\n"
                    f"健康：{fortune_health}\n"
                )

                return result

            else:
                logger.error(f"Horoscope request failed: {horoscope_data}")
                return "Failed to fetch horoscope data."

        except Exception as e:
            logger.error(f"Error fetching horoscope: {e}")
            return "Error occurred while fetching horoscope."



