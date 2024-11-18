import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from datetime import datetime
import sqlite3
import aiosqlite
import os

class RykerAccounts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.developer_id = 726117345457864814  # 新增開發者 ID
        # 取得目前檔案的目錄
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 設定資料庫路徑
        self.db_path = os.path.join(current_dir, "database", "ryker.db")
        print(f"資料庫路徑: {self.db_path}")  # 用於除錯

    @app_commands.command(
        name="add_ryker",
        description="新增 Ryker 小號到資料庫 (僅開發者可用)"
    )
    async def add_ryker(
        self, 
        interaction: discord.Interaction,
        user_id: str,
        reason: Optional[str] = "未提供原因"
    ):
        # 檢查是否為開發者
        if interaction.user.id != self.developer_id:
            await interaction.response.send_message(
                "❌ 此指令僅限開發者使用",
                ephemeral=True
            )
            return

        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 檢查是否已存在
                async with db.execute(
                    "SELECT * FROM ryker_accounts WHERE user_id = ?",
                    (user_id,)
                ) as cursor:
                    existing = await cursor.fetchone()
                
                if existing:
                    await interaction.response.send_message(
                        f"❌ 此 ID `{user_id}` 已存在於資料庫中",
                        ephemeral=True
                    )
                    return

                # 新增到資料庫
                await db.execute(
                    """
                    INSERT INTO ryker_accounts (user_id, reason, added_by, guild_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, reason, str(interaction.user.id), str(interaction.guild_id))
                )
                await db.commit()

                embed = discord.Embed(
                    title="✅ 成功新增 Ryker 小號",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="用戶 ID", value=f"`{user_id}`", inline=False)
                embed.add_field(name="原因", value=reason, inline=False)
                embed.add_field(name="新增者", value=f"<@{interaction.user.id}>", inline=False)
                embed.add_field(name="伺服器", value=f"{interaction.guild.name}", inline=False)
                
                await interaction.response.send_message(embed=embed)

        except discord.errors.NotFound:
            pass
        except Exception as e:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"❌ 發生錯誤: {str(e)}",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"❌ 發生錯誤: {str(e)}",
                        ephemeral=True
                    )
            except:
                pass

async def setup(bot):
    await bot.add_cog(RykerAccounts(bot)) 