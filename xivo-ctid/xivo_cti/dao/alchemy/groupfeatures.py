# -*- coding: utf-8 -*-
# Copyright (C) 2012  Avencall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Alternatively, XiVO CTI Server is available under other licenses directly
# contracted with Avencall. See the LICENSE file at top of the source tree
# or delivered in the installable package in which XiVO CTI Server is
# distributed for more details.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from xivo_cti.dao.alchemy.base import Base
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String


class GroupFeatures(Base):

    __tablename__ = 'groupfeatures'

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    number = Column(String(40), nullable=False, default='')
    context = Column(String(39))
    transfer_user = Column(Integer, nullable=False, default=0)
    transfer_call = Column(Integer, nullable=False, default=0)
    write_caller = Column(Integer, nullable=False, default=0)
    write_calling = Column(Integer, nullable=False, default=0)
    timeout = Column(Integer, nullable=False, default=0)
    preprocess_subroutine = Column(String(39))
    deleted = Column(Integer, nullable=False, default=0)
