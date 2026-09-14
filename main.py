import os
import asyncio
import datetime
from google import genai
from aiohttp import web
import discord
from discord.ext import commands

# 1. Servidor Web Fictício (Mantém o Render Free ativo)
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
        data_atual = datetime.date.today().strftime("%d/%m/%Y")
        
        if jogo:
            foco_instrucao = (
                f"Forneça um resumo detalhado e atualizado sobre as novidades mais marcantes, "
                f"atualizações de conteúdo, códigos ou notas de patch do jogo/experiência '{jogo}' no Roblox."
            )
            mensagem_espera = f"🔍 Buscando as principais novidades de **{jogo}** no Roblox..."
        else:
            foco_instrucao = (
                "Forneça um resumo das novidades e atualizações mais importantes da plataforma ROBLOX como um todo "
                "(eventos oficiais da Roblox Corp, atualizações do motor/engine, ferramentas de desenvolvimento ou feiras de comunidade)."
            )
            mensagem_espera = "🔍 Buscando as últimas novidades da plataforma Roblox..."

        await ctx.send(mensagem_espera)

        prompt = (
            f"Hoje é {data_atual}.\n"
            f"Você é o 'BloxNews', um jornalista especialista em Roblox.\n"
            f"{foco_instrucao}\n\n"
            f"DIRETRIZES DE RESPOSTA:\n"
            f"- Priorize atualizações recentes e relevantes. Ignore mecânicas antigas de anos atrás.\n"
            f"- Apresente de 2 a 3 tópicos bem explicados e organizados.\n"
            f"- Utilize a formatação do Discord (negritos, listas em marcadores e emojis do tema).\n"
            f"- Responda diretamente no formato final, sem saudações ou despedidas."
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
            await ctx.send(f"⚠️ Erro ao consultar o Gemini: `{e}`")

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
