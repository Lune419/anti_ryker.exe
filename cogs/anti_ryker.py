import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import aiosqlite

class AntiRyker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'database/ryker.db'
        self.developer_id = 726117345457864814
        self.pending_bans = {}  # 儲存待確認的封禁
        self.bot.loop.create_task(self.setup_database())
        
    async def setup_database(self):
        """建立資料庫表格"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS ryker_accounts (
                    user_id TEXT PRIMARY KEY,
                    reason TEXT,
                    added_by TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    guild_id TEXT
                )
            ''')
            await db.commit()

    async def add_to_database(self, user_id: str, reason: str, added_by: str, guild_id: str):
        """將使用者加入資料庫"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT INTO ryker_accounts (user_id, reason, added_by, guild_id) VALUES (?, ?, ?, ?)',
                (user_id, reason, added_by, guild_id)
            )
            await db.commit()
            
    @app_commands.command(name="ban_ryker", description="封禁Ryker分身並加入資料庫")
    @app_commands.default_permissions(ban_members=True)
    async def ban_ryker(self, interaction: discord.Interaction, user: discord.User):
        try:
            # 執行封禁
            await interaction.guild.ban(user, reason="Ryker分身")
            
            # 通知開發者確認
            developer = self.bot.get_user(self.developer_id)
            if developer:
                confirm_embed = discord.Embed(
                    title="新的Ryker分身回報",
                    description="請確認是否將此用戶加入資料庫",
                    color=discord.Color.yellow()
                )
                confirm_embed.add_field(name="用戶", value=f"{user} ({user.id})", inline=False)
                confirm_embed.add_field(name="回報者", value=f"{interaction.user} ({interaction.user.id})", inline=False)
                confirm_embed.add_field(name="伺服器", value=f"{interaction.guild.name} ({interaction.guild.id})", inline=False)
                
                # 建立確認按鈕
                view = ConfirmView(self, user.id, "Ryker分身", str(interaction.user.id), str(interaction.guild.id))
                await developer.send(embed=confirm_embed, view=view)
                
                # 回應原始指令
                embed = discord.Embed(
                    title="已封禁使用者",
                    description=f"使用者 {user.mention} 已被封禁，等待開發者確認後加入資料庫",
                    color=discord.Color.orange()
                )
                embed.add_field(name="原因", value="Ryker分身")
                embed.add_field(name="執行者", value=interaction.user.mention)
                
                await interaction.response.send_message(embed=embed)
                
        except discord.Forbidden:
            await interaction.response.send_message(
                "我沒有足夠的權限來封禁該使用者",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"執行時發生錯誤: {str(e)}",
                ephemeral=True
            )

class ConfirmView(discord.ui.View):
    def __init__(self, cog, user_id: str, reason: str, added_by: str, guild_id: str):
        super().__init__(timeout=None)
        self.cog = cog
        self.user_id = user_id
        self.reason = reason
        self.added_by = added_by
        self.guild_id = guild_id

    @discord.ui.button(label="確認加入", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.cog.developer_id:
            await interaction.response.send_message("只有開發者可以確認", ephemeral=True)
            return
            
        try:
            await self.cog.add_to_database(self.user_id, self.reason, self.added_by, self.guild_id)
            await interaction.response.send_message("✅ 已確認並加入資料庫")
            self.disable_all_buttons()
            await interaction.message.edit(view=self)
        except sqlite3.IntegrityError:
            await interaction.response.send_message("❌ 此用戶已在資料庫中")
        except Exception as e:
            await interaction.response.send_message(f"❌ 發生錯誤: {str(e)}")

    @discord.ui.button(label="拒絕加入", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.cog.developer_id:
            await interaction.response.send_message("只有開發者可以拒絕", ephemeral=True)
            return
            
        await interaction.response.send_message("❌ 已拒絕加入資料庫")
        self.disable_all_buttons()
        await interaction.message.edit(view=self)

    def disable_all_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

async def setup(bot):
    await bot.add_cog(AntiRyker(bot)) 