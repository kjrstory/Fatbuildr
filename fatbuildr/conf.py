#!/usr/bin/env python3
#
# Copyright (C) 2021 Rackslab
#
# This file is part of Fatbuildr.
#
# Fatbuildr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fatbuildr is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fatbuildr.  If not, see <https://www.gnu.org/licenses/>.

import configparser
import re
import logging

logger = logging.getLogger(__name__)


class RuntimeSubConfDirs(object):
    """Runtime sub-configuration class to hold directories paths."""

    def __init__(self):

        self.img = None
        self.queue = None
        self.state = None
        self.repos = None
        self.cache = None
        self.tmp = None

    def load(self, config):
        section = 'dirs'
        self.queue = config.get(section, 'queue')
        self.state = config.get(section, 'state')
        self.repos = config.get(section, 'repos')
        self.cache = config.get(section, 'cache')
        self.tmp = config.get(section, 'tmp')

    def dump(self):
        logger.debug("[dirs]")
        logger.debug("  queue: %s" % (self.queue))
        logger.debug("  state: %s" % (self.state))
        logger.debug("  repos: %s" % (self.repos))
        logger.debug("  cache: %s" % (self.cache))
        logger.debug("  tmp: %s" % (self.tmp))


class RuntimeSubConfImages(object):
    """Runtime sub-configuration class to hold images settings."""

    def __init__(self):

        self.storage = None
        self.defs = None
        self.formats = None
        self.create_cmd = None

    def load(self, config):
        section = 'images'
        self.storage = config.get(section, 'storage')
        self.defs = config.get(section, 'defs')
        self.formats = config.get(section, 'formats').split(',')
        self.create_cmd = config.get(section, 'create_cmd')

    def dump(self):
        logger.debug("[images]")
        logger.debug("  storage: %s" % (self.storage))
        logger.debug("  defs: %s" % (self.defs))
        logger.debug("  formats: %s" % (self.formats))
        logger.debug("  create_cmd: %s" % (self.create_cmd))


class RuntimeSubConfRegistry(object):
    """Runtime sub-configuration class to hold registry settings."""

    def __init__(self):

        self.conf = None

    def load(self, config):
        section = 'registry'
        self.conf = config.get(section, 'conf')

    def dump(self):
        logger.debug("[registry]")
        logger.debug("  conf: %s" % (self.conf))


class RuntimeSubConfContainers(object):
    """Runtime sub-configuration class to hold containers settings."""

    def __init__(self):

        self.init_opts = None

    def load(self, config):
        section = 'containers'
        self.init_opts = config.get(section, 'init_opts')

    def dump(self):
        logger.debug("[containers]")
        logger.debug("  init_opts: %s" % (self.init_opts))


class RuntimeSubConfKeyring(object):
    """Runtime sub-configuration class to hold keyring settings."""

    def __init__(self):

        self.storage = None
        self.type = None
        self.size = None
        self.expires = None

    def _parse_duration(self, _expires):
        m = re.search(r'(\d+)([a-z])', _expires)
        quantity = int(m.group(1))
        unit = m.group(2)
        if unit == 'd':
            self.expires = quantity * 86400
        elif unit == 'm':
            self.expires = quantity * 86400 * 30
        elif unit == 'y':
            self.expires = quantity * 86400 * 365
        else:
            raise ValueError("keyring expires unit '%s' is not valid" % (unit))

    def load(self, config):
        section = 'keyring'
        self.storage = config.get(section, 'storage')
        self.type = config.get(section, 'type')
        self.size = config.getint(section, 'size')
        try:
            self.expires = config.getboolean(section, 'expires')
        except ValueError:
            _expires = config.get(section, 'expires')
            self._parse_duration(_expires)
        if self.expires == True:
            raise ValueError("keyring expires must be set with a duration to be enabled")

    def dump(self):
        logger.debug("[keyring]")
        logger.debug("  storage: %s" % (self.storage))
        logger.debug("  type: %s" % (self.type))
        logger.debug("  size: %s" % (self.size))
        logger.debug("  expires: %s" % (str(self.expires)))


class RuntimeSubConfFormatDeb(object):
    """Runtime sub-configuration class to hold Deb format settings."""

    def __init__(self):

        self.init_cmd = None
        self.img_update_cmds = None
        self.env_update_cmds = None

    def load(self, config):
        section = 'format:deb'
        self.init_cmd = config.get(section, 'init_cmd')
        self.img_update_cmds = config.get(section, 'img_update_cmds')
        self.env_update_cmds = config.get(section, 'env_update_cmds')

    def dump(self):
        logger.debug("[format:deb]")
        logger.debug("  init_cmd: %s" % (self.init_cmd))
        logger.debug("  env_update_cmds: %s" % (self.env_update_cmds))


