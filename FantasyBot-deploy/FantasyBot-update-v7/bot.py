import os
import re
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
TICKET_CATEGORY_ID = int(
    os.getenv("TICKET_CATEGORY_ID", "1219289659318734928")
)

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
    "tickets": "ticket-panel-v7.png",
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


TICKET_TOPICS = {
    "technical": (
        "Техническая проблема",
        "Ошибки лаунчера, установки сборки, запуска игры или подключения.",
    ),
    "account": (
        "Заявка или аккаунт",
        "Регистрация, рассмотрение заявки и доступ к аккаунту FantasyRP.",
    ),
    "complaint": (
        "Жалоба",
        "Нарушение правил или ситуация, требующая внимания администрации.",
    ),
    "other": (
        "Другой вопрос",
        "Вопрос, который не подходит под остальные категории.",
    ),
}


def ticket_owner_id(channel: discord.TextChannel):
    """Возвращает ID автора тикета из темы канала."""

    if not channel.topic:
        return None

    match = re.search(r"fantasyrp-ticket-owner:(\d+)", channel.topic)
    return int(match.group(1)) if match else None


def can_close_ticket(
    member: discord.Member,
    channel: discord.TextChannel,
) -> bool:
    """Закрывать тикет может его автор или администратор."""

    return (
        member.guild_permissions.administrator
        or ticket_owner_id(channel) == member.id
    )


class TicketCloseConfirmView(discord.ui.View):
    """Подтверждение защищает тикет от случайного удаления."""

    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(
        label="Да, закрыть",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
    )
    async def confirm_close(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "Эта кнопка работает только внутри тикета.",
                ephemeral=True,
            )
            return

        if not isinstance(interaction.user, discord.Member) or not can_close_ticket(
            interaction.user,
            interaction.channel,
        ):
            await interaction.response.send_message(
                "Закрыть тикет может его автор или администратор.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "Тикет закрывается…",
            ephemeral=True,
        )
        await interaction.channel.delete(
            reason=f"Тикет закрыт пользователем {interaction.user}"
        )

    @discord.ui.button(
        label="Отмена",
        style=discord.ButtonStyle.secondary,
    )
    async def cancel_close(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content="Закрытие отменено.",
            view=self,
        )


