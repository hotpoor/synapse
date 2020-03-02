# -*- coding: utf-8 -*-
# Copyright 2020 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from synapse.api.errors import SynapseError
from synapse.http.servlet import parse_integer
from synapse.replication.http._base import ReplicationEndpoint

logger = logging.getLogger(__name__)


class ReplicationGetStreamUpdates(ReplicationEndpoint):
    NAME = "get_repl_stream_updates"
    PATH_ARGS = ("stream_name",)
    METHOD = "GET"

    def __init__(self, hs):
        super(ReplicationGetStreamUpdates, self).__init__(hs)

        from synapse.replication.tcp.streams import STREAMS_MAP

        self.streams = {stream.NAME: stream(hs) for stream in STREAMS_MAP.values()}

    @staticmethod
    def _serialize_payload(stream_name, from_token, upto_token, limit):
        return {"from_token": from_token, "upto_token": upto_token, "limit": limit}

    async def _handle_request(self, request, stream_name):
        stream = self.streams.get(stream_name)
        if stream is None:
            raise SynapseError(400, "Unknown stream")

        from_token = parse_integer(request, "from_token", required=True)
        upto_token = parse_integer(request, "upto_token", required=True)
        limit = parse_integer(request, "limit", required=True)

        updates, upto_token, limited = await stream.get_updates_since(
            from_token, upto_token, limit
        )

        return (
            200,
            {"updates": updates, "upto_token": upto_token, "limited": limited},
        )


def register_servlets(hs, http_server):
    ReplicationGetStreamUpdates(hs).register(http_server)
