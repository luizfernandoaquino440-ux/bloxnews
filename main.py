import os
import asyncio
import xml.etree.ElementTree as ET
import aiohttp
from aiohttp import web
from google import genai
import discord
from discord.ext import commands

# 1. Servidor Web (Render Keep-Alive)
async def handle_ping(request):
    return web.Response(text="Bot BloxNews online!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# 2. Configuração do Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 3. Funções de Busca Real (RSS Feed oficial Roblox DevForum)
async def buscar_noticias_roblox_reais():
    url = "https://devforum.roblox.com/c/updates/45.rss"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    xml_data = await resp.text()
                    root = ET.fromstring(xml_data)
                    items = root.findall('./channel/item')[:3]
                    
                    noticias = []
                    for item in items:
                        titulo = item.find('title').text if item.find('title') is not None else ""
                        link = item.find('link').text if item.find('link') is not None else ""
                        noticias.append(f"- Título: {titulo}\n  Link: {link}")
                    
                    return "\n".join(noticias)
    except Exception as e:
        print(f"Erro ao buscar RSS: {e}")
    return None

# 4. Configuração do Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 BloxNews conectado com sucesso como: {bot.user}")

@bot.command(name="noticias")
async def noticias(ctx, *, jogo: str = None):
    async with ctx.typing():
        if jogo:
            await ctx.send(f"🔍 Buscando informações sobre **{jogo}** no Roblox...")
            prompt = (
                f"O usuário quer notícias sobre o jogo '{jogo}' no Roblox.\n"
                f"AVISO CRÍTICO: Se você NÃO tiver certeza absoluta de uma atualização recente e real deste jogo, "
                f"RESPONDA APENAS: 'Não encontrei atualizações oficiais recentes confirmadas para o jogo {jogo}. "
                f"Recomendo checar a página oficial do jogo no Roblox.'\n"
                f"NUNCA invente atualizações, mecânicas ou códigos fictícios. Se souber de fatos reais, resuma-os em 2 tópicos com Markdown."
            )
        else:
            await ctx.send("🔍 Obtendo as últimas novidades oficiais do Roblox...")
            dados_reais = await buscar_noticias_roblox_reais()
            
            if dados_reais:
                prompt = (
                    f"Abaixo estão os anúncios oficiais MAIS RECENTES do Roblox retirados diretamente do DevForum:\n\n"
                    f"{dados_reais}\n\n"
                    f"Sua tarefa: Resuma e formate esses tópicos oficiais para o Discord usando emojis, negritos e marcadores.\n"
                    f"NÃO adicione nenhuma informação externa que não esteja no texto acima."
                )
            else:
                prompt = (
                    "Traga um resumo curto sobre a plataforma Roblox e como acompanhar os eventos oficiais "
                    "no site roblox.com. Não invente eventos."
                )

        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt,
                )
            )
            texto = response.text.strip()

            if len(texto) <= 2000:
                await ctx.send(texto)
            else:
                for i in range(0, len(texto), 1900):
                    await ctx.send(texto[i:i+1900])

        except Exception as e:
            await ctx.send(f"⚠️ Erro ao processar notícias: `{e}`")

# 5. Loop Principal
async def main():
    await start_web_server()
    token = os.environ.get("TOKEN")
    if token:
        await bot.start(token)
    else:
        print("❌ ERRO: Variável TOKEN não configurada!")

if __name__ == "__main__":
    asyncio.run(main())