class RuntimeSubConfFormatRpm(object):
    """Runtime sub-configuration class to hold RPM format settings."""

    def __init__(self):

        self.init_cmd = None
        self.img_update_cmds = None
        self.env_update_cmds = None

    def load(self, config):
        section = 'format:rpm'
        self.init_cmd = config.get(section, 'init_cmd')
        self.img_update_cmds = config.get(section, 'img_update_cmds')
        self.env_update_cmds = config.get(section, 'env_update_cmds')

    def dump(self):
        logger.debug("[format:rpm]")
        logger.debug("  init_cmd: %s" % (self.init_cmd))
        logger.debug("  img_update_cmds: %s" % (self.img_update_cmds))
        logger.debug("  env_update_cmds: %s" % (self.env_update_cmds))


class RuntimeConfApp(object):
    """Runtime sub-configuration class common to all Fatbuildr applications."""

    def __init__(self):
        self.instance = None


class RuntimeSubConfCtl(RuntimeConfApp):
    """Runtime sub-configuration class to ctl parameters."""

    def __init__(self):
        super().__init__()
        self.action = None
        # parameters for image action
        self.operation = None
        self.force = None
        # parameters for package action
        self.package = None
        self.basedir = None
        self.user_name = None
        self.user_email = None

    def load(self, config):
       self.instance = config.get('run', 'default_instance')

    def dump(self):
        logger.debug("[run]")
        logger.debug("  instance: %s" % (self.instance))
        logger.debug("  action: %s" % (self.action))
        logger.debug("  operation: %s" % (self.operation))
        logger.debug("  force: %s" % (self.force))
        logger.debug("  package: %s" % (self.package))
        logger.debug("  basedir: %s" % (self.basedir))
        logger.debug("  user_name: %s" % (self.user_name))
        logger.debug("  user_email: %s" % (self.user_email))
        logger.debug("  build_msg: %s" % (self.build_msg))


class RuntimeSubConfd(RuntimeConfApp):
    """Runtime sub-configuration class to fatbuildrd parameters."""

    def __init__(self):
        super().__init__()

    def load(self, config):
        pass

    def dump(self):
        pass


class RuntimeConf(object):
    """Runtime configuration class common to all Fatbuildr applications."""

    def __init__(self, run):
        self.run = run
        self.dirs = RuntimeSubConfDirs()
        self.images = RuntimeSubConfImages()
        self.registry = RuntimeSubConfRegistry()
        self.containers = RuntimeSubConfContainers()
        self.keyring = RuntimeSubConfKeyring()
        self.deb = RuntimeSubConfFormatDeb()
        self.rpm = RuntimeSubConfFormatRpm()
        self.config = None

    def load(self):
        """Load configuration files and set runtime parameters accordingly."""
        self.config = configparser.ConfigParser()
        # read vendor configuration file and override with site specific
        # configuration file
        vendor_conf_path = '/usr/lib/fatbuildr/fatbuildr.ini'
        site_conf_path = '/etc/fatbuildr/fatbuildr.ini'
        logger.debug("Loading vendor configuration file %s" % (vendor_conf_path))
        self.config.read_file(open(vendor_conf_path))
        logger.debug("Loading site specific configuration file %s" % (site_conf_path))
        self.config.read_file(open(site_conf_path))
        self.run.load(self.config)
        self.dirs.load(self.config)
        self.images.load(self.config)
        self.registry.load(self.config)
        self.containers.load(self.config)
        self.keyring.load(self.config)
        self.deb.load(self.config)
        self.rpm.load(self.config)

    def dump(self):
        """Dump all runtime configuration parameters when in debug mode."""
        if not logger.isEnabledFor(logging.DEBUG):
            return
        self.run.dump()
        self.dirs.dump()
        self.images.dump()
        self.registry.dump()
        self.containers.dump()
        self.keyring.dump()
        self.deb.dump()
        self.rpm.dump()


class RuntimeConfCtl(RuntimeConf):
    """Runtime configuration class for FatbuildrCtl application."""

    def __init__(self):
        super().__init__(RuntimeSubConfCtl())


class RuntimeConfd(RuntimeConf):
    """Runtime configuration class for Fatbuildrd application."""

    def __init__(self):
        super().__init__(RuntimeSubConfd())