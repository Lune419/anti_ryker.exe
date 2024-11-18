import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import asyncio
from typing import List, Tuple

class DBBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'database/ryker.db'
        self.DEVELOPER_ID = 726117345457864814
        
    async def process_ban(self, guild: discord.Guild, user_id: str) -> Tuple[int, int]:
        """處理單個用戶的封禁，返回 (already_banned, newly_banned)"""
        try:
            # 檢查用戶是否已被封禁
            try:
                await guild.fetch_ban(discord.Object(id=int(user_id)))
                return (1, 0)
            except discord.NotFound:
                pass
                
            # 嘗試封禁用戶
            await guild.ban(
                discord.Object(id=int(user_id)),
                reason="Ryker"
            )
            return (0, 1)
            
        except (discord.Forbidden, discord.HTTPException):
            return (0, 0)
        
    @app_commands.command(name="db_ban", description="一鍵封禁所有在資料庫中的Ryker")
    @app_commands.checks.has_permissions(ban_members=True)
    async def db_ban(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        
        try:
            # 獲取所有Ryker用戶
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('SELECT user_id FROM ryker_accounts') as cursor:
                    ryker_users = [row[0] for row in await cursor.fetchall()]
            
            if not ryker_users:
                await interaction.followup.send("資料庫中沒有Ryker用戶", ephemeral=True)
                return
                
            # 使用進度條顯示處理進度
            progress_embed = discord.Embed(
                title="🔄 正在批量封禁",
                description="處理中...\n進度: 0%",
                color=discord.Color.blue()
            )
            progress_msg = await interaction.followup.send(embed=progress_embed)
            
            # 並行處理封禁
            tasks = []
            chunk_size = 5  # 每次處理5個用戶
            already_banned = 0
            newly_banned = 0
            
            for i in range(0, len(ryker_users), chunk_size):
                chunk = ryker_users[i:i+chunk_size]
                chunk_tasks = [self.process_ban(interaction.guild, user_id) for user_id in chunk]
                results = await asyncio.gather(*chunk_tasks)
                
                # 更新計數
                for already, newly in results:
                    already_banned += already
                    newly_banned += newly
                    
                # 更新進度
                progress = (i + len(chunk)) / len(ryker_users) * 100
                progress_embed.description = f"處理中...\n進度: {progress:.1f}%"
                await progress_msg.edit(embed=progress_embed)
                
                # 短暫延遲以避免達到Discord的速率限制
                await asyncio.sleep(1)
            
            # 發送最終結果
            result_embed = discord.Embed(
                title="🔨 批量封禁完成",
                color=discord.Color.green()
            )
            result_embed.add_field(
                name="處理結果", 
                value=f"```已經封禁: {already_banned}\n新增封禁: {newly_banned}\n總計檢查: {len(ryker_users)}```",
                inline=False
            )
            result_embed.add_field(
                name="執行者", 
                value=interaction.user.mention,
                inline=False
            )
            
            await progress_msg.edit(embed=result_embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ 批量封禁失敗",
                description=f"發生錯誤：{str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(DBBan(bot)) 