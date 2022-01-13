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

from .deb import ArtefactBuildDeb
from .rpm import ArtefactBuildRpm


class BuildFactory(object):

    _formats = {
        'deb': ArtefactBuildDeb,
        'rpm': ArtefactBuildRpm,
    }

    @staticmethod
    def get(conf, request):
        if not request.form.format in BuildFactory._formats:
            raise RuntimeError("format %s unsupported by builders" % (request.form.format))
        return BuildFactory._formats[request.form.format](conf, request)