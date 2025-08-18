# Boot message
print("Booting up...")

import discord
from discord import app_commands 
from discord.ext import commands
import os
from discord import ui
from discord import app_commands, Interaction, SelectOption, Embed
from discord.ui import View, Select, Modal, TextInput
from datetime import datetime, timedelta, timezone

from flask import Flask
from threading import Thread

# ------------------- Keep Alive Webserver -------------------
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()


# ------------------- Discord Bot -------------------
# Vul hier je server-ID in (voor slash commands in 1 server)
GUILD_ID = 1342974632524775526

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True


bot = commands.Bot(command_prefix="/", intents=intents)
bot.role_embed_data = {}  # opslag voor role embeds


# Event: bot ready
@bot.event
async def on_ready():
    print(f"✅ Bot ingelogd als {bot.user}")
    try:
        # Alleen in 1 server syncen (snelste)
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"🌐 Slash commands gesynchroniseerd: {len(synced)}")
    except Exception as e:
        print(f"❌ Fout bij sync: {e}")


# ------------------- Commands -------------------
@bot.tree.command(
    name="ping",
    description="Check de latency van de bot (alleen voor speciale rol)",
    guild=discord.Object(id=GUILD_ID)
)
async def ping(interaction: discord.Interaction):
    allowed_role = 1402417593419305060  # vereiste rol-ID
    if allowed_role not in [r.id for r in interaction.user.roles]:
        await interaction.response.send_message(
            "❌ Je hebt geen toegang tot dit commando.", ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"Pong! `{bot.latency*1000:.2f}ms`", ephemeral=True
    )


# ------------------- Embed Modal -------------------
class EmbedModal(discord.ui.Modal, title="Maak een Embed"):
    titel = discord.ui.TextInput(label="Titel",
                                 style=discord.TextStyle.short,
                                 placeholder="Bijv. Mededeling",
                                 required=True,
                                 max_length=100)
    beschrijving = discord.ui.TextInput(
        label="Beschrijving",
        style=discord.TextStyle.paragraph,
        placeholder="Tekst die in de embed verschijnt",
        required=True,
        max_length=2000)
    kleur = discord.ui.TextInput(label="Kleur (hex of none)",
                                 style=discord.TextStyle.short,
                                 placeholder="#2ecc71",
                                 required=False,
                                 max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        kleur_input = self.kleur.value or "#2ecc71"
        if kleur_input.lower() == "none":
            color = discord.Color.default()
        else:
            try:
                color = discord.Color(int(kleur_input.strip("#"), 16))
            except:
                color = discord.Color.default()

        embed = discord.Embed(title=self.titel.value,
                              description=self.beschrijving.value,
                              color=color)
        embed.set_footer(text=f"Gemaakt door 𝑹𝒐𝒅𝒓𝒊𝒈𝒆𝒖𝒛 𝐂𝐨𝐦𝐦𝐮𝐧𝐢𝐭𝐲")

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Kon guild niet vinden.",
                                                    ephemeral=True)
            return

        options = [
            discord.SelectOption(label=ch.name, value=str(ch.id))
            for ch in guild.text_channels[:25]
        ]

        class ChannelSelect(discord.ui.View):

            @discord.ui.select(placeholder="Kies een kanaal", options=options)
            async def select_callback(self,
                                      select_interaction: discord.Interaction,
                                      select: discord.ui.Select):
                kanaal_id = int(select.values[0])
                kanaal = guild.get_channel(kanaal_id)
                if kanaal is None:
                    await select_interaction.response.edit_message(
                        content="Kanaal niet gevonden.", view=None)
                    return
                await kanaal.send(embed=embed)
                await select_interaction.response.edit_message(
                    content=f"✅ Embed gestuurd naar {kanaal.mention}",
                    view=None)

        await interaction.response.send_message(
            "Kies een kanaal voor je embed:",
            view=ChannelSelect(),
            ephemeral=True)


