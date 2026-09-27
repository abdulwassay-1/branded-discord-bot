import discord
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import os
import io
import json
import time
import math
from datetime import datetime, timezone


# =========================================================
# SETTINGS
# =========================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

DATA_FILE = "member_data.json"

WIDTH = 1100
HEIGHT = 560

DARK_BLUE = (5, 12, 28)
BLUE = (35, 145, 255)
LIGHT_BLUE = (130, 215, 255)
WHITE = (245, 250, 255)


# =========================================================
# DISCORD INTENTS
# =========================================================

intents = discord.Intents.default()

intents.message_content = True
intents.members = True
intents.voice_states = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)


# =========================================================
# DATA
# =========================================================

def load_data():

    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return {}


member_data = load_data()


def save_data():

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(member_data, f, indent=4)


def ensure_member(user_id):

    user_id = str(user_id)

    if user_id not in member_data:

        member_data[user_id] = {
            "warnings": 0,
            "messages": 0,
            "voice_seconds": 0,
            "voice_join": None
        }

        save_data()


# =========================================================
# FONTS
# =========================================================

def font(size, bold=False):

    if bold:

        paths = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf"
        ]

    else:

        paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf"
        ]

    for path in paths:

        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


TITLE_FONT = font(42, True)
NAME_FONT = font(32, True)
LABEL_FONT = font(14, True)
VALUE_FONT = font(22, True)
SMALL_FONT = font(14)


# =========================================================
# RELATIVE TIME
# =========================================================

def format_age(dt):

    if dt is None:
        return "Unknown"

    now = datetime.now(timezone.utc)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    seconds = int((now - dt).total_seconds())

    if seconds < 60:

        return f"{max(seconds, 1)} second" + (
            "" if seconds == 1 else "s"
        )

    minutes = seconds // 60

    if minutes < 60:

        return f"{minutes} minute" + (
            "" if minutes == 1 else "s"
        )

    hours = minutes // 60

    if hours < 24:

        return f"{hours} hour" + (
            "" if hours == 1 else "s"
        )

    days = seconds // 86400

    if days < 30:

        return f"{days} day" + (
            "" if days == 1 else "s"
        )

    months = days // 30

    if months < 12:

        remaining_days = days % 30

        if remaining_days > 0:

            return (
                f"{months} month"
                f"{'' if months == 1 else 's'} "
                f"{remaining_days} day"
                f"{'' if remaining_days == 1 else 's'}"
            )

        return f"{months} month" + (
            "" if months == 1 else "s"
        )

    years = days // 365

    remaining_days = days - (years * 365)

    remaining_months = remaining_days // 30

    if remaining_months > 0:

        return (
            f"{years} year"
            f"{'' if years == 1 else 's'} "
            f"{remaining_months} month"
            f"{'' if remaining_months == 1 else 's'}"
        )

    return f"{years} year" + (
        "" if years == 1 else "s"
    )


# =========================================================
# VOICE TIME
# =========================================================

def format_voice(seconds):

    seconds = int(seconds)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return f"{hours}h {minutes}m"


# =========================================================
# SECURITY
# =========================================================

def security_risk(member):

    ensure_member(member.id)

    warnings = member_data[str(member.id)]["warnings"]

    account_age = (
        datetime.now(timezone.utc)
        - member.created_at
    ).days

    if warnings >= 5:
        return "HIGH"

    if warnings >= 2:
        return "MEDIUM"

    if account_age < 3:
        return "HIGH"

    if account_age < 30:
        return "MEDIUM"

    return "LOW"


# =========================================================
# FIRE EFFECT
# =========================================================

