import asyncio
from typing import Union

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box
from dislash import ButtonStyle, Button, ActionRow


class ApplicationsCommands(commands.Cog):
    @commands.group(name="applicationset", aliases=["sset"])
    @commands.guild_only()
    @commands.admin()
    async def applications(self, ctx: commands.Context):
        """Base applications settings"""
        pass

    # Check running button tasks and update guild task if exists
    async def refresh_tasks(self, guild_id: str):
        for task in asyncio.all_tasks():
            if guild_id == task.get_name():
                task.cancel()
                await self.add_components()

    @applications.command(name="view")
    async def view_settings(self, ctx: commands.Context):
        """View applications settings"""
        conf = await self.config.guild(ctx.guild).all()
        category = self.bot.get_channel(conf["category"])
        if not category:
            category = conf['category']
        button_channel = self.bot.get_channel(conf['channel_id'])
        if button_channel:
            button_channel = button_channel.mention
        else:
            button_channel = conf['channel_id']
        msg = f"`Application Category:  `{category}\n" \
              f"`Button MessageID: `{conf['message_id']}\n" \
              f"`Button Channel:   `{button_channel}\n" \
              f"`Max Applications:      `{conf['max_applications']}\n" \
              f"`Button Content:   `{conf['button_content']}\n" \
              f"`Button Emoji:     `{conf['emoji']}\n" \
              f"`DM Alerts:        `{conf['dm']}\n" \
              f"`Users can Rename: `{conf['user_can_rename']}\n" \
              f"`Users can Close:  `{conf['user_can_close']}\n" \
              f"`Users can Manage: `{conf['user_can_manage']}\n" \
              f"`Save Transcripts: `{conf['transcript']}\n" \
              f"`Auto Close:       `{conf['auto_close']}\n" \
              f"`Application Name:      `{conf['application_name']}\n"
        log = conf["log"]
        if log:
            lchannel = ctx.guild.get_channel(log)
            if lchannel:
                msg += f"`Log Channel:      `{lchannel.mention}\n"
            else:
                msg += f"`Log Channel:      `{log}\n"
        applications = conf["applications"]
        suproles = ""
        if applications:
            for role_id in applications:
                role = ctx.guild.get_role(role_id)
                if role:
                    suproles += f"{role.mention}\n"
        blacklist = conf["blacklist"]
        busers = ""
        if blacklist:
            for user_id in blacklist:
                user = ctx.guild.get_member(user_id)
                if user:
                    busers += f"{user.name}-{user.id}\n"
                else:
                    busers += f"LeftGuild-{user_id}\n"
        embed = discord.Embed(
            title="Applications Settings",
            description=msg,
            color=discord.Color.random()
        )
        if suproles:
            embed.add_field(
                name="Applications Roles",
                value=suproles,
                inline=False
            )
        if busers:
            embed.add_field(
                name="Blacklisted Users",
                value=busers,
                inline=False
            )
        if conf["message"] != "{default}":
            embed.add_field(
                name="Application Message",
                value=box(conf["message"]),
                inline=False
            )
        await ctx.send(embed=embed)

    @applications.command(name="category")
    async def category(self, ctx: commands.Context, category: discord.CategoryChannel):
        """Set the category application channels will be created in"""
        if not category.permissions_for(ctx.guild.me).manage_channels:
            return await ctx.send(
                "I do not have 'Manage Channels' permissions in that category"
            )
        await self.config.guild(ctx.guild).category.set(category.id)
        await ctx.send(f"Applications will now be created in the {category.name} category")

    @applications.command(name="applicationsmessage")
    async def set_applications_button_message(self, ctx: commands.Context, message_id: discord.Message):
        """
        Set the applications application message

        The applications button will be added to this message
        """
        if not message_id.channel.permissions_for(ctx.guild.me).view_channel:
            return await ctx.send("I cant see that channel")
        if not message_id.channel.permissions_for(ctx.guild.me).read_messages:
            return await ctx.send("I cant read messages in that channel")
        if not message_id.channel.permissions_for(ctx.guild.me).read_message_history:
            return await ctx.send("I cant read message history in that channel")
        if message_id.author.id != self.bot.user.id:
            return await ctx.send("I can only add buttons to my own messages!")
        await self.config.guild(ctx.guild).message_id.set(message_id.id)
        await self.config.guild(ctx.guild).channel_id.set(message_id.channel.id)
        await ctx.send("Applications application message has been set!")
        await self.refresh_tasks(str(ctx.guild.id))

    @applications.command(name="applicationmessage")
    async def set_applications_application_message(self, ctx: commands.Context, *, message: str):
        """
        Set the message sent when a application is opened

        You can include any of these in the message to be replaced by their value when the message is sent
        `{username}` - Person's Discord username
        `{mention}` - This will mention the user
        `{id}` - This is the ID of the user that created the application

        You can set this to {default} to restore original settings
        """
        if len(message) > 1024:
            return await ctx.send("Message length is too long! Must be less than 1024 chars")
        await self.config.guild(ctx.guild).message.set(message)
        if message.lower() == "default":
            await ctx.send("Message has been reset to default")
        else:
            await ctx.send("Message has been set!")

    @applications.command(name="applicationsrole")
    async def set_applications_role(self, ctx: commands.Context, *, role: discord.Role):
        """
        Add/Remove application applications roles (one at a time)

        To remove a role, simply run this command with it again to remove it
        """
        async with self.config.guild(ctx.guild).applications() as roles:
            if role.id in roles:
                roles.remove(role.id)
                await ctx.send(f"{role.name} has been removed from applications roles")
            else:
                roles.append(role.id)
                await ctx.send(f"{role.name} has been added to applications roles")

    @applications.command(name="blacklist")
    async def set_user_blacklist(self, ctx: commands.Context, *, user: discord.Member):
        """
        Add/Remove users from the blacklist

        Users in the blacklist will not be able to create a application
        """
        async with self.config.guild(ctx.guild).blacklist() as bl:
            if user.id in bl:
                bl.remove(user.id)
                await ctx.send(f"{user.name} has been removed from the blacklist")
            else:
                bl.append(user.id)
                await ctx.send(f"{user.name} has been added to the blacklist")

    @applications.command(name="maxapplications")
    async def set_max_applications(self, ctx: commands.Context, max_applications: int):
        """Set the max amount of applications a user can have opened"""
        await self.config.guild(ctx.guild).max_applications.set(max_applications)
        await ctx.tick()

    @applications.command(name="logchannel")
    async def set_log_channel(self, ctx: commands.Context, *, log_channel: discord.TextChannel):
        """Set the log channel"""
        await self.config.guild(ctx.guild).log.set(log_channel.id)
        await ctx.tick()

    @applications.command(name="buttoncontent")
    async def set_button_content(self, ctx: commands.Context, *, button_content: str):
        """Set what you want the applications button to say"""
        if len(button_content) <= 80:
            await self.config.guild(ctx.guild).button_content.set(button_content)
            await ctx.tick()
            await self.refresh_tasks(str(ctx.guild.id))
        else:
            await ctx.send("Button content is too long! Must be less than 80 characters")

    @applications.command(name="buttoncolor")
    async def set_button_color(self, ctx: commands.Context, button_color: str):
        """Set button color(red/blue/green/grey only)"""
        c = button_color.lower()
        valid = ["red", "blue", "green", "grey", "gray"]
        if c not in valid:
            return await ctx.send("That is not a valid color, must be red, blue, green, or grey")
        await self.config.guild(ctx.guild).bcolor.set(c)
        await ctx.tick()
        await self.refresh_tasks(str(ctx.guild.id))

    @applications.command(name="buttonemoji")
    async def set_button_emoji(self, ctx: commands.Context, emoji: Union[discord.Emoji, discord.PartialEmoji, str]):
        """
        Set a button emoji

        Currently does NOT applications unicode emojis so if using a mobile device, use discord emoji panel
        """
        conf = await self.config.guild(ctx.guild).all()
        bcolor = conf["bcolor"]
        if bcolor == "red":
            style = ButtonStyle.red
        elif bcolor == "blue":
            style = ButtonStyle.blurple
        elif bcolor == "green":
            style = ButtonStyle.green
        else:
            style = ButtonStyle.grey
        button_content = conf["button_content"]
        button = ActionRow(
            Button(
                style=style,
                label=button_content,
                custom_id=f"{ctx.guild.id}",
                emoji=str(emoji)
            )
        )
        try:
            await ctx.send("This is what your button now looks like!", components=[button])
        except Exception as e:
            if "Invalid emoji" in str(e):
                return await ctx.send("Unable to use that emoji, try again")
            else:
                return await ctx.send(f"Cant use that emoji for some reason\nError: {e}")
        await self.config.guild(ctx.guild).emoji.set(str(emoji))
        await ctx.tick()
        await self.refresh_tasks(str(ctx.guild.id))

    @applications.command(name="tname")
    async def set_def_application_name(self, ctx: commands.Context, *, default_name: str):
        """
        Set the default application channel name

        You can include the following in the name
        `{num}` - Application number
        `{user}` - user's name
        `{id}` - user's ID
        `{shortdate}` - mm-dd
        `{longdate}` - mm-dd-yyyy
        `{time}` - hh-mm AM/PM according to bot host system time

        You can set this to {default} to use default "Application-Username
        """
        await self.config.guild(ctx.guild).application_name.set(default_name)
        await ctx.tick()

    # TOGGLES --------------------------------------------------------------------------------
    @applications.command(name="applicationembed")
    async def toggle_application_embed(self, ctx: commands.Context):
        """
        (Toggle) Application message as an embed

        When user opens a application, the formatted message will be an embed instead
        """
        toggle = await self.config.guild(ctx.guild).embeds()
        if toggle:
            await self.config.guild(ctx.guild).embeds.set(False)
            await ctx.send("Application message embeds have been **Disabled**")
        else:
            await self.config.guild(ctx.guild).embeds.set(True)
            await ctx.send("Application message embeds have been **Enabled**")

    @applications.command(name="dm")
    async def toggle_dms(self, ctx: commands.Context):
        """(Toggle) The bot sending DM's for application alerts"""
        toggle = await self.config.guild(ctx.guild).dm()
        if toggle:
            await self.config.guild(ctx.guild).dm.set(False)
            await ctx.send("DM alerts have been **Disabled**")
        else:
            await self.config.guild(ctx.guild).dm.set(True)
            await ctx.send("DM alerts have been **Enabled**")

    @applications.command(name="selfrename")
    async def toggle_rename(self, ctx: commands.Context):
        """(Toggle) If users can rename their own applications"""
        toggle = await self.config.guild(ctx.guild).user_can_rename()
        if toggle:
            await self.config.guild(ctx.guild).user_can_rename.set(False)
            await ctx.send("User can no longer rename their applications channel")
        else:
            await self.config.guild(ctx.guild).user_can_rename.set(True)
            await ctx.send("User can now rename their applications channel")

    @applications.command(name="selfclose")
    async def toggle_selfclose(self, ctx: commands.Context):
        """(Toggle) If users can close their own applications"""
        toggle = await self.config.guild(ctx.guild).user_can_close()
        if toggle:
            await self.config.guild(ctx.guild).user_can_close.set(False)
            await ctx.send("User can no longer close their applications channel")
        else:
            await self.config.guild(ctx.guild).user_can_close.set(True)
            await ctx.send("User can now close their applications channel")

    @applications.command(name="selfmanage")
    async def toggle_selfmanage(self, ctx: commands.Context):
        """
        (Toggle) If users can manage their own applications

        Users will be able to add/remove others to their applications application
        """
        toggle = await self.config.guild(ctx.guild).user_can_manage()
        if toggle:
            await self.config.guild(ctx.guild).user_can_manage.set(False)
            await ctx.send("User can no longer manage their applications channel")
        else:
            await self.config.guild(ctx.guild).user_can_manage.set(True)
            await ctx.send("User can now manage their applications channel")

    @applications.command(name="autoclose")
    async def toggle_autoclose(self, ctx: commands.Context):
        """(Toggle) Auto application close if user leaves guild"""
        toggle = await self.config.guild(ctx.guild).auto_close()
        if toggle:
            await self.config.guild(ctx.guild).auto_close.set(False)
            await ctx.send("Applications will no longer be closed if a user leaves the guild")
        else:
            await self.config.guild(ctx.guild).auto_close.set(True)
            await ctx.send("Applications will now be closed if a user leaves the guild")

    @applications.command(name="transcript")
    async def toggle_transcript(self, ctx: commands.Context):
        """
        (Toggle) Application transcripts

        Closed applications will have their transcripts uploaded to the log channel
        """
        toggle = await self.config.guild(ctx.guild).transcript()
        if toggle:
            await self.config.guild(ctx.guild).transcript.set(False)
            await ctx.send("Transcripts of closed applications will no longer be saved")
        else:
            await self.config.guild(ctx.guild).transcript.set(True)
            await ctx.send("Transcripts of closed applications will now be saved")
