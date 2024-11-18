import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import asyncio
from typing import List, Set

class GuildCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'database/ryker.db'
        self.BATCH_SIZE = 1000
        self.DELAY = 1
        
    async def get_ryker_ids(self) -> Set[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT user_id FROM ryker_accounts') as cursor:
                rows = await cursor.fetchall()
                return {row[0] for row in rows}
                
    @app_commands.command(name="check_guild", description="檢查伺服器中的Ryker分身")
    @app_commands.describe(guild_id="要檢查的伺服器ID（可選，預設為當前伺服器）")
    async def check_guild(self, interaction: discord.Interaction, guild_id: str = None):
        await interaction.response.defer(thinking=True)
        
        try:
            # 如果沒有提供guild_id，使用當前伺服器
            if guild_id is None:
                guild = interaction.guild
                if guild is None:
                    await interaction.followup.send("此命令必須在伺服器中使用", ephemeral=True)
                    return
            else:
                # 嘗試獲取指定的伺服器
                try:
                    guild = await self.bot.fetch_guild(int(guild_id))
                except discord.Forbidden:
                    await interaction.followup.send("無法存取該伺服器，請確保機器人已加入該伺服器", ephemeral=True)
                    return
                except discord.NotFound:
                    await interaction.followup.send("找不到指定的伺服器", ephemeral=True)
                    return
                except ValueError:
                    await interaction.followup.send("無效的伺服器ID", ephemeral=True)
                    return
            
            # 獲取所有Ryker ID
            ryker_ids = await self.get_ryker_ids()
            
            # 獲取伺服器成員
            try:
                members = [member async for member in guild.fetch_members()]
                total_members = len(members)
            except discord.Forbidden:
                await interaction.followup.send("無法獲取伺服器成員列表，請確保機器人有正確的權限", ephemeral=True)
                return
                
            # 創建進度embed
            progress_embed = discord.Embed(
                title="正在檢查伺服器成員",
                description=f"正在檢查 {guild.name} 的成員...",
                color=discord.Color.blue()
            )
            progress_embed.add_field(
                name="總成員數", 
                value=str(total_members)
            )
            await interaction.followup.send(embed=progress_embed)
            
            # 分批處理成員
            found_rykers = []
            for i in range(0, total_members, self.BATCH_SIZE):
                batch = members[i:i + self.BATCH_SIZE]
                batch_rykers = [
                    member for member in batch 
                    if str(member.id) in ryker_ids
                ]
                found_rykers.extend(batch_rykers)
                
                # 更新進度
                if i % (self.BATCH_SIZE * 5) == 0:
                    progress_embed.description = f"已檢查 {i + len(batch)}/{total_members} 名成員..."
                    try:
                        await interaction.edit_original_response(embed=progress_embed)
                    except discord.NotFound:
                        pass
                    
                await asyncio.sleep(self.DELAY)
                
            # 發送結果
            if found_rykers:
                result_embed = discord.Embed(
                    title=f"在 {guild.name} 中發現Ryker分身",
                    description=f"發現 {len(found_rykers)} 個Ryker分身",
                    color=discord.Color.red()
                )
                
                # 分批添加欄位
                for i, member in enumerate(found_rykers, 1):
                    result_embed.add_field(
                        name=f"分身 #{i}",
                        value=f"用戶: {member.mention}\nID: {member.id}",
                        inline=False
                    )
                    
                    if i % 25 == 0 and i < len(found_rykers):
                        await interaction.followup.send(embed=result_embed)
                        result_embed = discord.Embed(
                            title=f"在 {guild.name} 中發現Ryker分身（續）",
                            color=discord.Color.red()
                        )
                
                await interaction.followup.send(embed=result_embed)
            else:
                result_embed = discord.Embed(
                    title="檢查完成",
                    description=f"在 {guild.name} 中未發現Ryker分身",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=result_embed)
                
        except Exception as e:
            error_embed = discord.Embed(
                title="檢查時發生錯誤",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(GuildCheck(bot))