def draw_fire(draw, frame):

    base_y = 530

    for x in range(350, 1060, 35):

        wave = math.sin(
            frame * 0.8 + x * 0.08
        )

        height = int(
            28 + ((wave + 1) * 15)
        )

        # Outer flame
        draw.polygon(
            [
                (x, base_y),
                (x + 10, base_y - height),
                (x + 18, base_y - height // 2),
                (x + 28, base_y - height - 8),
                (x + 35, base_y)
            ],
            fill=(255, 85, 20)
        )

        # Inner flame
        inner = max(height - 14, 10)

        draw.polygon(
            [
                (x + 8, base_y),
                (x + 17, base_y - inner),
                (x + 25, base_y - 8),
                (x + 30, base_y)
            ],
            fill=(255, 210, 70)
        )


# =========================================================
# PROFILE GIF
# =========================================================

async def create_profile(member):

    ensure_member(member.id)

    data = member_data[str(member.id)]

    warnings = data["warnings"]

    messages = data["messages"]

    voice_seconds = data["voice_seconds"]

    # Current voice session
    if data.get("voice_join") is not None:

        voice_seconds += int(
            time.time() - data["voice_join"]
        )

    voice_time = format_voice(
        voice_seconds
    )

    joined = format_age(
        member.joined_at
    )

    created = format_age(
        member.created_at
    )

    risk = security_risk(
        member
    )

    # -------------------------------------------------------
    # AVATAR
    # -------------------------------------------------------

    try:

        avatar_bytes = await member.display_avatar.read()

        avatar = Image.open(
            io.BytesIO(avatar_bytes)
        ).convert("RGBA")

        avatar = avatar.resize(
            (270, 270),
            Image.Resampling.LANCZOS
        )

    except Exception:

        avatar = Image.new(
            "RGBA",
            (270, 270),
            (25, 60, 100, 255)
        )


    # -------------------------------------------------------
    # FRAMES
    # -------------------------------------------------------

    frames = []

    for frame in range(16):

        img = Image.new(
            "RGBA",
            (WIDTH, HEIGHT),
            DARK_BLUE + (255,)
        )

        draw = ImageDraw.Draw(img)

        # ---------------------------------------------------
        # BACKGROUND
        # ---------------------------------------------------

        for y in range(HEIGHT):

            ratio = y / HEIGHT

            r = int(4 + ratio * 5)
            g = int(10 + ratio * 12)
            b = int(25 + ratio * 30)

            draw.line(
                (0, y, WIDTH, y),
                fill=(r, g, b, 255)
            )

        # ---------------------------------------------------
        # BLUE GLOW
        # ---------------------------------------------------

        glow = Image.new(
            "RGBA",
            (WIDTH, HEIGHT),
            (0, 0, 0, 0)
        )

        glow_draw = ImageDraw.Draw(glow)

        pulse = int(
            30 + 15 * math.sin(frame * 0.5)
        )

        glow_draw.ellipse(
            (
                700 - pulse,
                -120 - pulse,
                1200 + pulse,
                350 + pulse
            ),
            fill=(30, 140, 255, 55)
        )

        glow = glow.filter(
            ImageFilter.GaussianBlur(55)
        )

        img = Image.alpha_composite(
            img,
            glow
        )

        draw = ImageDraw.Draw(img)

        # ---------------------------------------------------
        # MAIN CARD
        # ---------------------------------------------------

        draw.rounded_rectangle(
            (12, 12, WIDTH - 12, HEIGHT - 12),
            radius=28,
            fill=(8, 20, 40, 235),
            outline=BLUE + (255,),
            width=3
        )

        # ---------------------------------------------------
        # HEADER
        # ---------------------------------------------------

        draw.text(
            (390, 38),
            "BRANDED",
            font=TITLE_FONT,
            fill=WHITE
        )

        draw.text(
            (392, 88),
            "BRANDED COMMUNITY",
            font=LABEL_FONT,
            fill=LIGHT_BLUE
        )

        draw.line(
            (390, 120, 1040, 120),
            fill=BLUE,
            width=2
        )

        # ---------------------------------------------------
        # AVATAR GLOW
        # ---------------------------------------------------

        avatar_glow = Image.new(
            "RGBA",
            (WIDTH, HEIGHT),
            (0, 0, 0, 0)
        )

        glow_draw = ImageDraw.Draw(
            avatar_glow
        )

        glow_draw.rounded_rectangle(
            (35, 65, 325, 355),
            radius=25,
            outline=(30, 150, 255, 150),
            width=12
        )

        avatar_glow = avatar_glow.filter(
            ImageFilter.GaussianBlur(14)
        )

        img = Image.alpha_composite(
            img,
            avatar_glow
        )

        draw = ImageDraw.Draw(img)

        # ---------------------------------------------------
        # AVATAR
        # ---------------------------------------------------

        img.alpha_composite(
            avatar,
            (45, 75)
        )

        draw.rounded_rectangle(
            (40, 70, 320, 350),
            radius=20,
            outline=LIGHT_BLUE,
            width=3
        )

        # ---------------------------------------------------
        # NAME
        # ---------------------------------------------------

        draw.text(
            (370, 145),
            member.display_name,
            font=NAME_FONT,
            fill=WHITE
        )

        # ---------------------------------------------------
        # INFO BOX
        # ---------------------------------------------------

        def box(x, y, label, value):

            draw.rounded_rectangle(
                (x, y, x + 205, y + 72),
                radius=11,
                fill=(10, 25, 47, 245),
                outline=(55, 135, 220),
                width=2
            )

            draw.text(
                (x + 12, y + 9),
                label,
                font=LABEL_FONT,
                fill=(125, 190, 245)
            )

            draw.text(
                (x + 12, y + 36),
                str(value),
                font=VALUE_FONT,
                fill=WHITE
            )

        # ---------------------------------------------------
        # INFORMATION
        # ---------------------------------------------------

        box(
            370,
            200,
            "JOINED SERVER",
            joined
        )

        box(
            595,
            200,
            "ACCOUNT CREATED",
            created
        )

        box(
            820,
            200,
            "MESSAGES",
            messages
        )

        box(
            370,
            290,
            "WARNINGS",
            warnings
        )

        box(
            595,
            290,
            "VOICE TIME",
            voice_time
        )

        box(
            820,
            290,
            "SECURITY RISK",
            risk
        )

        # ---------------------------------------------------
        # USER INFORMATION
        # ---------------------------------------------------

        draw.text(
            (370, 385),
            f"@{member.name}",
            font=SMALL_FONT,
            fill=(160, 205, 240)
        )

        draw.text(
            (370, 412),
            f"USER ID: {member.id}",
            font=SMALL_FONT,
            fill=(100, 155, 205)
        )

        # ---------------------------------------------------
        # COMMUNITY BADGE
        # ---------------------------------------------------

        draw.rounded_rectangle(
            (790, 390, 1045, 440),
            radius=22,
            fill=(20, 105, 195, 255),
            outline=LIGHT_BLUE,
            width=2
        )

        draw.text(
            (812, 405),
            "BRANDED COMMUNITY",
            font=SMALL_FONT,
            fill=WHITE
        )

        # ---------------------------------------------------
        # PARTICLES
        # ---------------------------------------------------

        for i in range(22):

            x = (
                350
                + (
                    i * 71
                    + frame * 10
                ) % 690
            )

            y = (
                470
                - (
                    i * 17
                    + frame * 4
                ) % 65
            )

            radius = 1 + (i % 3)

            draw.ellipse(
                (
                    x,
                    y,
                    x + radius,
                    y + radius
                ),
                fill=(120, 215, 255, 190)
            )

        # ---------------------------------------------------
        # FIRE
        # ---------------------------------------------------

        draw_fire(
            draw,
            frame
        )

        # ---------------------------------------------------
        # SAVE FRAME
        # ---------------------------------------------------

        frames.append(
            img.convert("P")
        )


    # -------------------------------------------------------
    # CREATE GIF
    # -------------------------------------------------------

    output = io.BytesIO()

    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0,
        optimize=True
    )

    output.seek(0)

    return output


