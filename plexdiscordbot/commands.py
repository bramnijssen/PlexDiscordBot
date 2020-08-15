from discord.ext.commands import Cog, Bot, command, Context, check
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
        # Define page count
        tv_shows = db.get_all_tv_shows()
        page = 1
        total = len(tv_shows) // 10

        # If remainder exists, add one page
        if len(tv_shows) % 10 != 0:
            total += 1

        # Generate embed for message
        def gen_embed():
            desc = ""

            for i in range((page - 1) * 10, page * 10):
                title = tv_shows[i]["title"]
                slug = tv_shows[i]["slug"]

                desc += f"- [{title}](https://thetvdb.com/series/{slug})\n"

            return discord.Embed(
                colour=discord.Colour.from_rgb(229, 160, 13),
                title="TV Shows",
                description=desc
            ).set_footer(text=f"Page {page}/{total}")

        # Define arrow emoji
        left = "\U00002B05"
        right = "\U000027A1"

        # Add reactions to message
        async def add_reactions(message):
            await message.add_reaction(left)
            await message.add_reaction(right)

        # Send message and add reactions
        msg: discord.Message = await ctx.send(embed=gen_embed())
        await add_reactions(msg)

        timeout = 20
        from_dm = ctx.guild is None
        
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=timeout)

                # Check if message on which reaction was added is previously sent message AND if reacting user is
                # user who executed command
                if reaction.message.id == msg.id and user == ctx.author:
                    # If sent via DM, remove message and send new one
                    if from_dm:

                        if str(reaction.emoji) == left:
                            # If left reacted on first page, don't decrease page
                            if page != 1:
                                page -= 1

                            await msg.delete()
                            msg = await ctx.send(embed=gen_embed())
                            await add_reactions(msg)

                        elif str(reaction.emoji) == right:
                            # If right reacted on last page, don't increase page
                            if page != total:
                                page += 1

                            await msg.delete()
                            msg = await ctx.send(embed=gen_embed())
                            await add_reactions(msg)

                    # If sent on guild, remove reaction and edit message
                    else:

                        if str(reaction.emoji) == left:
                            # If left reacted on first page, just remove reaction
                            if page != 1:
                                page -= 1
                                await msg.edit(embed=gen_embed())

                        elif str(reaction.emoji) == right:
                            # If right reacted on last page, just remove reaction
                            if page != total:
                                page += 1
                                await msg.edit(embed=gen_embed())

            except asyncio.TimeoutError:
                embed = discord.Embed(
                    colour=discord.Colour.from_rgb(229, 160, 13),
                    title="TV Shows",
                    description=f"\U000023F0 **Timeout reached after {timeout} seconds**"
                )

                # When timeout reached, send timeout message and break
                if from_dm:
                    await msg.delete()
                    await ctx.send(embed=embed)

                else:
                    await msg.edit(embed=embed)
                    await msg.clear_reactions()

                break

            # If reaction on message in guild, remove reaction afterwards from all users except bot
            if reaction.message.guild is not None and reaction.message.id == msg.id and user != self.bot.user:
                await reaction.remove(user)
