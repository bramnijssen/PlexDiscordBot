from discord.ext.commands import Cog, Bot, command, Context
import database as db
import discord
import asyncio


def setup(bot):
    bot.add_cog(Commands(bot))


class Commands(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    # List all TV shows
    @command(name="tvshows")
    async def tv_shows(self, ctx: Context):
        # Return if via DM. Because of permissions for reaction removal
        if ctx.guild is None:
            await ctx.send("`.tvshows` can only be called on the server \U00002639")
            return

        # Floor divide number of pages
        tv_shows = await db.get_all_tv_shows()
        page = 1
        total = len(tv_shows) // 10

        # If remainder exists, add one page
        if len(tv_shows) % 10 != 0:
            total += 1

        # Embed message generation function
        def gen_embed():
            desc = ""

            for i in range((page - 1) * 10, page * 10):
                desc += f"- {tv_shows[i]['title']}\n"

            return discord.Embed(
                colour=discord.Colour.from_rgb(229, 160, 13),
                title="TV Shows",
                description=desc
            ).set_footer(text=f"Page {page}/{total}")

        msg: discord.Message = await ctx.send(embed=gen_embed())

        left = "\U00002B05"
        right = "\U000027A1"

        await msg.add_reaction(left)
        await msg.add_reaction(right)

        # Check if message on which reaction was added is previously sent message AND if reacting user is user who
        # executed command
        def check(reaction_check, user_check):
            return reaction_check.message.id == msg.id and user_check == ctx.author
        
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60)

                if str(reaction.emoji) == left:
                    # If left pressed on first page, just remove reaction
                    if page != 1:
                        page -= 1
                        await msg.edit(embed=gen_embed())
                    
                    await msg.remove_reaction(left, user)
                elif str(reaction.emoji) == right:
                    # If right pressed on last page, just remove reaction
                    if page != total:
                        page += 1
                        await msg.edit(embed=gen_embed())
                    
                    await msg.remove_reaction(right, user)

            except asyncio.TimeoutError:
                # When timeout reached, break
                break