@bot.tree.command(
    name="embed",
    description="Maak een embed via een formulier",
    guild=discord.Object(id=GUILD_ID)
)
async def embed(interaction: discord.Interaction):
    allowed_roles = {
        1402418713612910663,
        1403013958562218054,
        1342974632524775528,
        1405597740494356631,
        1402419665808134395
    }

    if not any(r.id in allowed_roles for r in interaction.user.roles):
        await interaction.response.send_message(
            "❌ Je hebt geen toegang tot dit commando.", ephemeral=True
        )
        return

    modal = EmbedModal()
    await interaction.response.send_modal(modal)


# ------------------- Role Embed Modal -------------------
class RoleEmbedModal(discord.ui.Modal, title="Maak een Role Embed"):
    titel = discord.ui.TextInput(label="Titel",
                                 style=discord.TextStyle.short,
                                 placeholder="Bijv. Kies je rol",
                                 required=True,
                                 max_length=100)
    beschrijving = discord.ui.TextInput(
        label="Beschrijving (embed tekst)",
        style=discord.TextStyle.paragraph,
        placeholder="Tekst die in de role-embed verschijnt",
        required=True,
        max_length=4000)
    mapping = discord.ui.TextInput(
        label="Mapping (emoji:role_id of emoji:RoleName)",
        style=discord.TextStyle.short,
        placeholder="Bijv: ✅:1402417593419305060, 🎮:Gamer",
        required=True,
        max_length=200)
    
    thumbnail = discord.ui.TextInput(
        label="Thumbnail (URL, optioneel)",
        style=discord.TextStyle.short,
        placeholder="https://example.com/thumb.png of type 'serverlogo'",
        required=False,
        max_length=200
    )
    kleur = discord.ui.TextInput(label="Kleur (hex of none)",
                                 style=discord.TextStyle.short,
                                 placeholder="#2ecc71",
                                 required=False,
                                 max_length=10)


    async def on_submit(self, interaction: discord.Interaction):
        # kleur instellen
        kleur_input = self.kleur.value or "#2ecc71"
        if kleur_input.lower() == "none":
            color = discord.Color.default()
        else:
            try:
                color = discord.Color(int(kleur_input.strip("#"), 16))
            except:
                color = discord.Color.default()

        embed = discord.Embed(
            title=self.titel.value,
            description=self.beschrijving.value,
            color=color
        )

        if self.thumbnail.value:
            if self.thumbnail.value.lower() == "serverlogo" and interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            else:
                embed.set_thumbnail(url=self.thumbnail.value)
        elif interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        if interaction.guild.icon:
            embed.set_footer(
                text=f"Gemaakt door {interaction.guild.name}",
                icon_url=interaction.guild.icon.url
            )
        else:
            embed.set_footer(text=f"Gemaakt door {interaction.guild.name}")
    
        # mapping parsen
        raw_map = {}
        for part in self.mapping.value.split(","):
            if ":" in part:
                left, right = part.split(":", 1)
                emoji_text = left.strip()
                role_part = right.strip()
                if emoji_text and role_part:
                    raw_map[emoji_text] = role_part

        if not raw_map:
            await interaction.response.send_message(
                "Geen geldige mapping gevonden. Gebruik format emoji:role_id of emoji:RoleName",
                ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Kon guild niet vinden.",
                                                    ephemeral=True)
            return

        options = [
            discord.SelectOption(label=ch.name, value=str(ch.id))
            for ch in guild.text_channels[:25]
        ]

        class ChannelSelect(discord.ui.View):

            @discord.ui.select(placeholder="Kies een kanaal", options=options)
            async def select_callback(self,
                                      select_interaction: discord.Interaction,
                                      select: discord.ui.Select):
                kanaal_id = int(select.values[0])
                kanaal = guild.get_channel(kanaal_id)
                if kanaal is None:
                    await select_interaction.response.edit_message(
                        content="Kanaal niet gevonden.", view=None)
                    return

                message = await kanaal.send(embed=embed)

                # raw_map normaliseren
                normalized_map = {}
                for emoji_text, role_part in raw_map.items():
                    role_id = None
                    if role_part.isdigit():
                        try:
                            role_id = int(role_part)
                            role_obj = guild.get_role(role_id)
                            if role_obj is None:
                                try:
                                    role_obj = await guild.fetch_role(role_id)
                                except:
                                    role_obj = None
                            if role_obj is None:
                                print(f"Rol-id niet gevonden in guild: {role_id}")
                                role_id = None
                        except:
                            role_id = None
                    else:
                        role_obj = discord.utils.get(guild.roles, name=role_part)
                        if role_obj:
                            role_id = role_obj.id
                        else:
                            print(f"Rolnaam niet gevonden: {role_part}")
                            role_id = None

                    try:
                        await message.add_reaction(emoji_text)
                        normalized_map[str(emoji_text)] = role_id
                    except Exception as e:
                        print(f"Kon emoji niet toevoegen ({emoji_text}): {e}")

                normalized_map = {k: v for k, v in normalized_map.items() if v is not None}

                bot.role_embed_data = getattr(bot, "role_embed_data", {})
                bot.role_embed_data[message.id] = normalized_map

                await select_interaction.response.edit_message(
                    content=f"✅ Role embed gestuurd naar {kanaal.mention}\nOpgeslagen mappings: {len(normalized_map)}",
                    view=None)

        await interaction.response.send_message(
            "Kies een kanaal voor je role embed:",
            view=ChannelSelect(),
            ephemeral=True)


