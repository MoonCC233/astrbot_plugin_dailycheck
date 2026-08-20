import os
import random

from astrbot.api import AstrBotConfig
from astrbot.api.star import Context, Star, register
from astrbot.api.event import AstrMessageEvent, filter

from .painter import combine, download_image

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
JRYSCACHE = os.path.join(PLUGIN_DIR, "jrys_cache.png")
JRYSDATA = os.path.join(PLUGIN_DIR, "jrys.json")
FONT_PATH = os.path.join(PLUGIN_DIR, "font", "MiSans-Medium.ttf")
BG_FOLDER = os.path.join(PLUGIN_DIR, "backgroundFolder")


@register(
    "astrbot_plugin_dailycheck",
    "MoonCC",
    "每日抽签：合并今日人品(jrrp)与今日运势(jrys)",
    "1.0.0",
)
class DailyCheckPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    @filter.command("jrrp")
    async def jrrp(self, event: AstrMessageEvent):
        '''获取今日人品值。用法：/jrrp'''
        user_id = event.get_sender_id()
        seed = user_id + str(__import__("datetime").date.today())
        random.seed(seed)
        jrrp_value = random.randint(0, 100)
        random.seed()
        yield event.plain_result(f"你今天的人品值为：{jrrp_value}")

    @filter.command("jrys", alias=["今日运势", "运势"])
    async def jrys(self, event: AstrMessageEvent):
        '''获取今日运势。用法：/jrys'''
        user_id = event.get_sender_id()

        # 读取运势数据
        if not os.path.exists(JRYSDATA):
            yield event.plain_result("运势数据文件缺失，请联系管理员。")
            return
        with open(JRYSDATA, "r", encoding="utf-8") as f:
            data = __import__("json").load(f)

        seed = user_id + str(__import__("datetime").date.today())
        random.seed(seed)
        fl = random.randint(0, 100)
        choice = random.choice(data)
        random.seed()

        # 配置项
        use_avatar = self.config.get("use_avatar", False)
        send_image = self.config.get("send_image", True)

        avatar_path = None
        if use_avatar:
            sender = event.get_sender()
            avatar_url = getattr(sender, "user_displayname", None)
            # 头像 URL 由平台事件提供，尝试获取
            try:
                avatar_url = event.get_avatars()[0] if event.get_avatars() else None
            except Exception:  # noqa: BLE001
                avatar_url = None
            if avatar_url:
                avatar_path = os.path.join(PLUGIN_DIR, f"avatar_{user_id}.png")
                download_image(avatar_url, avatar_path)

        img_path = combine(
            jrys_data=choice,
            user_id=user_id,
            fl=fl,
            avatar_path=avatar_path,
            bg_folder=BG_FOLDER,
            font_path=FONT_PATH,
        )

        if send_image:
            yield event.image_result(img_path)
        else:
            msg = (
                f"用户 {user_id} 今日运气: {fl}\n"
                f"{'★' * int(choice.get('star', 3))}{'☆' * (5 - int(choice.get('star', 3)))}\n"
                f"{choice.get('title', '')}\n"
                f"{choice.get('text', '')}\n"
                f"幸运方位: {choice.get('lucky', '')}\n"
                f"幸运颜色: {choice.get('lucky_color', '')}\n"
                f"幸运数字: {choice.get('lucky_num', '')}\n"
                f"幸运禁忌: {choice.get('avoid', '')}"
            )
            yield event.plain_result(msg)

        # 缓存图片路径，供 /jrys_last 使用
        self._last_img = img_path

    @filter.command("jrys_last")
    async def jrys_last(self, event: AstrMessageEvent):
        '''获取上次生成的今日运势卡片。用法：/jrys_last'''
        last = getattr(self, "_last_img", None)
        if last and os.path.exists(last):
            yield event.image_result(last)
        else:
            yield event.plain_result("暂无历史运势卡片，请先发送 /jrys 生成。")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        '''关键词触发今日运势（仅私聊）。'''
        if not self.config.get("auto_trigger", False):
            return
        if event.get_type() != filter.EventMessageType.PRIVATE_MESSAGE:
            return
        msg = event.message_str
        if msg and ("今日运势" in msg or "运势" in msg):
            async for r in self.jrys(event):
                yield r


def generate_card_image(user_id: str, jrys_data: dict, fl: int) -> str:
    """供外部直接调用的卡片生成入口。"""
    return combine(jrys_data, user_id, fl, bg_folder=BG_FOLDER, font_path=FONT_PATH)
