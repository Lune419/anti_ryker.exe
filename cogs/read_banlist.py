import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import asyncio

class ReadBanlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'database/ryker.db'
        self.DEVELOPER_ID = 726117345457864814
        self.BATCH_SIZE = 100  # 每批處理的封禁記錄數
        
    @app_commands.command(name="read_banlist", description="讀取伺服器封禁名單並加入Ryker資料庫")
    async def read_banlist(self, interaction: discord.Interaction):
        # 檢查是否為開發者
        if interaction.user.id != self.DEVELOPER_ID:
            await interaction.response.send_message("只有開發者可以使用此命令", ephemeral=True)
            return
            
        await interaction.response.defer(thinking=True)
        
        try:
            # 獲取伺服器的封禁名單
            bans = [entry async for entry in interaction.guild.bans()]
            total_bans = len(bans)
            
            if total_bans == 0:
                await interaction.followup.send("此伺服器沒有任何封禁記錄")
                return
                
            # 創建進度embed
            progress_embed = discord.Embed(
                title="正在處理封禁名單",
                description=f"共有 {total_bans} 個封禁記錄",
                color=discord.Color.blue()
            )
            progress_message = await interaction.followup.send(embed=progress_embed)
            
            # 將封禁用戶加入資料庫
            added_count = 0
            already_exists = 0
            
            async with aiosqlite.connect(self.db_path) as db:
                for i, ban_entry in enumerate(bans, 1):
                    try:
                        await db.execute(
                            'INSERT INTO ryker_accounts (user_id, reason, added_by, guild_id) VALUES (?, ?, ?, ?)',
                            (
                                str(ban_entry.user.id),
                                "Ryker",  # 統一設定原因為Ryker
                                str(interaction.user.id),
                                str(interaction.guild_id)
                            )
                        )
                        added_count += 1
                    except aiosqlite.IntegrityError:
                        already_exists += 1
                        
                    # 每處理BATCH_SIZE條記錄更新一次進度
                    if i % self.BATCH_SIZE == 0:
                        progress_embed.description = f"處理進度: {i}/{total_bans}"
                        await progress_message.edit(embed=progress_embed)
                        await asyncio.sleep(0.5)  # 避免速率限制
                        
                await db.commit()
            
            # 發送最終結果
            result_embed = discord.Embed(
                title="封禁名單處理完成",
                color=discord.Color.green()
            )
            result_embed.add_field(
                name="處理結果",
                value=f"✅ 成功加入: {added_count}\n"
                      f"⚠️ 已在資料庫中: {already_exists}\n"
                      f"📊 總封禁數: {total_bans}",
                inline=False
            )
            
            await interaction.followup.send(embed=result_embed)
            
        except discord.Forbidden:
            await interaction.followup.send(
                "我沒有足夠的權限來讀取封禁名單",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"處理時發生錯誤: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(ReadBanlist(bot))
