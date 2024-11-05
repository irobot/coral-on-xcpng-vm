# Coral USB device Passthrough to an XCP-ng VM

## Context

I have an XCP-ng server that hosts several virtual machines. One of the VMs needs access to a Google Coral USB device. Since all VMs are isolated from the host machine, each external device they need access to needs to be passed through to that VM explictly.

Doing that in XCP-ng requires going through a multi-step process:

1. List all USB devices visible to the host.
2. Figure out which one of them is the device we want passed through to the VM, and what its UUID is.
3. Tell XCP-ng to enable that device to be passed through. That creates a new USB group with its own UUID
4. Shutdown the target VM
5. Attach the device to the VM by providing the above USB *group* UUID.
6. Start up the target VM - the device is now accessible from within the VM.

See [XCP-ng USB Passthrough](https://docs.xcp-ng.org/compute/#%EF%B8%8F-usb-passthrough)

Needless to say, this is a tedious process that requires a lot of typing and copy & pasting if done manually.

## The problem

Whenever the XCP-ng host machine loses power for some reason, upon restart, the Coral device becomes "uninitialized". This manifests as `lsusb` listing it as manufactured by "Global Unichip Corp." instead of "Google Inc.". My assumption is that this is due to outdated USB drivers and/or the linux kernel version that XCP-ng is based on.

## Solution

The only solution I have been able to come up with is:
1. Pass the "uninitialized" device through to a VM that has a more up-to-date version of either Linux or Windows. It will still not be usable in the target VM, but somehow that kicks off a process that enables XCP-ng to see a new USB device, with manufacturer now correctly listed as "Google Inc.".
2. Pass the newly discovered device to the target VM.
3. Profit.

## Motivation

I've had to go through this whole process every time there was a power outage. Today I decided to try and ease the pain a little by writing a simple Python script to help automate most of it.

## How it works

Run the `coral.py` Python script.

> Note: installing Pyton on the XCP-ng host is not necessary, as XCP-ng ships with Python 2.7

The script needs to be provided the name of the target VM:
```
./coral.py -vm MyVMName
```

The script executes `lsusb` and looks for a device called "Google Inc.". If such a device is present it assusmes that this is the Coral device we want passed through to the target VM. It then executes all the necessary commands.

If "Google Inc." is not present in the output of lsusb, we check to see if "Global Unichip Corp." is present instead. If so, *that* USB device is passed through to the target machine.

> Note: The target VM will be restarted!

After the VM reboots, "Google Inc." should be present in the output of lsusb. At that point, the script needs to be rerun so the properly detected Coral device is passed through to the target VM.
