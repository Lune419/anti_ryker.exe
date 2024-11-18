import discord
from discord import app_commands
from discord.ext import commands
import os
import json

# 讀取設定檔
with open('settings.json', 'r', encoding='utf8') as jfile:
    jdata = json.load(jfile)

# 設置機器人意圖
intents = discord.Intents.all()
intents.message_content = True

# 創建機器人實例
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        
    async def setup_hook(self):
        # 載入所有cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        # 同步斜線命令
        await self.tree.sync()
        
    async def on_ready(self):
        print(f'已登入為 {self.user}')
        
bot = Bot()

# 運行機器人
bot.run(jdata['token'])