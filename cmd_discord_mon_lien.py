import discord
from discord.ext import commands

# ----------------------------
# CONFIGURATION
# ----------------------------
TOKEN = "MTQwOTE2NTY5MjE4NzcwNTQ2Ng.GYj3XF.MUD0h-oUF-ER-miWDT423hTLA1KkavDCnl2nrE"  # 🔑 Mets ici ton token sécurisé
LOG_CHANNEL_ID = 1409167403610407093  # ID du salon où stocker les infos

# ----------------------------
# INTENTS & BOT
# ----------------------------
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.invites = True
intents.message_content = True  # utile si plus tard tu veux lire les messages

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------------
# TRACKING DES INVITATIONS
# ----------------------------
# Format : { "user_id": {"invite": "url", "uses": nombre} }
tracking_data = {}


async def save_tracking_data(guild: discord.Guild):
    """
    Sauvegarde les infos dans le salon LOG_CHANNEL_ID avec un format clair.
    """
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    if log_channel is None:
        return

    # Efface les anciens messages (max 50 pour éviter le spam)
    await log_channel.purge(limit=50)

    if not tracking_data:
        await log_channel.send("📭 Aucune donnée enregistrée.")
        return

    description = "Voici la liste des liens d'invitations et leurs utilisations.\n\n"

    for user_id, data in tracking_data.items():
        member = guild.get_member(int(user_id))
        name = member.name if member else "Utilisateur inconnu"
        # Bloc d'info
        description += (
            f"👤 **{name}**  (ID : `{user_id}`)\n"
            f"Invité par : {name} (ID : `{user_id}`)\n"
            f"🔗 Lien : {data['invite']}\n"
            f"📈 Utilisations : **{data['uses']}**\n"
            f"--------------------------------------------\n\n"
        )

    embed = discord.Embed(
        title="📊 Suivi des Invitations",
        description=description,
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Système de suivi des invitations - Mis à jour automatiquement ✅")

    await log_channel.send(embed=embed)


# ----------------------------
# COMMANDE /monlien
# ----------------------------
@bot.tree.command(name="monlien", description="Génère ton lien d'invitation personnel au serveur.")
async def monlien(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    guild = interaction.guild

    if user_id not in tracking_data:
        # Crée un nouveau lien d’invitation
        invite = await guild.text_channels[0].create_invite(
            max_age=0,   # pas d'expiration
            max_uses=0,  # utilisations illimitées
            unique=True,
            reason=f"Invitation pour {interaction.user.name}"
        )
        tracking_data[user_id] = {"invite": invite.url, "uses": 0}

        # Sauvegarde dans le salon log
        await save_tracking_data(guild)

    await interaction.response.send_message(
        f"✅ Voici ton lien d'invitation unique au serveur :\n{tracking_data[user_id]['invite']}",
        ephemeral=True
    )


# ----------------------------
# COMMANDE /classement
# ----------------------------
@bot.tree.command(name="classement", description="Affiche le classement des meilleurs inviteurs.")
async def classement(interaction: discord.Interaction):
    if not tracking_data:
        await interaction.response.send_message("📭 Personne n’a encore invité quelqu’un.", ephemeral=True)
        return

    sorted_data = sorted(tracking_data.items(), key=lambda x: x[1]["uses"], reverse=True)

    embed = discord.Embed(
        title="🏆 Classement des meilleurs inviteurs",
        color=discord.Color.gold()
    )

    for i, (user_id, data) in enumerate(sorted_data[:10], start=1):
        member = interaction.guild.get_member(int(user_id))
        name = member.name if member else f"Utilisateur inconnu ({user_id})"
        embed.add_field(
            name=f"{i}. {name}",
            value=f"📈 **{data['uses']}** invitations",
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ----------------------------
# EVENT : Quand un membre rejoint
# ----------------------------
@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild
    invites = await guild.invites()

    for user_id, data in tracking_data.items():
        for inv in invites:
            if inv.url == data["invite"]:
                if inv.uses > data["uses"]:
                    tracking_data[user_id]["uses"] = inv.uses
                    await save_tracking_data(guild)
                break


# ----------------------------
# EVENT : Bot prêt
# ----------------------------
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔗 Slash commandes synchronisées ({len(synced)})")
    except Exception as e:
        print(f"Erreur sync : {e}")


# ----------------------------
# LANCEMENT DU BOT
# ----------------------------
bot.run(TOKEN)