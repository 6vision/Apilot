import plugins
import requests
import re
import json
from urllib.parse import urlparse
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel import channel
from common.log import logger
from plugins import *
from PIL import Image
from datetime import datetime, timedelta
BASE_URL_VVHAN = "https://api.vvhan.com/api/"
BASE_URL_ALAPI = "https://v2.alapi.cn/api/"

@plugins.register(
    name="Apilot",
    desire_priority=-1,
    hidden=False,
    desc="A plugin to handle specific keywords",
    version="0.2",
    author="vision",
)
class Apilot(Plugin):
    def __init__(self):
        super().__init__()
        self.alapi_token = None  # Setting a default value for alapi_token
        self.load_config_optional()  # Try to load the config in an optional manner
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context

    def load_config_optional(self):
        try:
            conf = super().load_config()
            if conf and "alapi_token" in conf:
                self.alapi_token = conf["alapi_token"]
                logger.info("[Apilot] inited and alapi_token loaded successfully")
            else:
                logger.warn("[Apilot] inited but alapi_token not found in config")
        except Exception as e:
            logger.warn(f"[Apilot] Error loading config: {e}")

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type not in [
            ContextType.TEXT
        ]:
            return
        content = e_context["context"].content
        logger.debug("[Apilot] on_handle_context. content: %s" % content)

        if content == "早报":
            news = self.get_morning_news(self.alapi_token)
            reply_type = ReplyType.IMAGE_URL if self.is_valid_url(news) else ReplyType.TEXT
            reply = self.create_reply(reply_type, news or "早报服务异常，请检查配置或者查看服务器log")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑
        if content == "摸鱼":
            moyu = self.get_moyu_calendar()
            reply_type = ReplyType.IMAGE_URL if self.is_valid_url(moyu) else ReplyType.TEXT
            reply = self.create_reply(reply_type, moyu or "早报服务异常，请检查配置或者查看服务器log")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

        if content.startswith("快递"):
            # Extract the part after "快递"
            tracking_number = content[2:].strip()

            # Check if alapi_token is available before calling the function
            if not self.alapi_token:
                self.handle_error("alapi_token not configured", "快递请求失败")
                reply = self.create_reply(ReplyType.TEXT, "请先配置alapi的token")
            else:
                # Call query_express_info function with the extracted tracking_number and the alapi_token from config
                content = self.query_express_info(self.alapi_token, tracking_number)
                reply = self.create_reply(ReplyType.TEXT, content)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

        match = re.match(r'^([\u4e00-\u9fa5]{2}座)$', content)
        if match:
            if content in ZODIAC_MAPPING:
                zodiac_english = ZODIAC_MAPPING[content]
                content = self.get_horoscope(zodiac_english)
                reply = self.create_reply(ReplyType.TEXT, content)
            else:
                reply = self.create_reply(ReplyType.TEXT, "请重新输入星座名称")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

        if content == "微博热搜":
            content = self.get_weibo_hot_trends()
            reply = self.create_reply(ReplyType.TEXT, content)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

        # 天气查询
        weather_match = re.search(r'([\u4e00-\u9fa5]{1,6})的?天气$', content)
        if weather_match:
            # 如果匹配成功，提取第一个捕获组（可能包含“的”的城市名）
            city_with_optional_de = weather_match.group(1)
            # 移除可能存在的“的”
            city = city_with_optional_de.replace('的', '')
            if not self.alapi_token:
                self.handle_error("alapi_token not configured", "天气请求失败")
                reply = self.create_reply(ReplyType.TEXT, "请先配置alapi的token")
            else:
                content = self.get_weather(self.alapi_token, city)
                reply = self.create_reply(ReplyType.TEXT, content)
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS  # 事件结束，并跳过处理context的默认逻辑

    def get_help_text(self, **kwargs):
        help_text = "\n🐳发送“早报”、“摸鱼”、“微博热搜”、“星座名称”会有惊喜！\n📦快递查询：<快递+快递单号>\n🌦️天气查询：城市+天气"
        return help_text


    def get_morning_news(self, alapi_token):
        if not alapi_token:
            url = BASE_URL_VVHAN + "60s?type=json"
            payload = "format=json"
            headers = {'Content-Type': "application/x-www-form-urlencoded"}
            try:
                morning_news_info = self.make_request(url, method="POST", headers=headers, data=payload)
                if isinstance(morning_news_info, dict) and morning_news_info['success']:
                    return morning_news_info['imgUrl']
                else:
                    return self.handle_error(morning_news_info, "get_morning_news失败")
            except Exception as e:
                return self.handle_error(e, "早报获取失败")
        else:
            url = BASE_URL_ALAPI + "zaobao"
            payload = f"token={alapi_token}&format=json"
            headers = {'Content-Type': "application/x-www-form-urlencoded"}
            try:
                morning_news_info = self.make_request(url, method="POST", headers=headers, data=payload)
                if isinstance(morning_news_info, dict) and morning_news_info.get('code') == 200:
                    return morning_news_info['data']['image']
                else:
                    return self.handle_error(morning_news_info, "get_morning_news失败")
            except Exception as e:
                return self.handle_error(e, "早报获取失败")

    def get_moyu_calendar(self):
        url = BASE_URL_VVHAN + "moyu?type=json"
        payload = "format=json"
        headers = {'Content-Type': "application/x-www-form-urlencoded"}

        try:
            moyu_calendar_info = self.make_request(url, method="POST", headers=headers, data=payload)
            # 验证请求是否成功
            if isinstance(moyu_calendar_info, dict) and moyu_calendar_info['success']:
                return moyu_calendar_info['url']
            else:
                return self.handle_error(moyu_calendar_info,"moyu_calendar请求失败")
        except Exception as e:
            return self.handle_error(e, "获取摸鱼日历信息失败")


    def get_horoscope(self, astro_sign: str, time_period: str = "today"):
        url = BASE_URL_VVHAN + "horoscope"
        params = {
            'type': astro_sign,
            'time': time_period
        }
        try:
            horoscope_data = self.make_request(url, "GET", params=params)
            if isinstance(horoscope_data, dict) and horoscope_data['success']:
                data = horoscope_data['data']

                result = (
                    f"{data['title']} ({data['time']}):\n\n"
                    f"💡【每日建议】\n宜：{data['todo']['yi']}\n忌：{data['todo']['ji']}\n\n"
                    f"📊【运势指数】\n"
                    f"总运势：{data['index']['all']}\n"
                    f"爱情：{data['index']['love']}\n"
                    f"工作：{data['index']['work']}\n"
                    f"财运：{data['index']['money']}\n"
                    f"健康：{data['index']['health']}\n\n"
                    f"🍀【幸运提示】\n数字：{data['luckynumber']}\n"
                    f"颜色：{data['luckycolor']}\n"
                    f"星座：{data['luckyconstellation']}\n\n"
                    f"✍【简评】\n{data['shortcomment']}\n\n"
                    f"📜【详细运势】\n"
                    f"总运：{data['fortunetext']['all']}\n"
                    f"爱情：{data['fortunetext']['love']}\n"
                    f"工作：{data['fortunetext']['work']}\n"
                    f"财运：{data['fortunetext']['money']}\n"
                    f"健康：{data['fortunetext']['health']}\n"
                )

                return result

            else:
                return self.handle_error("horoscope_data", "Failed to fetch horoscope data.")

        except Exception as e:
            return self.handle_error(e, "获取星座信息失败")


    def get_weibo_hot_trends(self):
        url = BASE_URL_VVHAN + "wbhot"
        try:
            data = self.make_request(url, "GET")
            if isinstance(data, dict) and data['success'] == True:
                output = []
                topics = data['data']
                output.append(f'更新时间：{data["time"]}\n')
                for i, topic in enumerate(topics[:15], 1):
                    formatted_str = f"{i}. {topic['title']} ({topic['hot']} 浏览)\nURL: {topic['url']}\n"
                    output.append(formatted_str)
                return "\n".join(output)
            else:
                return self.handle_error(data, "热榜获取失败")
        except Exception as e:
            return self.handle_error(e, "获取热搜失败")


    def query_express_info(self, alapi_token, tracking_number, com="", order="asc"):
        url = BASE_URL_ALAPI + "kd"
        payload = f"token={alapi_token}&number={tracking_number}&com={com}&order={order}"
        headers = {'Content-Type': "application/x-www-form-urlencoded"}

        try:
            response_json = self.make_request(url, method="POST", headers=headers, data=payload)

            if not isinstance(response_json, dict) and response_json.get("code") != 200:
                return f"查询失败：{response_json.get('msg')}"
            data = response_json.get("data")
            if not data.get("info"):
                return "抱歉：没有查询到快递信息。"
            formatted_result = [
                f"快递编号：{data.get('nu')}",
                f"快递公司：{data.get('com')}",
                f"状态：{data.get('status_desc')}",
                "状态信息："
            ]
            for info in data.get("info"):
                time_str = info.get('time')[5:-3]
                formatted_result.append(f"{time_str} - {info.get('status_desc')}\n    {info.get('content')}")

            return "\n".join(formatted_result)

        except Exception as e:
            return self.handle_error(e, "快递查询失败")

    def get_weather(self, alapi_token, city: str):
        url = BASE_URL_ALAPI + 'tianqi'
        params = {
            'city': city,
            'token': f'{alapi_token}'  # 请将你的token填在这里
        }
        try:
            weather_data = self.make_request(url, "GET", params=params)
            print(weather_data)
            if isinstance(weather_data, dict) and weather_data.get('code') == 200:
                data = weather_data['data']
                update_time = data['update_time']
                dt_object = datetime.strptime(update_time, "%Y-%m-%d %H:%M:%S")
                formatted_update_time = dt_object.strftime("%m-%d %H:%M")
                # Basic Info
                formatted_output = []
                basic_info = (
                    f"🏙️ 城市: {data['city']} ({data['province']})\n"
                    f"🕒 更新: {formatted_update_time}\n"
                    f"🌦️ 天气: {data['weather']}\n"
                    f"🌡️ 温度: ↓{data['min_temp']}℃| 现{data['temp']}℃| ↑{data['max_temp']}℃\n"
                    f"🌬️ 风向: {data['wind']}\n"
                    f"💦 湿度: {data['humidity']}\n"
                    f"🌅 日出/日落: {data['sunrise']} / {data['sunset']}\n"
                )
                formatted_output.append(basic_info)


                # Clothing Index,处理部分县区穿衣指数返回null
                chuangyi_data = data.get('index', {}).get('chuangyi', {})
                if chuangyi_data:
                    chuangyi_level = chuangyi_data.get('level', '未知')
                    chuangyi_content = chuangyi_data.get('content', '未知')
                else:
                    chuangyi_level = '未知'
                    chuangyi_content = '未知'

                chuangyi_info = f"👚 穿衣指数: {chuangyi_level} - {chuangyi_content}\n"
                formatted_output.append(chuangyi_info)
                # Next 7 hours weather
                ten_hours_later = dt_object + timedelta(hours=10)

                future_weather = []
                for hour_data in data['hour']:
                    forecast_time_str = hour_data['time']
                    forecast_time = datetime.strptime(forecast_time_str, "%Y-%m-%d %H:%M:%S")

                    if dt_object < forecast_time <= ten_hours_later:
                        future_weather.append(f"     {forecast_time.hour:02d}:00 - {hour_data['wea']} - {hour_data['temp']}°C")

                future_weather_info = "⏳ 未来10小时的天气预报:\n" + "\n".join(future_weather)
                formatted_output.append(future_weather_info)

                # Alarm Info
                if data.get('alarm'):
                    alarm_info = "⚠️ 预警信息:\n"
                    for alarm in data['alarm']:
                        alarm_info += (
                            f"🔴 标题: {alarm['title']}\n"
                            f"🟠 等级: {alarm['level']}\n"
                            f"🟡 类型: {alarm['type']}\n"
                            f"🟢 提示: \n{alarm['tips']}\n"
                            f"🔵 内容: \n{alarm['content']}\n\n"
                        )
                    formatted_output.append(alarm_info)

                return "\n".join(formatted_output)
            else:
                return self.handle_error("weather_data", "获取失败，请查看服务器log")

        except Exception as e:
            return self.handle_error(e, "获取天气信息失败")

    def make_request(self, url, method="GET", headers=None, params=None, data=None, json_data=None):
        try:
            if method.upper() == "GET":
                response = requests.request(method, url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.request(method, url, headers=headers, data=data, json=json_data)
            else:
                return {"success": False, "message": "Unsupported HTTP method"}

            return response.json()
        except Exception as e:
            return self.handle_error(e, "请求失败")


    def create_reply(self, reply_type, content):
        reply = Reply()
        reply.type = reply_type
        reply.content = content
        return reply


    def handle_error(self, error, message):
        logger.error(f"{message}，错误信息：{error}")
        return message

    def is_valid_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False
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
