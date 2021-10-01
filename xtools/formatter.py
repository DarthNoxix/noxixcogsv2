import discord
import datetime

from redbot.core.utils.chat_formatting import box


# Check if an object is None
def check(data):
    if data:
        return data
    return "Can't fetch data"


# Time Converter
def time_format(time):
    minutes, _ = divmod(time, 60)
    hours, minutes = divmod(minutes, 60)
    return hours, minutes


# Microsoft's timestamp end digits are fucked up and random so we iteratively try fixing them by stripping digits
def fix_timestamp(time):
    try:
        time = datetime.datetime.fromisoformat(time)
    except ValueError:
        stripping_that_shit = True
        strip = -1
        while stripping_that_shit:
            try:
                time = datetime.datetime.fromisoformat(time[:strip])
                stripping_that_shit = False
            except ValueError:
                strip -= 1
                if strip < -10:
                    stripping_that_shit = False  # idfk then
    return time


# Format profile data
def profile(data):
    # Main profile data
    gt, bio, location, gs, pfp, tenure, tier, rep = None, None, None, None, None, None, None, None
    user = data["profile_users"][0]
    xuid = user['id']
    for setting in user["settings"]:
        if setting["id"] == "Gamertag":
            gt = setting["value"]
        if setting["id"] == "Bio":
            bio = setting['value']
        if setting["id"] == "Location":
            location = setting['value']
        if setting["id"] == "Gamerscore":
            gs = "{:,}".format(int(setting['value']))
        if setting["id"] == "GameDisplayPicRaw":
            pfp = setting['value']
        if setting["id"] == "TenureLevel":
            tenure = setting['value']
        if setting["id"] == "AccountTier":
            tier = setting['value']
        if setting["id"] == "XboxOneRep":
            rep = setting['value']
    return gt, xuid, bio, location, gs, pfp, tenure, tier, rep


# Format profile embed
def profile_embed(data):
    gt, xuid, bio, location, gs, pfp, tenure, tier, rep = profile(data)
    state = data["presence"]["state"]
    if state == "Online":
        color = discord.Color.green()
    else:
        color = discord.Color.dark_grey()
    title = f"{gt}'s Profile ({state})"
    embed = discord.Embed(
        title=title,
        color=color,
        description="Any field saying `Can't fetch data` is due to account privacy settings, you can manage that "
                    "**[here](https://account.xbox.com/en-gb/Settings)**"
    )
    following = data["friends"]["target_following_count"]
    followers = data["friends"]["target_follower_count"]
    account_info = f"Gamerscore: `{gs}`\n" \
                   f"Followers: `{followers}`\n" \
                   f"Following: `{following}`\n" \
                   f"AccountTier: `{tier}`\n" \
                   f"Player Rep: `{rep}`\n" \
                   f"Location: `{check(location)}`\n" \
                   f"Member For: `{tenure} years`\n" \
                   f"XUID: `{xuid}`"
    embed.set_thumbnail(url=pfp)
    embed.add_field(name="Account Info", value=account_info)

    presence = data["presence"]

    # Rename devices according to their code name
    def device_check(device):
        if device == "Durango":
            device = "1st Gen XboxOne"
        if device == "Scarlett":
            device = "Xbox Series S"
        if device == "WindowsOneCore":
            device = "Windows"
        return device

    # Format field depending if user is offline or not
    current_time = datetime.datetime.utcnow()
    if "lastSeen" in presence:
        game = presence["lastSeen"]["titleName"]
        device = presence["lastSeen"]["deviceType"]
        device = device_check(device)
        time = fix_timestamp(presence["lastSeen"]["timestamp"])
        tdiff = current_time - time
        h, m = time_format(tdiff.seconds)
        if tdiff.days >= 1:
            lseen = f"{tdiff.days}d ago on {device}:\n{game}"
        elif h < 1:
            lseen = f"{m}m ago on {device}:\n{game}"
        else:
            lseen = f"{h}h {m}m ago on {device}:\n{game}"
        embed.add_field(name="Last Seen", value=lseen)
    if "devices" in presence:
        device = presence["devices"][0]["type"]
        device = device_check(device)
        gamelist = ""
        for game in presence["devices"][0]["titles"]:
            gamelist += f"{game['name']}\n"
        embed.add_field(name="Active Now", value=f"{gamelist}on {device}")

    # Format activity field
    activitylist = ""
    for activity in data["activity"]:
        desc = activity["description"]
        desc = desc[:1].upper() + desc[1:]
        time = fix_timestamp(activity["date"])
        diff = current_time - time
        h, m = time_format(diff.seconds)
        if diff.days >= 30:
            months, _ = divmod(diff.days, 30)
            if months == 1:
                event = f"{months} month ago"
            else:
                event = f"{months} months ago"
        elif 30 > diff.days > 1:
            event = f"{diff.days} days ago"
        elif h < 1:
            event = f"{m} minutes ago"
        else:
            event = f"{h}h {m}m ago"
        activitylist += f"{desc} - {event}\n"
    embed.add_field(name="Recent Activity", value=activitylist, inline=False)

    if bio != "":
        embed.add_field(name="Bio", value=box(bio), inline=False)
    return embed


