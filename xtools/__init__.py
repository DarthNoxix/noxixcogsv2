from .xtools import XTools
___red_end_user_data_statement__ = (
    "This cog does not persistently store data about users."
)


def setup(bot):
    cog = XTools(bot)
    bot.add_cog(cog)
