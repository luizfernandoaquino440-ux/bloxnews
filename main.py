import os
import asyncio
from google import genai
from google.genai import types
from aiohttp import web
import discord
from discord.ext import commands

# 1. Servidor Web Fictício (Mantém o Render Free ativo)
async def handle_ping(request):
    return web.Response(text="Bot BloxNews online com Google Search!")

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

# 3. Configuração do Bot do Discord
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
            foco_instrucao = (
                f"Pesquise profundamente na web sobre as ÚLTIMAS atualizações, notas de patch, "
                f"eventos de tempo limitado, sneaks, códigos e novidades do jogo '{jogo}' no Roblox."
            )
            mensagem_espera = f"🔍 Pesquisando afundo na web sobre **{jogo}** no Roblox..."
        else:
            foco_instrucao = (
                "Pesquise profundamente na web sobre os acontecimentos mais RECENTES do PRÓPRIO ROBLOX como plataforma "
                "(eventos oficiais vigentes, anúncios da Roblox Corp, atualizações do motor/plataforma ou The Hunt/Innovation Awards)."
            )
            mensagem_espera = "🔍 Pesquisando afundo na web sobre as novidades da plataforma Roblox..."

        await ctx.send(mensagem_espera)

        prompt = (
            f"Você é o 'BloxNews', um jornalista investigativo especializado em Roblox.\n"
            f"{foco_instrucao}\n\n"
            f"REGRAS OBRIGATÓRIAS:\n"
            f"- Use a ferramenta de pesquisa para buscar fatos e dados RECENTES.\n"
            f"- Traga apenas de 2 a 3 notícias marcantes e confirmadas.\n"
            f"- Explique o que mudou ou o que está acontecendo AGORA (ignore updates antigos de meses atrás).\n"
            f"- Formatado para Discord com negritos, tópicos em marcadores e emojis temáticos.\n"
            f"- Não inclua saudações genéricas no começo ou no final."
        )

        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt,
                    # Ativa a pesquisa em tempo real no Google
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
            )
            texto = response.text.strip()

            if len(texto) <= 2000:
                await ctx.send(texto)
            else:
                for i in range(0, len(texto), 1900):
                    await ctx.send(texto[i:i+1900])

        except Exception as e:
            await ctx.send(f"⚠️ Erro ao consultar a pesquisa do Gemini: `{e}`")

# 4. Loop Principal
async def main():
    await start_web_server()
    token = os.environ.get("TOKEN")
    if token:
        await bot.start(token)
    else:
        print("❌ ERRO: Variável TOKEN não foi configurada no Render!")

if __name__ == "__main__":
    asyncio.run(main())
