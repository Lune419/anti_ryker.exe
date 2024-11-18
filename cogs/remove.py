import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite

class Remove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'database/ryker.db'
        self.DEVELOPER_ID = 726117345457864814
        
    @app_commands.command(name="remove", description="將無辜的人從Ryker資料庫中移除")
    @app_commands.describe(user_id="要移除的用戶ID")
    async def remove(self, interaction: discord.Interaction, user_id: str):
        # 檢查是否為開發者
        if interaction.user.id != self.DEVELOPER_ID:
            await interaction.response.send_message("只有開發者可以使用此命令", ephemeral=True)
            return
            
        await interaction.response.defer(thinking=True)
        
        try:
            # 檢查ID格式是否正確
            try:
                user_id = str(int(user_id))  # 確保ID是數字
            except ValueError:
                await interaction.followup.send("無效的用戶ID格式", ephemeral=True)
                return
                
            # 檢查用戶是否在資料庫中
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    'SELECT * FROM ryker_accounts WHERE user_id = ?', 
                    (user_id,)
                ) as cursor:
                    if not await cursor.fetchone():
                        await interaction.followup.send(
                            f"用戶ID: {user_id} 不在Ryker資料庫中",
                            ephemeral=True
                        )
                        return
                        
                # 從資料庫中移除用戶
                await db.execute(
                    'DELETE FROM ryker_accounts WHERE user_id = ?',
                    (user_id,)
                )
                await db.commit()
                
            # 發送成功訊息
            embed = discord.Embed(
                title="✅ 移除成功",
                description=f"用戶ID: {user_id} 已從Ryker資料庫中移除",
                color=discord.Color.green()
            )
            embed.add_field(name="執行者", value=interaction.user.mention)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ 移除失敗",
                description=f"發生錯誤：{str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Remove(bot))