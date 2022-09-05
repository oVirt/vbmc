#
# Copyright 2022 Red Hat, Inc.
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

import argparse
import logging
import os

from ovirtbmc import ovirtbmc


LOGGER = logging.getLogger(__name__)


def main(args):
    parser = argparse.ArgumentParser(
        prog='ovirtbmc',
        description='Virtual BMC for controlling oVirt vm',
    )
    parser.add_argument('--port', dest='port', type=int, default=623, help='Port to listen on; defaults to 623')
    parser.add_argument('--address', dest='address', default='::', help='Address to bind to; defaults to ::')
    parser.add_argument('--vm', dest='vm', help='The id or name of the oVirt vm to manage')
    parser.add_argument('--vm-inventory', dest='vm_inventory', help='A file containing a list of vms\' ids or names to manage')
    parser.add_argument(
        '--cache-status',
        dest='cache_status',
        default=False,
        action='store_true',
        help='Cache the status of the managed vm. This can reduce load on the host, but if the vm status is changed '
        'outside the BMC then it may become out of sync.',
    )
    parser.add_argument(
        '--engine-fqdn',
        dest='engine_fqdn',
        required=True,
        help='Engine FQDN',
    )
    parser.add_argument(
        '--engine-username',
        dest='engine_username',
        default='admin@internal',
        help='Engine username; defaults to admin@internal',
    )
    parser.add_argument(
        '--engine-password',
        dest='engine_password',
        default='123456',
        help='Engine password; defaults to 123456',
    )

    args = parser.parse_args(args=args)

    if args.vm is None and args.vm_inventory is None:
        parser.error('You need to pass a single VM via --vm or a file with list of VMs via --vm-inventory')

    port = args.port

    if args.vm_inventory:
        with open(args.vm_inventory) as inventory:
            for vm in inventory:
                vm = vm.strip()
                res = os.fork()
                if res == 0:
                    LOGGER.debug(f"Child running for {vm} on {port}")
                    break
                elif res > 0:
                    port += 1
                else:
                    raise RuntimeException("Fork failed")
            else:
                LOGGER.debug("Parent process waiting on children")
                try:
                    while True:
                        os.wait()
                except ChildProcessError:
                    pass
                LOGGER.debug("All children finished")
                return 0
    else:
        vm = args.vm

    # Default to ipv6 format, but use the appropriate format for ipv4 address.
    address = args.address if ':' in args.address else f'::ffff:{args.address}'
    mybmc = ovirtbmc.OvirtBmc(
        {'admin': 'password'},
        port=port,
        address=address,
        vm=vm,
        cache_status=args.cache_status,
        engine_fqdn=args.engine_fqdn,
        engine_username=args.engine_username,
        engine_password=args.engine_password,
    )
    mybmc.listen()