# Format screnshot json for sending to the menu
def screenshot_embeds(data, gamertag):
    pages = []
    length = len(data["screenshots"])
    cur_page = 1
    for pic in data["screenshots"]:
        game = pic["title_name"]
        name = pic["screenshot_name"]
        caption = pic["user_caption"]
        views = pic["views"]
        ss = pic["screenshot_uris"][0]["uri"]
        ss = ss.split("?")[0]
        timestamp = (datetime.datetime.fromisoformat(pic["date_taken"])).strftime("%m/%d/%Y, %H:%M:%S")
        embed = discord.Embed(
            title=f"{gamertag}'s Screenshots",
            color=discord.Color.random(),
            description=f"If a field says `Can't fetch data` it is because there is nothing entered for it "
        )
        embed.set_image(url=ss)
        embed.add_field(name="Info",
                        value=f"Game: `{check(game)}`\n"
                        f"Screenshot Name: `{check(name)}`\n"
                        f"Views: `{check(views)}`\n"
                        f"Taken on: `{check(timestamp)}`\n"
                        f"Caption: `{check(caption)}`\n")
        embed.set_footer(text=f"Pages: {cur_page}/{length}")
        cur_page += 1
        pages.append(embed)
    return pages


# Format game info
def game_embeds(gamertag, gamename, title_pic, gs, achievement_data, minutes_played):
    embeds = []
    achievements = achievement_data["achievements"]
    count = 1
    for ach in achievements:
        name = ach["name"]
        status = ach["progress_state"]
        desc = ach["locked_description"]
        icon = ach["media_assets"][0]["url"]
        worth = ach["rewards"][0]["value"]
        if status == "Achieved":
            timestamp = ach["progression"]["time_unlocked"]
            time = fix_timestamp(timestamp)
            time = time.strftime("%m/%d/%Y, %H:%M:%S")
            desc = ach["description"]
            info = f"{name}" \
                   f"Status: Unlocked on {time}\n" \
                   f"{desc}\n" \
                   f"{worth} Gamerscore"
        else:
            info = f"{name}" \
                   f"Status: {status}\n" \
                   f"{desc}\n" \
                   f"{worth} Gamerscore"

        embed = discord.Embed(
            description=f"**{gamertag}'s Achievements for {gamename}**\n{gs} Gamerscore"
        )
        embed.add_field(name="Achievement Info", value=info)
        embed.set_thumbnail(url=title_pic)
        embed.set_image(url=icon)
        hours, minutes = divmod(minutes_played, 60)
        days, hours = divmod(hours, 24)
        embed.set_footer(text=f"Page {count}/{len(achievements)} | Total time played: {days}d {hours}h {minutes}m")
        embeds.append(embed)
        count += 1
    return embeds


# Format friend list
def friend_embeds(friend_data, main_gamertag):
    embeds = []
    count = 1
    friends = friend_data["people"]
    for friend in friends:
        xuid = friend["xuid"]
        followed_by = friend["is_following_caller"]
        name = friend["gamertag"]
        pfp = friend["display_pic_raw"]
        gs = friend["gamer_score"]
        rep = friend["xbox_one_rep"]
        tier = friend["detail"]["account_tier"]
        state = friend["presence_state"]
        account_info = f"Gamerscore: `{gs}`\n" \
                       f"AccountTier: `{tier}`\n" \
                       f"Player Rep: `{rep}`\n" \
                       f"XUID: `{xuid}`\n" \
                       f"Is Following {main_gamertag}: `{followed_by}`"

        game = None
        color = discord.Color.random()
        if state == "Online":
            color = discord.Color.green()
            game = friend["presence_text"]

        session = friend["multiplayer_summary"]["in_multiplayer_session"]
        party = friend["multiplayer_summary"]["in_party"]

        bio = friend["detail"]["bio"]

        embed = discord.Embed(
            color=color,
            description=f"**{main_gamertag}'s Friends**"
        )
        embed.set_thumbnail(url=pfp)
        embed.add_field(name=f"{name} ({state})", value=account_info, inline=False)
        if state == "Online":
            embed.add_field(name="Playing", value=game)
        if int(session) > 0 or int(party) > 0:
            embed.add_field(name="Session Info", value=f"Game Session: {session} players\nParty Chat: {party}")
        if bio != "":
            embed.add_field(name="Bio", value=box(bio), inline=False)
        embed.set_footer(text=f"Page {count}/{len(friends)}")
        count += 1
        embeds.append(embed)
    return embeds