# =========================================================
# READY
# =========================================================

@bot.event
async def on_ready():

    print()
    print("==============================")
    print(" BRANDED COMMUNITY BOT ONLINE ")
    print("==============================")
    print(f"Logged in as: {bot.user}")
    print()


# =========================================================
# MEMBER JOIN
# =========================================================

@bot.event
async def on_member_join(member):

    ensure_member(
        member.id
    )


# =========================================================
# MESSAGE TRACKING
# =========================================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    ensure_member(
        message.author.id
    )

    member_data[
        str(message.author.id)
    ]["messages"] += 1

    save_data()

    await bot.process_commands(
        message
    )


# =========================================================
# VOICE TRACKING
# =========================================================

@bot.event
async def on_voice_state_update(
    member,
    before,
    after
):

    ensure_member(
        member.id
    )

    user_id = str(member.id)

    # Joined voice
    if (
        before.channel is None
        and after.channel is not None
    ):

        member_data[user_id][
            "voice_join"
        ] = time.time()

    # Left voice
    elif (
        before.channel is not None
        and after.channel is None
    ):

        joined = member_data[user_id].get(
            "voice_join"
        )

        if joined:

            elapsed = int(
                time.time() - joined
            )

            member_data[user_id][
                "voice_seconds"
            ] += elapsed

            member_data[user_id][
                "voice_join"
            ] = None

    save_data()


# =========================================================
# WARN
# =========================================================

@bot.command()
@commands.has_permissions(
    manage_messages=True
)
async def warn(
    ctx,
    member: discord.Member
):

    ensure_member(
        member.id
    )

    member_data[
        str(member.id)
    ]["warnings"] += 1

    save_data()

    count = member_data[
        str(member.id)
    ]["warnings"]

    await ctx.send(
        f"⚠️ {member.mention} now has "
        f"**{count} warning(s)**."
    )


# =========================================================
# UNWARN
# =========================================================

@bot.command()
@commands.has_permissions(
    manage_messages=True
)
async def unwarn(
    ctx,
    member: discord.Member
):

    ensure_member(
        member.id
    )

    if member_data[
        str(member.id)
    ]["warnings"] > 0:

        member_data[
            str(member.id)
        ]["warnings"] -= 1

    save_data()

    count = member_data[
        str(member.id)
    ]["warnings"]

    await ctx.send(
        f"✅ {member.mention} now has "
        f"**{count} warning(s)**."
    )


# =========================================================
# PRO
# =========================================================

@bot.command()
async def pro(ctx):

    print(
        f"!pro requested by {ctx.author}"
    )

    try:

        gif = await create_profile(
            ctx.author
        )

        file = discord.File(
            gif,
            filename="branded_profile.gif"
        )

        await ctx.send(
            file=file
        )

    except Exception as e:

        print(
            "PROFILE ERROR:",
            repr(e)
        )

        await ctx.send(
            "❌ Profile generate karte waqt error aa gaya."
        )


# =========================================================
# COMMAND ERRORS
# =========================================================

@bot.event
async def on_command_error(
    ctx,
    error
):

    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ You don't have permission "
            "to use this command."
        )

        return

    if isinstance(
        error,
        commands.MemberNotFound
    ):

        await ctx.send(
            "❌ Member nahi mila."
        )

        return

    if isinstance(
        error,
        commands.CommandNotFound
    ):

        return

    print(
        "COMMAND ERROR:",
        repr(error)
    )


# =========================================================
# START
# =========================================================

if not TOKEN:

    print(
        "❌ DISCORD_TOKEN .env file mein nahi mila."
    )

else:

    bot.run(TOKEN)