@bot.tree.command(
    name="roleembed",
    description="Maak een role embed (alleen bepaalde rollen mogen dit)",
    guild=discord.Object(id=GUILD_ID))
async def roleembed(interaction: discord.Interaction):
    allowed_roles = {
        1402418713612910663,
        1403013958562218054,
        1342974632524775528,
        1405597740494356631,
        1402419665808134395
    }

    if not any(r.id in allowed_roles for r in interaction.user.roles):
        await interaction.response.send_message(
            "❌ Je hebt geen toegang tot dit commando.", ephemeral=True
        )
        return

    modal = RoleEmbedModal()
    await interaction.response.send_modal(modal)


# ------------------- Reactions → Roles -------------------
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    emoji_map = getattr(bot, "role_embed_data", {}).get(payload.message_id)
    if not emoji_map:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    member = guild.get_member(payload.user_id)
    if member is None:
        try:
            member = await guild.fetch_member(payload.user_id)
        except:
            return
    if member.bot:
        return

    key = str(payload.emoji)
    role_id = emoji_map.get(key)
    if role_id:
        role = guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role)
            except Exception as e:
                print(f"Kon rol niet toevoegen: {e}")


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    emoji_map = getattr(bot, "role_embed_data", {}).get(payload.message_id)
    if not emoji_map:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    member = guild.get_member(payload.user_id)
    if member is None:
        try:
            member = await guild.fetch_member(payload.user_id)
        except:
            return
    if member.bot:
        return

    key = str(payload.emoji)
    role_id = emoji_map.get(key)
    if role_id:
        role = guild.get_role(role_id)
        if role:
            try:
                await member.remove_roles(role)
            except Exception as e:
                print(f"Kon rol niet verwijderen: {e}")


# ------------------- Moderatie Modal -------------------
ALLOWED_ROLES = {1402418357596061756, 1402418713612910663, 1403013958562218054,
                 1342974632524775528, 1405597740494356631, 1402419665808134395}
LOG_CHANNELS = {
    "ban": 1405586824847556769,
    "kick": 1405586854442569749,
    "warn": 1406995238404231299,
    "timeout": 1405586885384081448
}

