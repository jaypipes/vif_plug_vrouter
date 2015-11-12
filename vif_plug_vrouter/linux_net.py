#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Implements vlans, bridges, and iptables rules using linux utilities."""

import os

from oslo_log import log as logging
from oslo_utils import excutils

from vif_plug_vrouter.i18n import _LE
from vif_plug_vrouter import processutils

LOG = logging.getLogger(__name__)


def device_exists(device):
    """Check if ethernet device exists."""
    return os.path.exists('/sys/class/net/%s' % device)


def create_tap_dev(dev, mac_address=None):
    if not device_exists(dev):
        try:
            # First, try with 'ip'
            processutils.execute('ip', 'tuntap', 'add', dev, 'mode',
                                 'tap', check_exit_code=[0, 2, 254],
                                 run_as_root=True)
        except processutils.ProcessExecutionError:
            # Second option: tunctl
            processutils.execute('tunctl', '-b', '-t', dev,
                                 run_as_root=True)
        if mac_address:
            processutils.execute('ip', 'link', 'set', dev, 'address', mac_address,
                                 check_exit_code=[0, 2, 254],
                                 run_as_root=True)
        processutils.execute('ip', 'link', 'set', dev, 'up',
                             check_exit_code=[0, 2, 254],
                             run_as_root=True)


def delete_net_dev(dev):
    """Delete a network device only if it exists."""
    if device_exists(dev):
        try:
            processutils.execute('ip', 'link', 'delete', dev,
                                 check_exit_code=[0, 2, 254],
                                 run_as_root=True)
            LOG.debug("Net device removed: '%s'", dev)
        except processutils.ProcessExecutionError:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed removing net device: '%s'"), dev)
