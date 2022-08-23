# Virtual BMC for oVirt VMs

## Supported IPMI commands

```

  # Power the virtual machine on, off, graceful off, NMI and reset
  ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power on|off

  # Check the power status
  ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power status

  # Set the boot device to network, hd or cdrom
  ipmitool -I lanplus -U admin -P password -H 127.0.0.1 chassis bootdev pxe|disk|cdrom

```

## Acknowledgements
Parts of this project has been inspired by [openstack-virtual-baremetal](https://opendev.org/openstack/openstack-virtual-baremetal).
