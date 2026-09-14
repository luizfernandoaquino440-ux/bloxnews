import os
import asyncio
from duckduckgo_search import DDGS
from google import genai
from aiohttp import web
import discord
from discord.ext import commands

# 1. Servidor Web (Render Keep-Alive)
async def handle_ping(request):
    return web.Response(text="Bot BloxNews online com Web Search!")

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

# 3. Função de Pesquisa Web Gratuita (DuckDuckGo)
def pesquisar_na_web(query):
    try:
        results = list(DDGS().text(query, max_results=3))
        if not results:
            return None
        
        texto_buscado = ""
        for r in results:
            texto_buscado += f"- Fonte ({r['title']}): {r['body']}\n Link: {r['href']}\n\n"
        return texto_buscado
    except Exception as e:
        print(f"Erro na busca web: {e}")
        return None

# 4. Bot Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 BloxNews conectado como: {bot.user}")

@bot.command(name="noticias")
async def noticias(ctx, *, jogo: str = None):
    async with ctx.typing():
        loop = asyncio.get_running_loop()

        if jogo:
            await ctx.send(f"🔍 Pesquisando na web em tempo real sobre **{jogo}** no Roblox...")
            termo_busca = f"Roblox {jogo} latest update patch notes news codes"
        else:
            await ctx.send("🔍 Pesquisando as últimas notícias gerais do Roblox na web...")
            termo_busca = f"Roblox platform latest updates news events"

        # Faz a busca web em segundo plano
        resultados_web = await loop.run_in_executor(None, pesquisar_na_web, termo_busca)

        if resultados_web:
            prompt = (
                f"Você é o 'BloxNews', um jornalista especializado em Roblox.\n"
                f"Com base APENAS nos resultados reais de busca da web abaixo, crie um resumo das novidades:\n\n"
                f"{resultados_web}\n\n"
                f"REGRAS:\n"
                f"- Destaque as principais atualizações, códigos ou novidades encontradas.\n"
                f"- Formate com marcadores, emojis e negritos para o Discord.\n"
                f"- Se houver links relevantes nos dados acima, adicione-os no final.\n"
                f"- Seja direto e sem saudações."
            )
        else:
            prompt = (
                f"Informe que você tentou pesquisar na web sobre '{jogo if jogo else 'Roblox'}', "
                f"mas não encontrou resultados recentes e peça para tentar novamente mais tarde."
            )

        try:
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
            await ctx.send(f"⚠️ Erro ao gerar resposta: `{e}`")

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
