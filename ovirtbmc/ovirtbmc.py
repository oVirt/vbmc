#!/usr/bin/env python
#
# Copyright 2015 Red Hat, Inc.
# Copyright 2015 Lenovo
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

# Virtual BMC for controlling oVirt VMs, based on openstackbmc from openstack-virtual-baremetal

# Sample ipmitool commands:
# ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power on
# ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power status
# ipmitool -I lanplus -U admin -P password -H 127.0.0.1 chassis bootdev pxe|disk|cdrom
# ipmitool -I lanplus -U admin -P password -H 127.0.0.1 mc reset cold

import argparse
import sys
import time

from ovirtsdk4 import Connection
from ovirtsdk4 import types
from pyghmi.ipmi.bmc import Bmc


class OvirtBmc(Bmc):
    def __init__(self, authdata, port, address, vm_name, cache_status, engine_fqdn, engine_username, engine_password):
        super().__init__(authdata, port=port, address=address)
        self.ovirt_conn = Connection(
            url=f'https://{engine_fqdn}/ovirt-engine/api',
            username=engine_username,
            password=engine_password,
            insecure=True,
        )
        self.vms_service = self.ovirt_conn.system_service().vms_service()
        self.vm = None
        self.cache_disabled = not cache_status
        self.cached_status = None
        self.target_status = None
        # At times the bmc service is started before important things like networking have fully initialized. Keep
        # trying to find the vm indefinitely, since there's no point in continuing if we don't have an vm.
        while True:
            try:
                self.vm = self._find_vm(vm_name)
                if self.vm is not None:
                    self.log(f'Managing vm: {vm_name} ID: {self.vm}')
                    break
            except Exception as e:
                self.log(f'Exception finding vm "{vm_name}": {e}')
                time.sleep(1)

    def _find_vm(self, vm_name):
        vms = (vm for vm in self.vms_service.list() if vm.name == vm_name)
        try:
            vm_id = next(vms).id
            return vm_id
        except StopIteration:
            self.log(f'Could not find specified vm {vm_name}')
            sys.exit(1)

    def get_boot_device(self):
        """Return the currently configured boot device"""
        vm = self.vms_service.service(self.vm).get()
        retval = vm.os.boot.devices[0]
        self.log('Reporting boot device', retval)
        return retval

    def set_boot_device(self, bootdevice):
        """Set the boot device for the managed vm

        :param bootdevice: One of ['network', 'hd', 'cdrom'] to set the boot device to network, hard disk or CD-ROM
                           respectively.
        """
        vm = self.vms_service.service(self.vm).get()
        if bootdevice == 'network':
            vm.os.boot.devices[0] = types.BootDevice.NETWORK
        elif bootdevice == 'hd':
            vm.os.boot.devices[0] = types.BootDevice.HD
        elif bootdevice == 'cdrom':
            vm.os.boot.devices[0] = types.BootDevice.CDROM
        else:
            raise Exception(f'Boot device {bootdevice} not supported')
        self.vms_service.service(self.vm).update(vm)
        self.log('Set boot device to', bootdevice)

    def cold_reset(self):
        # Reset of the BMC, not managed system, here we will exit the demo
        self.log('Shutting down in response to BMC cold reset request')
        sys.exit(0)

    def _vm_up(self):
        no_cached_data = self.cached_status is None
        vm_changing_state = self.cached_status != self.target_status

        if no_cached_data or vm_changing_state or self.cache_disabled:
            vm = self.vms_service.service(self.vm).get()
            self.cached_status = vm.status

        vm_is_up = self.cached_status == types.VmStatus.UP
        vm_is_powering_up = self.cached_status == types.VmStatus.POWERING_UP

        return vm_is_up or vm_is_powering_up

    def get_power_state(self):
        """Returns the current power state of the managed vm"""
        state = self._vm_up()
        self.log(f'Reporting power state "{state}" for vm {self.vm}')
        return state

    def power_off(self):
        """Stop the managed vm"""
        # this should be power down without waiting for clean shutdown
        self.target_status = types.VmStatus.DOWN
        if self._vm_up():
            self.vms_service.service(self.vm).stop()
            self.log(f'Powered off {self.vm}')
        else:
            self.log(f'{self.vm} is already off.')

    def power_on(self):
        """Start the managed vm"""
        self.target_status = types.VmStatus.UP
        if not self._vm_up():
            self.vms_service.service(self.vm).start()
            self.log(f'Powered on {self.vm}')
        else:
            self.log(f'{self.vm} is already up.')

    def power_reset(self):
        """Not implemented"""
        print('WARNING: Received request for unimplemented action power_reset')

    def power_shutdown(self):
        """Stop the managed vm"""
        # should attempt a clean shutdown
        self.target_status = types.VmStatus.DOWN
        self.vms_service.service(self.vm).shutdown()
        self.log(f'Politely shut down {self.vm}')

    def log(self, *msg):
        """Helper function that prints msg and flushes stdout"""
        print(' '.join(msg))
        sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(
        prog='ovirtbmc',
        description='Virtual BMC for controlling oVirt vm',
    )
    parser.add_argument('--port', dest='port', type=int, default=623, help='Port to listen on; defaults to 623')
    parser.add_argument('--address', dest='address', default='::', help='Address to bind to; defaults to ::')
    parser.add_argument('--vm-name', dest='vm_name', required=True, help='The name of the oVirt vm to manage')
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

    args = parser.parse_args()
    # Default to ipv6 format, but use the appropriate format for ipv4 address.
    address = args.address if ':' in args.address else f'::ffff:{args.address}'
    mybmc = OvirtBmc(
        {'admin': 'password'},
        port=args.port,
        address=address,
        vm_name=args.vm_name,
        cache_status=args.cache_status,
        engine_fqdn=args.engine_fqdn,
        engine_username=args.engine_username,
        engine_password=args.engine_password,
    )
    mybmc.listen()


if __name__ == '__main__':
    main()
