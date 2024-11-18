import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
import asyncio

class ResetDB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'database/ryker.db'
        self.DEVELOPER_ID = 726117345457864814
        
    @app_commands.command(name="reset_db", description="清空Ryker資料庫（僅開發者可用）")
    async def reset_db(self, interaction: discord.Interaction):
        # 檢查是否為開發者
        if interaction.user.id != self.DEVELOPER_ID:
            await interaction.response.send_message("只有開發者可以使用此命令", ephemeral=True)
            return
            
        # 創建確認按鈕
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.value = None
                
            @discord.ui.button(label="確認清空", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()
                
            @discord.ui.button(label="取消", style=discord.ButtonStyle.grey)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()
                
        # 發送確認訊息
        view = ConfirmView()
        embed = discord.Embed(
            title="⚠️ 危險操作",
            description="你確定要清空整個Ryker資料庫嗎？\n**此操作無法復原！**",
            color=discord.Color.red()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        # 等待用戶確認
        await view.wait()
        
        if view.value is None:
            await interaction.edit_original_response(
                content="操作已超時取消", 
                embed=None, 
                view=None
            )
            return
            
        if not view.value:
            await interaction.edit_original_response(
                content="操作已取消", 
                embed=None, 
                view=None
            )
            return
            
        # 開始清空資料庫
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM ryker_accounts')
                await db.commit()
                
            success_embed = discord.Embed(
                title="✅ 資料庫已清空",
                description="所有Ryker帳號記錄已被刪除",
                color=discord.Color.green()
            )
            await interaction.edit_original_response(
                embed=success_embed, 
                view=None
            )
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ 清空失敗",
                description=f"發生錯誤：{str(e)}",
                color=discord.Color.red()
            )
            await interaction.edit_original_response(
                embed=error_embed, 
                view=None
            )

async def setup(bot):
    await bot.add_cog(ResetDB(bot))
