import os
import random
import asyncio
import aiofiles
import aiofiles.os

from astrbot.api import AstrBotConfig, logger
from astrbot.api.star import Context, Star, register
from astrbot.api.event import AstrMessageEvent, filter

from .resources import ResourceManager
from .painter import FortunePainter


@register(
    "astrbot_plugin_dailycheck",
    "MoonCC",
    "每日抽签：合并今日人品(jrrp)与今日运势(jrys)",
    "1.0.0",
)
class DailyCheckPlugin(Star):
    """每日抽签插件：整合今日人品(jrrp)与今日运势(jrys)"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.resources = ResourceManager(self.config)
        self.painter = FortunePainter(self.config)

    async def initialize(self):
        """插件加载后初始化资源（如启用背景图预缓存）。"""
        await self.resources.initialize()

    # ---------------- 今日人品 (jrrp) ----------------
    @filter.command("jrrp")
    async def jrrp(self, event: AstrMessageEvent):
        """获取今日人品值。用法：/jrrp"""
        user_id = event.get_sender_id()
        seed = user_id + str(__import__("datetime").date.today())
        random.seed(seed)
        jrrp_value = random.randint(0, 100)
        random.seed()
        yield event.plain_result(f"你今天的人品值为：{jrrp_value}")

    # ---------------- 今日运势 (jrys) ----------------
    @filter.command("jrys", alias=["今日运势", "运势"])
    async def jrys_command_handler(self, event: AstrMessageEvent):
        """处理 /jrys, /今日运势, /运势 等指令"""
        setattr(event, "_jrys_processed", True)
        async for result in self.jrys(event):
            yield result

    @filter.command("jrys_last")
    async def jrys_last_command_handler(self, event: AstrMessageEvent):
        """处理 /jrys_last 指令，发送上一次生成的原图"""
        user_id = event.get_sender_id()
        self.jrys_data = await self.resources._load_jrys_data()
        user_last_images = self.jrys_data.get("_user_last_images", {})
        if user_id not in user_last_images:
            yield event.plain_result("你还没有生成过今日运势哦，先发送 jrys 生成一张吧！")
            return

        last_info = user_last_images[user_id]
        path = last_info.get("path")

        if not path or not os.path.exists(path):
            yield event.plain_result("找不到上一次生成的原图了，可能已被清理，请重新生成～")
            return

        yield event.image_result(path)

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def jrys_keyword_handler(self, event: AstrMessageEvent, *args, **kwargs):
        """私聊关键词触发今日运势（受 auto_trigger 控制）"""
        if getattr(event, "_jrys_processed", False):
            return

        if not self.config.get("auto_trigger", False):
            return
        if event.get_type() != filter.EventMessageType.PRIVATE_MESSAGE:
            return

        message_str = event.message_str.strip()
        keywords = {"jrys", "今日运势", "运势"}
        if message_str in keywords:
            async for result in self.jrys(event):
                yield result

    async def jrys(self, event: AstrMessageEvent):
        """核心运势生成逻辑（整合自 jrys）"""
        user_id = event.get_sender_id()
        user_name = event.get_sender_name()
        use_avatar = self.config.get("use_avatar", False)

        self.jrys_data = await self.resources._load_jrys_data()

        background_path = None
        background_should_cleanup = False

        try:
            tasks = [self.resources.get_background_image()]
            if use_avatar:
                tasks.insert(0, self.resources.get_avatar_img(user_id))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            if use_avatar:
                avatar_path, background_result = results
            else:
                background_result = results[0]
                avatar_path = None

            if isinstance(background_result, Exception):
                logger.error(f"获取背景图片时出错: {background_result}")
                yield event.plain_result("获取背景图片失败，请稍后再试～")
                return
            if background_result is None:
                yield event.plain_result("获取背景图片失败，请稍后再试～")
                return

            background_path, background_should_cleanup = background_result

            if isinstance(avatar_path, Exception):
                logger.error(f"获取头像时出错: {avatar_path}")
                avatar_path = None

        except Exception as e:
            logger.error(f"获取头像或背景图片时出错: {e}")
            yield event.plain_result("获取头像或背景图片失败，请稍后再试～")
            return

        temp_file_path = None

        try:
            temp_file_path = await asyncio.to_thread(
                self.painter.generate_image_sync,
                user_id,
                avatar_path,
                background_path,
                self.jrys_data,
            )

            if temp_file_path is None:
                yield event.plain_result("生成图片失败，请稍后再试～")
                return

            yield event.image_result(temp_file_path)

            # 保存上一次使用的背景图信息（供 /jrys_last 使用）
            if "_user_last_images" not in self.jrys_data:
                self.jrys_data["_user_last_images"] = {}

            user_last_images = self.jrys_data["_user_last_images"]
            if user_id in user_last_images:
                old_info = user_last_images[user_id]
                old_path = old_info.get("path")
                if (
                    old_info.get("should_cleanup")
                    and old_path
                    and old_path != background_path
                    and os.path.exists(old_path)
                ):
                    try:
                        await aiofiles.os.remove(old_path)
                    except Exception:
                        pass

            user_last_images[user_id] = {
                "path": background_path,
                "should_cleanup": background_should_cleanup,
            }
            await self.resources._save_jrys_data()
            background_should_cleanup = False

        except Exception as e:
            logger.error(f"生成运势图片过程中出错: {e}")
            yield event.plain_result("生成图片失败，请稍后再试～")

        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass

            if (
                background_should_cleanup
                and background_path
                and os.path.exists(background_path)
            ):
                try:
                    os.remove(background_path)
                except Exception:
                    pass

    async def terminate(self):
        """插件终止时的清理工作"""
        if self.resources._precache_task and not self.resources._precache_task.done():
            self.resources._precache_task.cancel()
            try:
                await self.resources._precache_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"预缓存任务清理失败: {e}")

        if self.resources._session:
            await self.resources._session.close()
            logger.info("HTTP会话已关闭")
