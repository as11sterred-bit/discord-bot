import os
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
TICKET_CHANNEL_ID = int(os.getenv("TICKET_CHANNEL_ID", "0"))

if not TOKEN:
    raise RuntimeError("В файле .env отсутствует DISCORD_TOKEN")


MAIN_COLOR = 0x55B8E8
ASSETS_DIR = Path(__file__).parent / "assets"

IMAGE_FILES = {
    "navigation": "navigation.png",
    "start": "how-to-start.png",
    "about": "about-server.png",
    "modpack": "modpack.png",
    "help": "help.png",
    "website": "website.png",
}


def create_info_embed(title: str, description: str) -> discord.Embed:
    """Создаёт одинаково оформленные информационные окна."""

    return discord.Embed(
        title=title,
        description=description,
        color=MAIN_COLOR,
    )


def add_banner(embed: discord.Embed, image_name: str) -> discord.File:
    """Добавляет к карточке локальный баннер и возвращает его для отправки."""

    filename = IMAGE_FILES[image_name]
    embed.set_image(url=f"attachment://{filename}")
    return discord.File(ASSETS_DIR / filename, filename=filename)


class WebsiteView(discord.ui.View):
    """Кнопка перехода из карточки сайта."""

    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(
            discord.ui.Button(
                label="Открыть frplay.ru",
                emoji="🌐",
                style=discord.ButtonStyle.link,
                url="https://frplay.ru",
            )
        )


class NavigationView(discord.ui.View):
    """Кнопки общей навигационной панели."""

    def __init__(self):
        # timeout=None позволяет зарегистрировать панель как постоянную.
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Как начать",
        emoji="🚀",
        style=discord.ButtonStyle.primary,
        custom_id="fantasyrp:navigation:start",
    )
    async def start_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        embed = create_info_embed(
            "Как начать играть",
            (
                "**1. Зарегистрируйтесь** на [frplay.ru](https://frplay.ru).\n\n"
                "**2. Заполните заявку** на вступление в проект.\n\n"
                "**3. Дождитесь её рассмотрения.** "
                "Результат можно проверить на сайте.\n\n"
                "**4. После принятия заявки скачайте лаунчер.** "
                "Он самостоятельно установит Minecraft и необходимую сборку.\n\n"
                "**5. Запустите игру через лаунчер** и присоединяйтесь к серверу."
            ),
        )

        embed.set_footer(
            text="Для игры используется Minecraft Java Edition 1.20.1"
        )

        banner = add_banner(embed, "start")

        await interaction.response.send_message(
            embed=embed,
            file=banner,
            ephemeral=True,
        )

    @discord.ui.button(
        label="О сервере",
        emoji="🧭",
        style=discord.ButtonStyle.secondary,
        custom_id="fantasyrp:navigation:about",
    )
    async def about_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        embed = create_info_embed(
            "О сервере FantasyRP",
            (
                "**FantasyRP** — ролевой Minecraft-сервер, на котором "
                "история мира создаётся самими игроками.\n\n"
                "Основывайте государства, участвуйте в общем сюжете, "
                "развивайте поселения и выстраивайте собственную экономику. "
                "Можно влиять на большие события мира или выбрать более "
                "спокойный путь развития и выживания — направление зависит "
                "от вас.\n\n"
                "Правила проекта, заявки и дополнительная информация "
                "размещены на [официальном сайте](https://frplay.ru)."
            ),
        )

        banner = add_banner(embed, "about")

        await interaction.response.send_message(
            embed=embed,
            file=banner,
            ephemeral=True,
        )

    @discord.ui.button(
        label="Сборка",
        emoji="🧩",
        style=discord.ButtonStyle.secondary,
        custom_id="fantasyrp:navigation:modpack",
    )
    async def modpack_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        embed = create_info_embed(
            "Игровая сборка",
            (
                "**Версия:** Minecraft Java Edition 1.20.1\n"
                "**Количество модов:** более 130\n\n"
                "Самостоятельно устанавливать Minecraft и моды не нужно. "
                "После принятия заявки скачайте фирменный лаунчер с сайта — "
                "он подготовит игру и установит актуальную версию сборки.\n\n"
                "Запускайте сервер только через этот лаунчер, чтобы версия "
                "клиента совпадала с серверной."
            ),
        )

        banner = add_banner(embed, "modpack")

        await interaction.response.send_message(
            embed=embed,
            file=banner,
            ephemeral=True,
        )

    @discord.ui.button(
        label="Помощь",
        emoji="🎫",
        style=discord.ButtonStyle.success,
        custom_id="fantasyrp:navigation:help",
    )
    async def help_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        ticket_channel = None

        if interaction.guild and TICKET_CHANNEL_ID:
            ticket_channel = interaction.guild.get_channel(
                TICKET_CHANNEL_ID
            )

        if ticket_channel:
            description = (
                "Если возникла проблема с регистрацией, заявкой, "
                "лаунчером или входом на сервер, создайте обращение в "
                f"{ticket_channel.mention}.\n\n"
                "Опишите проблему и, если возможно, приложите скриншот ошибки."
            )
        else:
            description = (
                "Канал помощи пока не настроен. "
                "Обратитесь к администрации сервера."
            )

        embed = create_info_embed(
            "Нужна помощь?",
            description,
        )

        banner = add_banner(embed, "help")

        await interaction.response.send_message(
            embed=embed,
            file=banner,
            ephemeral=True,
        )

    @discord.ui.button(
        label="Сайт",
        emoji="🌐",
        style=discord.ButtonStyle.primary,
        custom_id="fantasyrp:navigation:website",
    )
    async def website_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        embed = create_info_embed(
            "Официальный сайт FantasyRP",
            (
                "На сайте можно зарегистрироваться, подать заявку, "
                "ознакомиться с правилами проекта и после принятия заявки "
                "скачать игровой лаунчер."
            ),
        )

        banner = add_banner(embed, "website")

        await interaction.response.send_message(
            embed=embed,
            file=banner,
            view=WebsiteView(),
            ephemeral=True,
        )


