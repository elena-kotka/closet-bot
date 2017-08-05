# -*- coding: utf-8 -*-

import logging
from database import connect, scoped_session, get_session
import inspect
import asyncio
import os
import discord
from discord.ext.commands.view import StringView
from discord.ext.commands.context import Context
from discord.ext.commands.errors import CommandNotFound, CommandError
from discord.ext.commands import Bot, Command, command
import models

logger = logging.getLogger(__name__)


class ClosetBot(Bot):
    def __init__(self, db_uri=None, command_prefix='!', *args, **kwargs):
        super(ClosetBot, self).__init__(command_prefix, *args, **kwargs)
        self.db = connect(db_uri)
        self.register_commands()
        self.add_check(self.check_user)

    def register_commands(self):
        members = inspect.getmembers(self)
        for name, member in members:
            if isinstance(member, Command):
                if member.parent is None:
                    self.add_command(member)
                continue

    def run(self):
        super(ClosetBot, self).run(os.environ.get('CLOSET_BOT_DISCORD_TOKEN', None))

    def check_user(self, ctx):
        session = get_session(self.db)
        patron = session.query(models.Patron).filter_by(id=ctx.message.author.id).first()
        if not patron:
            patron = self.add_patron(ctx.message.author, session)
        ctx.patron = patron
        ctx.session = session
        return bool(session)

    @staticmethod
    def add_patron(member, session):
        identity = ClosetBot.add_identity(member, session)

        patron = models.Patron(
            id=member.id,
            identity_name=identity.name
        )
        session.add(patron)
        return patron

    @staticmethod
    def add_identity(member, session):
        identity = models.Identity(
            name=member.name,
            display_name=member.display_name,
            avatar=member.avatar_url
        )
        session.add(identity)

        suit = models.Suit(
            identity_name=identity.name
        )
        session.add(suit)
        return identity

    @asyncio.coroutine
    def on_ready(self):
        with scoped_session(self.db) as session:
            for member in self.get_all_members():
                patron = session.query(models.Patron).filter_by(id=member.id).first()
                if not patron:
                    self.add_patron(member, session)

    def get_destination(self, id):
        speaking_with = self.get_channel(id)
        if not speaking_with:
            for server in self.servers:
                for member in server.members:
                    if member.id == id:
                        speaking_with = member

        return speaking_with

    @command('info', pass_context=True)
    async def command_info(self, ctx):
        """ Display information about yourself, including what suit you're using."""
        em = discord.Embed()
        if ctx.patron.suit:
            em.set_thumbnail(url=ctx.patron.suit.identity.avatar)
            em.set_author(name=ctx.patron.suit.identity.name, icon_url=ctx.patron.suit.identity.avatar)
        else:
            em.set_thumbnail(url=ctx.patron.identity.avatar)
            em.set_author(name=ctx.patron.identity.name, icon_url=ctx.patron.identity.avatar)

        speaking_with = self.get_destination(ctx.patron.speaking_with)

        em.description = "Speaking with: {0}".format(speaking_with.name if speaking_with else 'No one')
        channel = ctx.message.channel
        await self.send_message(channel, embed=em)

    @command('suit', pass_context=True)
    async def command_suit(self, ctx):
        """ List available suits that can be worn."""
        suits = ctx.session.query(models.Suit)

        for suit in suits:
            em = discord.Embed()
            em.set_thumbnail(url=suit.identity.avatar)
            em.set_author(name=suit.identity.name, icon_url=suit.identity.avatar)

            channel = ctx.message.channel
            await self.send_message(channel, embed=em)

    @command('dress', pass_context=True)
    async def command_dress(self, ctx, suit_identity_name=None):
        """Pull on an available suit."""
        if not suit_identity_name:
            return

        suit = ctx.session.query(models.Suit).filter_by(identity_name=suit_identity_name).first()
        if not suit:
            return
        ctx.patron.suit_identity_name = suit.identity_name

    @command('undress', pass_context=True)
    async def command_undress(self, ctx):
        """Take off on an available suit."""
        ctx.patron.suit_identity_name = None

    @command('message', pass_context=True)
    async def command_message(self, ctx, destination=None):
        """Set which channel or user you are speaking to or provide a list of available destinations."""
        members = [member for member in self.get_all_members() if member != self.user]
        channels = [channel for channel in self.get_all_channels() if channel.name.startswith('nsfw-rp-')]

        if not destination:
            em = discord.Embed()
            em.set_author(name='Available Users/Channels')
            channel = ctx.message.channel
            description = """\nChannels:\n\t{0}\n\nUsers:\n\t{1}
            """
            em.description = description.format(
                '\n\t'.join(["{0} - {1}".format(member.name, member.status) for member in members]),
                '\n\t'.join([channel.name[len('nsfw-rp-'):] for channel in channels])
            )
            await self.send_message(channel, embed=em)

        else:
            members.extend(channels)
            member = list(
                filter(lambda x: (x.name[len('nsfw-rp-'):] if x.name.startswith('nsfw-rp-') else x.name) == destination,
                       members)
            )
            if not member:
                return
            ctx.patron.speaking_with = member[0].id

    @command('puppet', pass_context=True)
    async def no_command(self, ctx, destination=None):
        """Set which channel or user you are speaking to."""
        if not ctx.patron.speaking_with:
            return

        em = discord.Embed()
        em.set_thumbnail(url=ctx.patron.suit.identity.avatar)
        em.set_author(name=ctx.patron.suit.identity.name, icon_url=ctx.patron.suit.identity.avatar)
        em.description = ctx.message.content
        await self.send_message(self.get_destination(ctx.patron.speaking_with), embed=em)

    @asyncio.coroutine
    def on_message(self, message):

        view = StringView(message.content)
        if self._skip_check(message.author, self.user):
            return

        if message.channel.type != discord.ChannelType.private:
            return

        logger.info("{0} - {1}".format(message.author, message.content))
        prefix = yield from self._get_prefix(message)
        invoked_prefix = prefix

        if not isinstance(prefix, (tuple, list)):
            if not view.skip_string(prefix):
                invoked_prefix = None
        else:
            invoked_prefix = discord.utils.find(view.skip_string, prefix)

        invoker = view.get_word()
        tmp = {
            'bot': self,
            'invoked_with': invoker,
            'message': message,
            'view': view,
            'prefix': invoked_prefix
        }
        ctx = Context(**tmp)
        del tmp

        if invoked_prefix is None:
            invoker = 'puppet'

        if invoker in self.commands:
            cmd = self.commands[invoker]
            self.dispatch('command', cmd, ctx)
            try:
                yield from cmd.invoke(ctx)
            except CommandError as e:
                ctx.command.dispatch_error(e, ctx)
            else:
                self.dispatch('command_completion', cmd, ctx)
        elif invoker:
            exc = CommandNotFound('Command "{}" is not found'.format(invoker))
            self.dispatch('command_error', exc, ctx)

        if hasattr(ctx, 'session') and ctx.session:
            ctx.session.commit()
