import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite

class RykerJoinListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'database/ryker.db'
        self.bot.loop.create_task(self.setup_database())
        
    async def setup_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            # 創建通知頻道設定表
            await db.execute('''
                CREATE TABLE IF NOT EXISTS notification_channels (
                    guild_id TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL
                )
            ''')
            await db.commit()
            
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # 檢查加入的用戶是否在Ryker資料庫中
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT reason FROM ryker_accounts WHERE user_id = ?',
                (str(member.id),)
            ) as cursor:
                ryker_info = await cursor.fetchone()
                
                if not ryker_info:
                    return
                    
            # 獲取該伺服器的通知頻道ID
            async with db.execute(
                'SELECT channel_id FROM notification_channels WHERE guild_id = ?',
                (str(member.guild.id),)
            ) as cursor:
                result = await cursor.fetchone()
                
                if not result:
                    return
                    
                channel_id = int(result[0])
                channel = member.guild.get_channel(channel_id)
                
                if not channel:
                    return
                    
                # 發送通知
                embed = discord.Embed(
                    title="⚠️ Ryker用戶加入提醒",
                    description=f"{member.mention} 已加入伺服器",
                    color=discord.Color.red()
                )
                embed.add_field(name="用戶ID", value=str(member.id))
                embed.add_field(name="原因", value=ryker_info[0])
                
                await channel.send(embed=embed)
                
    @app_commands.command(name="set_notification", description="設定Ryker通知頻道（需要管理員權限）")
    @app_commands.describe(channel="要設定的通知頻道")
    @app_commands.default_permissions(administrator=True)
    @commands.has_permissions(administrator=True)
    async def set_notification(self, interaction: discord.Interaction, channel: discord.TextChannel):
        # 檢查用戶是否有管理員權限
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ 此指令需要管理員權限", ephemeral=True)
            return
            
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO notification_channels (guild_id, channel_id)
                    VALUES (?, ?)
                ''', (str(interaction.guild_id), str(channel.id)))
                await db.commit()
                
            embed = discord.Embed(
                title="✅ 通知頻道設定成功",
                description=f"已將 {channel.mention} 設為Ryker通知頻道",
                color=discord.Color.green()
            )
            embed.add_field(name="設定者", value=interaction.user.mention)
            embed.add_field(name="伺服器", value=interaction.guild.name)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ 設定失敗：{str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(RykerJoinListener(bot))