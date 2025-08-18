# Boot message
print("Booting up...")

import os
from datetime import datetime, timezone
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput, Select, UserSelect
from discord import SelectOption
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


# ------------------- Config -------------------
GUILD_ID = 1342974632524775526

# Moderation roles allowed for regular moderatie menu
ALLOWED_ROLES = {
    1402418357596061756,
    1402418713612910663,
    1403013958562218054,
    1342974632524775528,
    1405597740494356631,
    1402419665808134395
}

# Roles allowed to UNBAN (as you listed; includes the extra id you provided)
UNBAN_ROLES = {
    1402418357596061756,
    1402418713612910663,
    1403013958562218054,
    1342974632524775527,
    1342974632524775528,
    1405597740494356631,
    1402419665808134395
}

# Log channels
LOG_CHANNELS = {
    "ban": 1405586824847556769,
    "kick": 1405586854442569749,
    "warn": 1406995238404231299,
    # timeout removed per request
}

UNBAN_LOG_CHANNEL = 1405587917287587860  # provided unban log channel


# ------------------- Bot -------------------
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
bot.role_embed_data = {}  # opslag voor role embeds


# ------------------- Events -------------------
@bot.event
async def on_ready():
    print(f"✅ Bot ingelogd als {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"🌐 Slash commands gesynchroniseerd: {len(synced)}")
    except Exception as e:
        print(f"❌ Fout bij sync: {e}")


# ------------------- Embed Modal -------------------
class EmbedModal(Modal, title="Maak een Embed"):
    titel = TextInput(label="Titel", style=discord.TextStyle.short, placeholder="Bijv. Mededeling", required=True, max_length=100)
    beschrijving = TextInput(label="Beschrijving", style=discord.TextStyle.paragraph, placeholder="Tekst die in de embed verschijnt", required=True, max_length=2000)
    kleur = TextInput(label="Kleur (hex of none)", style=discord.TextStyle.short, placeholder="#2ecc71", required=False, max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        kleur_input = self.kleur.value or "#2ecc71"
        if kleur_input.lower() == "none":
            color = discord.Color.default()
        else:
            try:
                color = discord.Color(int(kleur_input.strip("#"), 16))
            except:
                color = discord.Color.default()

        embed = discord.Embed(title=self.titel.value, description=self.beschrijving.value, color=color)
        embed.set_footer(text=f"Gemaakt door {interaction.user}")

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Kon guild niet vinden.", ephemeral=True)
            return

        options = [SelectOption(label=ch.name, value=str(ch.id)) for ch in guild.text_channels[:25]]

        class ChannelSelect(View):
            @discord.ui.select(placeholder="Kies een kanaal", options=options)
            async def select_callback(self, select_interaction: discord.Interaction, select: Select):
                kanaal_id = int(select.values[0])
                kanaal = guild.get_channel(kanaal_id)
                if kanaal is None:
                    await select_interaction.response.edit_message(content="Kanaal niet gevonden.", view=None)
                    return
                await kanaal.send(embed=embed)
                await select_interaction.response.edit_message(content=f"✅ Embed gestuurd naar {kanaal.mention}", view=None)

        await interaction.response.send_message("Kies een kanaal voor je embed:", view=ChannelSelect(), ephemeral=True)


@bot.tree.command(name="embed", description="Maak een embed via formulier", guild=discord.Object(id=GUILD_ID))
async def embed_cmd(interaction: discord.Interaction):
    allowed_roles = {
        1402418713612910663,
        1403013958562218054,
        1342974632524775528,
        1405597740494356631,
        1402419665808134395
    }
    if not any(r.id in allowed_roles for r in interaction.user.roles):
        await interaction.response.send_message("❌ Je hebt geen toegang tot dit commando.", ephemeral=True)
        return
    await interaction.response.send_modal(EmbedModal())


# ------------------- Role Embed Modal -------------------
class RoleEmbedModal(Modal, title="Maak een Role Embed"):
    titel = TextInput(label="Titel", style=discord.TextStyle.short, placeholder="Bijv. Kies je rol", required=True, max_length=100)
    beschrijving = TextInput(label="Beschrijving (embed tekst)", style=discord.TextStyle.paragraph, placeholder="Tekst die in de role-embed verschijnt", required=True, max_length=4000)
    mapping = TextInput(label="Mapping (emoji:role_id of emoji:RoleName)", style=discord.TextStyle.short, placeholder="Bijv: ✅:1402417593419305060, 🎮:Gamer", required=True, max_length=200)
    thumbnail = TextInput(label="Thumbnail (URL of 'serverlogo')", style=discord.TextStyle.short, placeholder="https://example.com/thumb.png of 'serverlogo'", required=False, max_length=200)
    kleur = TextInput(label="Kleur (hex of none)", style=discord.TextStyle.short, placeholder="#2ecc71", required=False, max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        kleur_input = self.kleur.value or "#2ecc71"
        if kleur_input.lower() == "none":
            color = discord.Color.default()
        else:
            try:
                color = discord.Color(int(kleur_input.strip("#"), 16))
            except:
                color = discord.Color.default()

        embed = discord.Embed(title=self.titel.value, description=self.beschrijving.value, color=color)

        if self.thumbnail.value:
            if self.thumbnail.value.lower() == "serverlogo" and interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            else:
                embed.set_thumbnail(url=self.thumbnail.value)
        elif interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        if interaction.guild.icon:
            embed.set_footer(text=f"Gemaakt door {interaction.guild.name}", icon_url=interaction.guild.icon.url)
        else:
            embed.set_footer(text=f"Gemaakt door {interaction.guild.name}")

        raw_map = {}
        for part in self.mapping.value.split(","):
            if ":" in part:
                left, right = part.split(":", 1)
                emoji_text = left.strip()
                role_part = right.strip()
                if emoji_text and role_part:
                    raw_map[emoji_text] = role_part

        if not raw_map:
            await interaction.response.send_message("Geen geldige mapping gevonden. Gebruik format emoji:role_id of emoji:RoleName", ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Kon guild niet vinden.", ephemeral=True)
            return

        options = [SelectOption(label=ch.name, value=str(ch.id)) for ch in guild.text_channels[:25]]

        class ChannelSelect(View):
            @discord.ui.select(placeholder="Kies een kanaal", options=options)
            async def select_callback(self, select_interaction: discord.Interaction, select: Select):
                kanaal_id = int(select.values[0])
                kanaal = guild.get_channel(kanaal_id)
                if kanaal is None:
                    await select_interaction.response.edit_message(content="Kanaal niet gevonden.", view=None)
                    return

                message = await kanaal.send(embed=embed)

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

                await select_interaction.response.edit_message(content=f"✅ Role embed gestuurd naar {kanaal.mention}\nOpgeslagen mappings: {len(normalized_map)}", view=None)

        await interaction.response.send_message("Kies een kanaal voor je role embed:", view=ChannelSelect(), ephemeral=True)


@bot.tree.command(name="roleembed", description="Maak een role embed (alleen bepaalde rollen mogen dit)", guild=discord.Object(id=GUILD_ID))
async def roleembed(interaction: discord.Interaction):
    allowed_roles = {
        1402418713612910663,
        1403013958562218054,
        1342974632524775528,
        1405597740494356631,
        1402419665808134395
    }
    if not any(r.id in allowed_roles for r in interaction.user.roles):
        await interaction.response.send_message("❌ Je hebt geen toegang tot dit commando.", ephemeral=True)
        return
    await interaction.response.send_modal(RoleEmbedModal())


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


#------------------- Moderatie UI (timeout removed) -------------------
class ModeratieModal(Modal, title="Reden"):
    reden = TextInput(label="Reden", style=discord.TextStyle.paragraph, placeholder="Geef een reden", required=True)

    def __init__(self, view_ref):
        super().__init__()
        self.view_ref = view_ref

    async def on_submit(self, interaction: discord.Interaction):
        view = self.view_ref
        view.reden = self.reden.value

        member: discord.Member = view.target_member
        actie = view.actie
        reden = view.reden

        try:
            if actie == "ban":
                await member.ban(reason=reden)
            elif actie == "kick":
                await member.kick(reason=reden)
            elif actie == "warn":
                # simple warn: log only (persistent warns can be added later)
                pass
            else:
                await interaction.response.send_message("❌ Ongeldige actie.", ephemeral=True)
                return

            # Logging to mapping channels
            log_channel_id = LOG_CHANNELS.get(actie)
            if log_channel_id and interaction.guild:
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


class ModeratieView(View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=None)
        self.author = author
        self.target_member: discord.Member = None
        self.actie: str = None
        self.reden: str = None

        # programmatic UserSelect (compatible cross-version)
        user_select = discord.ui.UserSelect(placeholder="Kies een gebruiker", min_values=1, max_values=1)
        user_select.callback = self._user_selected
        self.add_item(user_select)

        # Buttons: Ban / Kick / Warn (timeout removed)
        for label, style, attr in [
            ("Ban", discord.ButtonStyle.danger, "ban"),
            ("Kick", discord.ButtonStyle.primary, "kick"),
            ("Warn", discord.ButtonStyle.secondary, "warn")
        ]:
            btn = Button(label=label, style=style)
            btn.callback = self.make_callback(attr)
            self.add_item(btn)

    async def _user_selected(self, interaction: discord.Interaction):
        try:
            sel_vals = interaction.data.get("values", [])
            if sel_vals:
                selected_id = int(sel_vals[0])
                selected = interaction.guild.get_member(selected_id) or await interaction.guild.fetch_member(selected_id)
            else:
                selected = None
        except:
            selected = None

        if selected is None:
            await interaction.response.send_message("❌ Kon geselecteerde gebruiker niet vinden.", ephemeral=True)
            return

        self.target_member = selected
        await interaction.response.send_message(f"✅ Gebruiker gekozen: {self.target_member.mention}", ephemeral=True)

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


# ------------------- Moderatie command -------------------
@bot.tree.command(name="moderatie", description="Open het moderatie UI menu", guild=discord.Object(id=GUILD_ID))
async def moderatie(interaction: discord.Interaction):
    if not any(r.id in ALLOWED_ROLES for r in interaction.user.roles):
        await interaction.response.send_message("❌ Je hebt geen toegang.", ephemeral=True)
        return
    await interaction.response.send_message("Moderatie menu:", view=ModeratieView(interaction.user), ephemeral=True)


# ------------------- UNBAN command (by ID) -------------------
@bot.tree.command(name="unban", description="Unban een gebruiker via ID (loggingsysteem)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user_id="Discord user ID om te unbannen", reason="Reden (optioneel)")
async def unban(interaction: discord.Interaction, user_id: str, reason: str = "Geen reden opgegeven"):
    # permissions
    if not any(r.id in UNBAN_ROLES for r in interaction.user.roles):
        await interaction.response.send_message("❌ Je hebt geen toestemming om unbans uit te voeren.", ephemeral=True)
        return

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("❌ Guild niet gevonden.", ephemeral=True)
        return

    # parse id
    try:
        uid = int(user_id.strip())
    except:
        await interaction.response.send_message("❌ Ongeldige user ID.", ephemeral=True)
        return

    try:
        bans = await guild.bans()
    except Exception as e:
        await interaction.response.send_message(f"❌ Kon bans lijst niet ophalen: {e}", ephemeral=True)
        return

    target_ban = None
    for ban_entry in bans:
        if ban_entry.user.id == uid:
            target_ban = ban_entry
            break

    if target_ban is None:
        await interaction.response.send_message("❌ Deze gebruiker is niet geband (of ID niet gevonden).", ephemeral=True)
        return

    try:
        await guild.unban(target_ban.user, reason=reason)
    except Exception as e:
        await interaction.response.send_message(f"❌ Unban faalde: {e}", ephemeral=True)
        return

    # Log naar unban-kanaal
    log_channel = guild.get_channel(UNBAN_LOG_CHANNEL)
    if log_channel:
        embed = discord.Embed(
            title="Unban uitgevoerd",
            description=f"**Gebruiker:** {target_ban.user} (`{target_ban.user.id}`)\n**Door:** {interaction.user.mention}\n**Reden:** {reason}",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        await log_channel.send(embed=embed)

    await interaction.response.send_message(f"✅ Unbanned: {target_ban.user} (`{target_ban.user.id}`)", ephemeral=True)


# ------------------- Start Bot -------------------
keep_alive()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ Geen Discord TOKEN gevonden in environment variables!")
else:
    bot.run(TOKEN)
