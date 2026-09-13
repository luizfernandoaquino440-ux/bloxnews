import os
import aiohttp
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'🤖 Bot {bot.user} está online!')

@bot.command(name="noticias")
async def noticias_roblox(ctx):
    await ctx.send("🤖 *Buscando novidades do Roblox... Aguarde!*")

    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    prompt = (
        "Você é um jornalista especialista em Roblox. "
        "Traga um resumo com as notícias, atualizações e novidades mais recentes do Roblox. "
        "Use tópicos curtos, negritos e emojis. Responda em português do Brasil de forma direta."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    texto_da_ia = data['candidates'][0]['content']['parts'][0]['text']
                    
                    embed = discord.Embed(
                        title="📰 Giro de Notícias Roblox",
                        description=texto_da_ia,
                        color=discord.Color.blue()
                    )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Erro ao falar com a IA. Verifique a chave do Gemini.")
    except Exception:
        await ctx.send("❌ Erro ao tentar gerar as notícias.")

bot.run(os.environ.get('TOKEN'))