class ModeratieModal(Modal, title="Reden en opties"):
    reden = TextInput(label="Reden", style=discord.TextStyle.paragraph, placeholder="Geef een reden", required=True)
    duur = TextInput(label="Timeout in seconden (alleen bij timeout)", style=discord.TextStyle.short,
                     placeholder="Laat leeg indien niet van toepassing", required=False)

    def __init__(self, view_ref):
        super().__init__()
        self.view_ref = view_ref

    async def on_submit(self, interaction: discord.Interaction):
        view = self.view_ref
        view.reden = self.reden.value
        if view.actie == "timeout" and self.duur.value.isdigit():
            view.duur_sec = int(self.duur.value)
        else:
            view.duur_sec = None

        member: discord.Member = view.target_member
        actie = view.actie
        reden = view.reden

        try:
            if actie == "ban":
                await member.ban(reason=reden)
            elif actie == "kick":
                await member.kick(reason=reden)
            elif actie == "warn":
                # voeg hier je eigen warn systeem toe
                pass
            elif actie == "timeout":
                if view.duur_sec is None:
                    await interaction.response.send_message("❌ Geef een geldige duur voor timeout.", ephemeral=True)
                    return
                until_time = datetime.now(timezone.utc) + timedelta(seconds=view.duur_sec)
                await member.timeout(until=until_time, reason=reden)

            # Log
            log_channel_id = LOG_CHANNELS.get(actie)
            if log_channel_id:
                log_channel = interaction.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title=f"{actie.capitalize()} uitgevoerd",
                        description=f"**Gebruiker:** {member.mention}\n**Reden:** {reden}\n**Door:** {interaction.user.mention}",
                        color=discord.Color.red()
                    )
                    await log_channel.send(embed=embed)

            await interaction.response.send_message(f"✅ Actie {actie} uitgevoerd op {member.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Fout bij uitvoeren: {e}", ephemeral=True)


# ------------------- Moderatie View -------------------
class ModeratieView(View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=None)
        self.author = author
        self.target_member: discord.Member = None
        self.actie: str = None
        self.reden: str = None
        self.duur_sec: int = None

        # Knoppen
        for label, style, attr in [
            ("Ban", discord.ButtonStyle.danger, "ban"),
            ("Kick", discord.ButtonStyle.primary, "kick"),
            ("Warn", discord.ButtonStyle.secondary, "warn"),
            ("Timeout", discord.ButtonStyle.success, "timeout")
        ]:
            btn = Button(label=label, style=style)
            btn.callback = self.make_callback(attr)
            self.add_item(btn)

    # Dynamische callback voor elke actie
    def make_callback(self, actie):
        async def callback(interaction: discord.Interaction):
            if not any(r.id in ALLOWED_ROLES for r in interaction.user.roles):
                await interaction.response.send_message("❌ Je hebt geen toegang tot dit menu.", ephemeral=True)
                return

            if self.target_member is None:
                await interaction.response.send_message("❌ Kies eerst een gebruiker.", ephemeral=True)
                return

            self.actie = actie
            await interaction.response.send_modal(ModeratieModal(self))
        return callback

    # User select
    @UserSelect(placeholder="Kies een gebruiker", min_values=1, max_values=1)
    async def select_user(self, interaction: discord.Interaction, select: UserSelect):
        self.target_member = select.values[0]
        await interaction.response.send_message(f"✅ Gebruiker gekozen: {self.target_member.mention}", ephemeral=True)

# ------------------- Bot Ready -------------------
@bot.event
async def on_ready():
    print(f"✅ Bot ingelogd als {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"🌐 Slash commands gesynchroniseerd: {len(synced)}")
    except Exception as e:
        print(f"❌ Fout bij sync: {e}")
# ------------------- Start Bot -------------------
keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")  # gebruik "TOKEN" als env variable in Koyeb
if not TOKEN:
    print("❌ Geen Discord TOKEN gevonden in environment variables!")
else:
    bot.run(TOKEN)
