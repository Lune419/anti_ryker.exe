import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import aiosqlite

class UnbanRyker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'database/ryker.db'
        self.developer_id = 726117345457864814
        
    @app_commands.command(
        name="unban_ryker", 
        description="解除Ryker的封禁（需要管理員權限）"
    )
    @app_commands.default_permissions(ban_members=True)
    async def unban_ryker(self, interaction: discord.Interaction, user_id: str):
        try:
            # 檢查是否在資料庫中
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    'SELECT * FROM ryker_accounts WHERE user_id = ?', 
                    (user_id,)
                ) as cursor:
                    if not await cursor.fetchone():
                        await interaction.response.send_message(
                            "❌ 此用戶不在資料庫中",
                            ephemeral=True
                        )
                        return

            # 執行解封
            user = discord.Object(id=int(user_id))
            await interaction.guild.unban(user, reason="管理員解除封禁")
            
            # 通知開發者確認
            developer = self.bot.get_user(self.developer_id)
            if developer:
                confirm_embed = discord.Embed(
                    title="解封確認請求",
                    description="請確認是否將此用戶從資料庫中移除",
                    color=discord.Color.yellow()
                )
                confirm_embed.add_field(
                    name="用戶 ID", 
                    value=f"`{user_id}`", 
                    inline=False
                )
                confirm_embed.add_field(
                    name="解封者",
                    value=f"{interaction.user} ({interaction.user.id})",
                    inline=False
                )
                confirm_embed.add_field(
                    name="伺服器",
                    value=f"{interaction.guild.name} ({interaction.guild.id})",
                    inline=False
                )
                
                # 建立確認按鈕
                view = UnbanConfirmView(self, user_id, interaction.guild.id)
                await developer.send(embed=confirm_embed, view=view)
            
            # 回應原始指令
            embed = discord.Embed(
                title="✅ 已解除封禁",
                description="用戶已被解除封禁，等待開發者確認後從資料庫移除",
                color=discord.Color.orange()
            )
            embed.add_field(name="用戶 ID", value=f"`{user_id}`")
            embed.add_field(name="執行者", value=interaction.user.mention)
            
            await interaction.response.send_message(embed=embed)
            
        except ValueError:
            await interaction.response.send_message(
                "❌ 無效的使用者ID格式",
                ephemeral=True
            )
        except discord.NotFound:
            await interaction.response.send_message(
                "❌ 找不到該用戶的封禁記錄",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ 我沒有足夠的權限來解除封禁",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ 執行時發生錯誤: {str(e)}",
                ephemeral=True
            )

class UnbanConfirmView(discord.ui.View):
    def __init__(self, cog, user_id: str, guild_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.user_id = user_id
        self.guild_id = guild_id

    @discord.ui.button(label="確認移除", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.cog.developer_id:
            await interaction.response.send_message("只有開發者可以確認", ephemeral=True)
            return
            
        try:
            async with aiosqlite.connect(self.cog.db_path) as db:
                await db.execute(
                    'DELETE FROM ryker_accounts WHERE user_id = ?',
                    (self.user_id,)
                )
                await db.commit()
            
            await interaction.response.send_message("✅ 已確認並從資料庫移除")
            self.disable_all_buttons()
            await interaction.message.edit(view=self)
        except Exception as e:
            await interaction.response.send_message(f"❌ 發生錯誤: {str(e)}")

    @discord.ui.button(label="拒絕移除", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.cog.developer_id:
            await interaction.response.send_message("只有開發者可以拒絕", ephemeral=True)
            return
            
        await interaction.response.send_message("❌ 已拒絕從資料庫移除")
        self.disable_all_buttons()
        await interaction.message.edit(view=self)

    def disable_all_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

async def setup(bot):
    await bot.add_cog(UnbanRyker(bot))
