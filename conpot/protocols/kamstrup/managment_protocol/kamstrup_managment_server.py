# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import logging
import socket
from lxml import etree

from gevent.server import StreamServer

import conpot.core as conpot_core
from command_responder import CommandResponder

logger = logging.getLogger(__name__)


class KamstrupManagmentServer(object):
    def __init__(self, template, timeout=0):
        self.template = template
        self.timeout = timeout
        self.command_responder = CommandResponder(template)

        dom = etree.parse(template)
        mac_address = dom.xpath('//conpot_template/protocols/kamstrup_managment/mac_address/text()')[0]
        self.banner = "\r\nWelcome...\r\nConnected to [{0}]\r\n".format(mac_address)

        logger.info('Kamstrup managment protocol server initialized.')

    def handle(self, sock, address):
        session = conpot_core.get_session('kamstrup_managment_protocol', address[0], address[1])
        logger.info('New connection from {0}:{1}. ({2})'.format(address[0], address[1], session.id))

        try:
            sock.send(self.banner)

            while True:
                request = sock.recv(1024)
                if not request:
                    logger.info('Client disconnected. ({0})'.format(session.id))
                    break

                logdata = {'request': request}
                response = self.command_responder.respond(request)
                logdata['response'] = response
                logger.debug('Kamstrup managment traffic from {0}: {1} ({2})'.format(address[0], logdata, session.id))
                session.add_event(logdata)

                if response is None:
                    break
                sock.send(response)

        except socket.timeout:
            logger.debug('Socket timeout, remote: {0}. ({1})'.format(address[0], session.id))

        sock.close()

    def get_server(self, host, port):
        connection = (host, port)
        server = StreamServer(connection, self.handle)
        logger.info('Kamstrup managment protocol server started on: {0}'.format(connection))
        return server


