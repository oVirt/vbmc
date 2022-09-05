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

import sys

import ovirtsdk4
from ovirtsdk4 import Connection
from ovirtsdk4 import types
from pyghmi.ipmi.bmc import Bmc


class OvirtBmc(Bmc):
    def __init__(self, authdata, port, address, vm, cache_status, engine_fqdn, engine_username, engine_password):
        super().__init__(authdata, port=port, address=address)
        self.ovirt_conn = Connection(
            url=f'https://{engine_fqdn}/ovirt-engine/api',
            username=engine_username,
            password=engine_password,
            insecure=True,
        )
        self.vms_service = self.ovirt_conn.system_service().vms_service()
        self.vm_id = None
        self.vm_name = None
        self.cache_disabled = not cache_status
        self.cached_status = None
        self.target_status = None
        try:
            self.vm_id, self.vm_name = self._find_vm(vm)
            self.log(f'Managing vm {self.vm_name} ({self.vm_id}) on port {port}')
        except Exception as e:
            self.log(f'Exception finding vm "{vm}": {e}')
            sys.exit(1)

    def _find_vm(self, vm):
        try:
            # assume vm is ID
            name = self.vms_service.service(vm).get().name
            return vm, name
        except ovirtsdk4.NotFoundError:
            # assume vm is name
            vms = self.vms_service.list(search=f'name={vm}')
            try:
                return vms[0].id, vms[0].name
            except IndexError:
                self.log(f'Could not find specified vm {vm}')
                sys.exit(1)

    def get_boot_device(self):
        """Return the currently configured boot device"""
        vm = self.vms_service.service(self.vm_id).get()
        retval = vm.os.boot.devices[0]
        self.log('Reporting boot device', retval)
        return str(retval)

    def set_boot_device(self, bootdevice):
        """Set the boot device for the managed vm

        :param bootdevice: One of ['network', 'hd', 'cdrom'] to set the boot device to network, hard disk or CD-ROM
                           respectively.
        """
        vm = self.vms_service.service(self.vm_id).get()
        if bootdevice == 'network':
            vm.os.boot.devices[0] = types.BootDevice.NETWORK
        elif bootdevice == 'hd':
            vm.os.boot.devices[0] = types.BootDevice.HD
        elif bootdevice == 'cdrom':
            vm.os.boot.devices[0] = types.BootDevice.CDROM
        else:
            raise Exception(f'Boot device {bootdevice} not supported')
        self.vms_service.service(self.vm_id).update(vm)
        self.log(f'Set boot device on {self.vm_name} ({self.vm_id}) to {bootdevice}')

    def cold_reset(self):
        # Reset of the BMC, not managed system, here we will exit the demo
        self.log('Shutting down in response to BMC cold reset request')
        sys.exit(0)

    def _vm_up(self):
        no_cached_data = self.cached_status is None
        vm_changing_state = self.target_status is not None and self.cached_status != self.target_status

        if no_cached_data or vm_changing_state or self.cache_disabled:
            vm = self.vms_service.service(self.vm_id).get()
            self.cached_status = vm.status

        vm_is_up = self.cached_status == types.VmStatus.UP
        vm_is_powering_up = (
            self.cached_status == types.VmStatus.POWERING_UP or self.cached_status == types.VmStatus.REBOOT_IN_PROGRESS
        )

        return vm_is_up or vm_is_powering_up

    def get_power_state(self):
        """Returns the current power state of the managed vm"""
        state = self._vm_up()
        self.log(f'Reporting power state "{state}" for vm {self.vm_name} ({self.vm_id})')
        return state

    def power_off(self):
        """Stop the managed vm"""
        # this should be power down without waiting for clean shutdown
        self.target_status = types.VmStatus.DOWN
        if self._vm_up():
            self.vms_service.service(self.vm_id).stop()
            self.log(f'Powered {self.vm_name} ({self.vm_id}) down')
        else:
            self.log(f'{self.vm_name} ({self.vm_id}) is already down.')

    def power_on(self):
        """Start the managed vm"""
        self.target_status = types.VmStatus.UP
        if not self._vm_up():
            self.vms_service.service(self.vm_id).start()
            self.log(f'Powered {self.vm_name} ({self.vm_id}) up')
        else:
            self.log(f'{self.vm_name} ({self.vm_id}) is already up.')

    def power_reset(self):
        """Not implemented"""
        print('WARNING: Received request for unimplemented action power_reset')

    def power_shutdown(self):
        """Stop the managed vm"""
        # should attempt a clean shutdown
        self.target_status = types.VmStatus.DOWN
        self.vms_service.service(self.vm_id).shutdown()
        self.log(f'Politely shut {self.vm_name} ({self.vm_id}) down')

    def log(self, *msg):
        """Helper function that prints msg and flushes stdout"""
        print(' '.join(msg))
        sys.stdout.flush()