def gameclip_embeds(clip_data, gamertag):
    embeds = []
    count = 1
    clips = clip_data["game_clips"]
    for clip in clips:
        state = clip["state"]
        recorded_on = fix_timestamp(clip["date_recorded"]).strftime("%m/%d/%Y, %H:%M:%S")
        published = False
        if state == "Published":
            published = True
        duration = int(clip["duration_in_seconds"])
        m, s = divmod(duration, 60)
        views = clip["views"]
        title = clip["clip_name"]
        if title == "":
            title = "Untitled"
        thumbnail = clip["thumbnails"][0]["uri"]
        clip_uri = clip["game_clip_uris"][0]["uri"]
        game = clip["title_name"]
        embed = discord.Embed(
            description=f"**{gamertag}'s Game Clips**",
            color=discord.Color.random()
        )
        embed.set_image(url=thumbnail)
        clip_info = f"Title: `{title}`\n" \
                    f"Game: `{game}`\n" \
                    f"Duration: `{m}m {s}s`\n" \
                    f"Views: `{views}`\n" \
                    f"State: `{state}`\n" \
                    f"Recorded on: `{recorded_on}`\n"
        if published:
            published_on = fix_timestamp(clip["date_published"]).strftime("%m/%d/%Y, %H:%M:%S")
            clip_info += f"Published on `{published_on}`\n"
        clip_info += f"**[Click Here To Watch]({clip_uri})**"
        embed.add_field(name="Clip Info", value=clip_info)
        embed.set_footer(text=f"Pages {count}/{len(clips)}")
        count += 1
        embeds.append(embed)
    return embeds


# Format microsoft service data
def status(data):
    overall_status = data["ServiceStatus"]["Status"]["Overall"]["State"]
    overall_id = data["ServiceStatus"]["Status"]["Overall"]["Id"]
    last_updated = data["ServiceStatus"]["Status"]["Overall"]["LastUpdated"]
    last_updated = fix_timestamp(last_updated).strftime("%m/%d/%Y, %H:%M:%S")
    if overall_status == "Impacted":
        embed = discord.Embed(
            title="⚠ Microsoft Status Alert ⚠",
            color=discord.Color.orange(),
            description="Microsoft is experiencing technical problems with the following services:"
        )
        embed.set_footer(text=f"Last Updated: {last_updated}")
        for service in data["ServiceStatus"]["CoreServices"]["Category"]:
            service_status = service["Status"]["Name"]
            if service_status == "Impacted":
                service_id = service["Id"]
                service_name = service["Name"]
                status_id = service["Status"]["Id"]
                actions = ''
                for scenario in service["Scenarios"]["Scenario"]:
                    if scenario["Status"]["Name"] == "Impacted":
                        scenario_id = scenario["Status"]["Id"]
                        action = scenario["Name"]
                        timestamp = scenario["Incidents"]["Incident"]["Begin"]
                        timestamp = fix_timestamp(timestamp).strftime("%m/%d/%Y, %H:%M:%S")
                        message = scenario["Incidents"]["Incident"]["Stage"]["Message"]
                        level_of_impact = scenario["Incidents"]["Incident"]["LevelOfImpact"]["Name"]
                        actions += f"`{action}`-`{timestamp}`-`{level_of_impact} impact`\n"
                embed.add_field(name=f"{service_name}",
                                value=actions,
                                inline=False)
        for title in data["ServiceStatus"]["Titles"]["Category"]:
            title_name = title["Name"]
            status = title["Status"]["Name"]
            if status == "Impacted":
                actions = ''
                for scenario in title["Scenarios"]["Scenario"]:
                    if scenario["Status"]["Name"] == "Impacted":
                        scenario_name = scenario["Name"]
                        level_of_impact = scenario["Incidents"]["Incident"]["LevelOfImpact"]["Name"]
                        timestamp = scenario["Incidents"]["Incident"]["Begin"]
                        timestamp = fix_timestamp(timestamp).strftime("%m/%d/%Y, %H:%M:%S")
                        actions += f"`{scenario_name}`-`{timestamp}`-`{level_of_impact} impact`\n"
                embed.add_field(name=f"{title_name}",
                                value=actions,
                                inline=False)
    else:
        color = discord.Color.green()
        embed = discord.Embed(description="✅ All Microsoft services are up and running!", color=color)
    return embed