class TicketCloseView(discord.ui.View):
    """Постоянная кнопка управления созданным тикетом."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Закрыть тикет",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="fantasyrp:ticket:close",
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "Эта кнопка работает только внутри тикета.",
                ephemeral=True,
            )
            return

        if not isinstance(interaction.user, discord.Member) or not can_close_ticket(
            interaction.user,
            interaction.channel,
        ):
            await interaction.response.send_message(
                "Закрыть тикет может его автор или администратор.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "Закрыть этот тикет? Канал и его сообщения будут удалены.",
            view=TicketCloseConfirmView(),
            ephemeral=True,
        )


class TicketCategoryView(discord.ui.View):
    """Выбор причины обращения и создание приватного канала."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Выберите тему обращения…",
        min_values=1,
        max_values=1,
        custom_id="fantasyrp:ticket:category",
        options=[
            discord.SelectOption(
                label="Техническая проблема",
                value="technical",
                emoji="🛠️",
                description="Лаунчер, сборка, запуск или подключение",
            ),
            discord.SelectOption(
                label="Заявка или аккаунт",
                value="account",
                emoji="📝",
                description="Регистрация, заявка и доступ к аккаунту",
            ),
            discord.SelectOption(
                label="Жалоба",
                value="complaint",
                emoji="⚖️",
                description="Нарушение правил или спорная ситуация",
            ),
            discord.SelectOption(
                label="Другой вопрос",
                value="other",
                emoji="💬",
                description="Всё, что не вошло в остальные категории",
            ),
        ],
    )
    async def select_category(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select,
    ):
        if interaction.guild is None or not isinstance(
            interaction.user,
            discord.Member,
        ):
            await interaction.response.send_message(
                "Создать тикет можно только на сервере.",
                ephemeral=True,
            )
            return

        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        if not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message(
                "Категория для тикетов не найдена. Сообщите администрации.",
                ephemeral=True,
            )
            return

        owner_marker = f"fantasyrp-ticket-owner:{interaction.user.id}"
        existing_ticket = next(
            (
                channel
                for channel in category.text_channels
                if channel.topic and owner_marker in channel.topic
            ),
            None,
        )

        if existing_ticket:
            await interaction.response.send_message(
                f"У вас уже есть открытый тикет: {existing_ticket.mention}",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        topic_key = select.values[0]
        topic_title, topic_description = TICKET_TOPICS[topic_key]
        safe_name = re.sub(
            r"[^a-zа-яё0-9]+",
            "-",
            interaction.user.display_name.lower(),
        ).strip("-")
        safe_name = safe_name[:24] or "user"

        bot_member = interaction.guild.me
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                view_channel=False,
            ),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
            ),
        }

        if bot_member:
            overwrites[bot_member] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
            )

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{safe_name}-{interaction.user.id % 10000:04d}",
            category=category,
            topic=f"{owner_marker};type:{topic_key}",
            overwrites=overwrites,
            reason=f"Тикет создан пользователем {interaction.user}",
        )

        welcome_embed = create_info_embed(
            f"{topic_title} • обращение открыто",
            (
                f"{topic_description}\n\n"
                "**Чтобы мы помогли быстрее:**\n"
                "• подробно опишите, что произошло;\n"
                "• укажите, что уже пробовали сделать;\n"
                "• приложите скриншот или текст ошибки, если они есть.\n\n"
                "Администрация ответит здесь, когда освободится. "
                "Не отмечайте сотрудников повторно без необходимости."
            ),
        )
        welcome_embed.set_footer(
            text="Когда вопрос решён, закройте обращение кнопкой ниже"
        )

        await channel.send(
            content=interaction.user.mention,
            embed=welcome_embed,
            view=TicketCloseView(),
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=False,
                everyone=False,
            ),
        )
        await interaction.followup.send(
            f"Обращение создано: {channel.mention}",
            ephemeral=True,
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
                "Путь на сервер состоит из нескольких простых шагов. "
                "Так мы знакомимся с новыми игроками и сохраняем атмосферу "
                "общего ролевого мира.\n\n"
                "**1. Создайте аккаунт** на [frplay.ru](https://frplay.ru).\n"
                "Используйте актуальные данные, чтобы не потерять доступ.\n\n"
                "**2. Заполните заявку на вступление.**\n"
                "Расскажите о себе и своём игровом опыте спокойно и честно — "
                "важнее понятные ответы, а не их объём.\n\n"
                "**3. Дождитесь решения администрации.**\n"
                "Статус заявки можно проверить в личном кабинете на сайте.\n\n"
                "**4. После одобрения скачайте фирменный лаунчер.**\n"
                "Он установит подходящую версию Minecraft и актуальную сборку.\n\n"
                "**5. Запустите игру через лаунчер** и подключитесь к серверу. "
                "Если появится ошибка, откройте раздел «Помощь» и приложите "
                "скриншот проблемы."
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
                "история мира складывается из решений и поступков игроков.\n\n"
                "**Чем можно заниматься:**\n"
                "• основывать государства и развивать поселения;\n"
                "• участвовать в общем сюжете и создавать собственные истории;\n"
                "• выстраивать торговлю, дипломатию и игровую экономику;\n"
                "• исследовать мир и выбирать спокойный путь развития.\n\n"
                "Ролевая игра не требует постоянно находиться в центре событий. "
                "Можно влиять на крупные перемены или постепенно развивать "
                "своего персонажа и окружение — направление выбираете вы.\n\n"
                "Перед началом ознакомьтесь с правилами и устройством проекта "
                "на [официальном сайте](https://frplay.ru)."
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
                "Сборка дополняет привычный Minecraft и служит технической "
                "основой игрового мира FantasyRP. Самостоятельно искать и "
                "устанавливать отдельные моды не требуется.\n\n"
                "**Как установить:**\n"
                "• дождитесь одобрения заявки;\n"
                "• скачайте фирменный лаунчер с официального сайта;\n"
                "• войдите в аккаунт и дождитесь окончания установки;\n"
                "• запускайте игру только через этот лаунчер.\n\n"
                "Лаунчер поддерживает сборку в актуальном состоянии. Не меняйте "
                "файлы модов вручную: несовпадение версий может помешать входу "
                "на сервер. При проблемах сообщите текст ошибки в тикете."
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
        embed = create_info_embed(
            "Нужна помощь?",
            (
                "Для обращений работает отдельный центр поддержки. Перейдите "
                "в канал с панелью тикетов и выберите подходящую категорию — "
                "бот создаст приватный канал для общения с администрацией.\n\n"
                "**Перед созданием тикета:**\n"
                "• выберите наиболее подходящую категорию;\n"
                "• подготовьте понятное описание ситуации;\n"
                "• приложите скриншот или текст ошибки, если они есть.\n\n"
                "Для одного вопроса достаточно одного тикета. Ответ может занять "
                "время — администрация увидит обращение и вернётся к вам."
            ),
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
                "[frplay.ru](https://frplay.ru) — основная точка входа в "
                "FantasyRP. Там собрана информация, которая нужна до начала "
                "игры и во время участия в проекте.\n\n"
                "**На сайте можно:**\n"
                "• зарегистрировать аккаунт;\n"
                "• заполнить и проверить статус заявки;\n"
                "• ознакомиться с правилами проекта;\n"
                "• после одобрения скачать игровой лаунчер.\n\n"
                "Используйте только официальный сайт — так вы получите "
                "актуальные файлы и не рискуете данными своего аккаунта."
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
        self.add_view(TicketCategoryView())
        self.add_view(TicketCloseView())

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
            "Это отправная точка для знакомства с проектом. Здесь можно узнать, "
            "как попасть на сервер, чем живёт игровой мир, как установить "
            "сборку и куда обратиться, если возникнет проблема.\n\n"
            "Выберите нужный раздел ниже — информация откроется лично для вас "
            "и не будет загромождать канал."
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


@bot.tree.command(
    name="ticket-panel",
    description="Опубликовать панель создания тикетов FantasyRP",
)
@app_commands.guild_only()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel(interaction: discord.Interaction):
    embed = create_info_embed(
        "Центр поддержки FantasyRP",
        (
            "Здесь можно создать приватное обращение к администрации. "
            "Выберите тему в меню ниже — после этого появится отдельный канал, "
            "доступный только вам и администраторам.\n\n"
            "**Категории обращений:**\n"
            "🛠️ **Техническая проблема** — лаунчер, сборка или подключение;\n"
            "📝 **Заявка или аккаунт** — регистрация и доступ;\n"
            "⚖️ **Жалоба** — нарушение правил или спорная ситуация;\n"
            "💬 **Другой вопрос** — всё остальное.\n\n"
            "Создавайте один тикет на один вопрос и сразу описывайте ситуацию "
            "подробно. Скриншоты и текст ошибки помогут решить проблему быстрее."
        ),
    )
    embed.set_footer(
        text="FantasyRP • Поддержка игроков"
    )
    banner = add_banner(embed, "tickets")

    await interaction.response.defer(ephemeral=True)

    if interaction.channel is None:
        await interaction.followup.send(
            "Не удалось определить канал.",
            ephemeral=True,
        )
        return

    await interaction.channel.send(
        embed=embed,
        file=banner,
        view=TicketCategoryView(),
    )
    await interaction.followup.send(
        "Панель тикетов опубликована.",
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


@ticket_panel.error
async def ticket_panel_error(
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
