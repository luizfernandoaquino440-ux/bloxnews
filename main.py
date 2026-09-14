import os
import asyncio
from duckduckgo_search import DDGS
from groq import Groq
from aiohttp import web
import discord
from discord.ext import commands

# 1. Servidor Web (Keep-Alive no Render)
async def handle_ping(request):
    return web.Response(text="Bot BloxNews online com Groq!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# 2. Cliente Groq API
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 3. Pesquisa Web em tempo real (DuckDuckGo)
def pesquisar_na_web(query):
    try:
        results = list(DDGS().text(query, max_results=4))
        if not results:
            return None
        
        texto_buscado = ""
        for r in results:
            texto_buscado += f"- Fonte ({r['title']}): {r['body']}\n Link: {r['href']}\n\n"
        return texto_buscado
    except Exception as e:
        print(f"Erro na busca web: {e}")
        return None

# 4. Configuração do Bot Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 BloxNews conectado com sucesso usando Groq como: {bot.user}")

@bot.command(name="noticias")
async def noticias(ctx, *, jogo: str = None):
    async with ctx.typing():
        loop = asyncio.get_running_loop()

        if jogo:
            await ctx.send(f"🔍 Pesquisando na web em tempo real sobre **{jogo}** no Roblox...")
            termo_busca = f"Roblox {jogo} latest update patch notes news"
        else:
            await ctx.send("🔍 Pesquisando as últimas notícias do Roblox na web...")
            termo_busca = "Roblox platform latest updates news events"

        resultados_web = await loop.run_in_executor(None, pesquisar_na_web, termo_busca)

        if resultados_web:
            prompt = (
                f"Você é o 'BloxNews', um jornalista especializado em Roblox.\n"
                f"Com base APENAS nos resultados de busca abaixo, crie um resumo objetivo das novidades:\n\n"
                f"{resultados_web}\n\n"
                f"REGRAS:\n"
                f"- Destaque as principais atualizações ou novidades encontradas.\n"
                f"- Formate com marcadores, emojis e negritos para o Discord.\n"
                f"- Seja direto e responda em português.\n"
                f"- Não inclua saudações ou despedidas."
            )
        else:
            prompt = (
                f"Informe resumidamente em português que você pesquisou sobre '{jogo if jogo else 'Roblox'}', "
                f"mas não encontrou atualizações recentes nas fontes da web no momento."
            )

        try:
            # Modelo estável e rápido garantido na Groq
            chat_completion = await loop.run_in_executor(
                None,
                lambda: groq_client.chat.completions.create(
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    model="llama-3.1-8b-instant",
                )
            )
            texto = chat_completion.choices[0].message.content.strip()

            if len(texto) <= 2000:
                await ctx.send(texto)
            else:
                for i in range(0, len(texto), 1900):
                    await ctx.send(texto[i:i+1900])

        except Exception as e:
            await ctx.send(f"⚠️ Erro ao gerar notícias com Groq: `{e}`")

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