class FantasyBot(commands.Bot):
    async def setup_hook(self):
        # Регистрируем кнопки старых панелей после перезапуска бота.
        self.add_view(NavigationView())

        synced_commands = await self.tree.sync()
        print(f"Загружено команд: {len(synced_commands)}")


intents = discord.Intents.default()

bot = FantasyBot(
    command_prefix="!",
    intents=intents,
)


@bot.event
async def on_ready():
    print(f"Бот запущен: {bot.user}")


@bot.tree.command(
    name="panel",
    description="Опубликовать навигационную панель FantasyRP",
)
@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def panel(interaction: discord.Interaction):
    main_embed = discord.Embed(
        title="Навигация FantasyRP",
        description=(
            "Добро пожаловать на **FantasyRP**!\n\n"
            "Здесь собрана основная информация о проекте, "
            "подключении и игровой сборке. Выберите нужный раздел ниже."
        ),
        color=MAIN_COLOR,
    )

    main_embed.add_field(
        name="Версия",
        value="Java Edition 1.20.1",
        inline=True,
    )

    main_embed.add_field(
        name="Сборка",
        value="Более 130 модов",
        inline=True,
    )

    main_embed.add_field(
        name="Вступление",
        value="Через заявку на сайте",
        inline=True,
    )

    main_embed.set_footer(
        text="FantasyRP • Ваше путешествие начинается здесь"
    )

    banner = add_banner(main_embed, "navigation")

    # Подтверждаем команду, чтобы Discord не решил, что бот завис.
    await interaction.response.defer(ephemeral=True)

    if interaction.channel is None:
        await interaction.followup.send(
            "Не удалось определить канал.",
            ephemeral=True,
        )
        return

    await interaction.channel.send(
        embed=main_embed,
        file=banner,
        view=NavigationView(),
    )

    await interaction.followup.send(
        "Навигационная панель опубликована.",
        ephemeral=True,
    )


@panel.error
async def panel_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
):
    if isinstance(error, app_commands.MissingPermissions):
        message = "Эту команду могут использовать только администраторы."

        if interaction.response.is_done():
            await interaction.followup.send(
                message,
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                message,
                ephemeral=True,
            )
        return

    raise error


bot.run(TOKEN)
