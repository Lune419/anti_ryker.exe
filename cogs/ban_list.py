import discord
from discord.ext import commands
from discord import app_commands
import re
import aiosqlite
import os
from typing import List, Tuple

class BanList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 定義所有關鍵字的正規表達式
        self.patterns = [
            re.compile(r'ryker', re.IGNORECASE),
            re.compile(r'ry\b', re.IGNORECASE),
            re.compile(r'藍恐龍'),
            re.compile(r'狗叫'),
            re.compile(r'球歷史'),
            re.compile(r'可悲'),
            re.compile(r'審查'),
            re.compile(r'傻逼'),
            re.compile(r'ban', re.IGNORECASE)
        ]

    def contains_keywords(self, reason: str) -> bool:
        """檢查原因是否包含任何關鍵字"""
        if not reason:
            return False
        
        # 加入除錯輸出
        print(f"檢查原因: {reason}")
        for pattern in self.patterns:
            if pattern.search(reason):
                print(f"找到匹配: {pattern.pattern}")
                return True
        return False

    @app_commands.command(
        name="ban_keyword",
        description="列出包含特定關鍵字的停權名單"
    )
    async def list_keyword_bans(self, interaction: discord.Interaction):
        await interaction.response.defer()  # 延遲回應，因為可能需要一些時間

        try:
            # 獲取伺服器的所有停權資料
            bans = [ban_entry async for ban_entry in interaction.guild.bans()]
            
            # 過濾出包含關鍵字的停權
            keyword_bans: List[Tuple[discord.User, str]] = [
                (ban_entry.user, ban_entry.reason) 
                for ban_entry in bans 
                if self.contains_keywords(ban_entry.reason)
            ]

            if not keyword_bans:
                await interaction.followup.send("沒有找到包含指定關鍵字的停權記錄。")
                return

            # 創建嵌入訊息
            embeds = []
            current_embed = discord.Embed(
                title="關鍵字停權名單",
                description="以下是包含特定關鍵字的停權用戶",
                color=discord.Color.blue()
            )
            
            field_count = 0
            for user, reason in keyword_bans:
                # Discord 限制每個 embed 最多 25 個欄位
                if field_count >= 25:
                    embeds.append(current_embed)
                    current_embed = discord.Embed(
                        title="關鍵字停權名單（續）",
                        color=discord.Color.blue()
                    )
                    field_count = 0

                current_embed.add_field(
                    name=f"{user.name} ({user.id})",
                    value=f"原因: {reason or '未提供原因'}",
                    inline=False
                )
                field_count += 1

            embeds.append(current_embed)

            # 發送所有 embed
            for embed in embeds:
                await interaction.followup.send(embed=embed)

        except discord.Forbidden:
            await interaction.followup.send("我沒有權限查看停權名單！", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"發生錯誤: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BanList(bot)) 