#! /usr/bin/python
# coding=utf8
# the above tag defines encoding for this document and is for Python 2.x compatibility

import re
import sys
import subprocess

def call_cmd(cmd):
  print("> {0}".format(cmd))
  result = subprocess.call(cmd, shell=True)
  if result != 0:
    sys.exit("Failed with code: {0}".format(result))

def exec_and_read(cmd):

  print("> {0}".format(cmd))
  output = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read()
  # print output
  return output

def exec_and_match(cmd, regex, name):
  output = exec_and_read(cmd)
  match = re.search(regex, output, re.MULTILINE)

  if match is None:
    sys.exit("Could not identify {0}!".format(name))

  result = match.group(1)
  print("{0}: {1}".format(name, result))
  return result

def test_lsusb(lsusb, vendor_name):
  lsusb_regex = r"Bus.*Device.*:\sID\s[0-9a-z:]+\s{0}.*\n".format(re.escape(vendor_name))
  match = re.search(lsusb_regex, lsusb, re.MULTILINE)
  if match is not None:
    print("{0} detected!".format(vendor_name))
  return match is not None

def pass_usb_device_to_vm(device_name, vm_name):
  pusb_list_cmd = "sudo xe pusb-list"
  usb_regex = r"uuid.*:\s([0-9a-z-]+)\n.*\n.*\n\s*vendor-desc.*:\s{0}".format(re.escape(device_name))
  usb_uuid = exec_and_read(
    pusb_list_cmd,
    usb_regex,
    "USB UUID for {0}".format(device_name)
  )

  param_set_cmd = "sudo xe pusb-param-set uuid={0} passthrough-enabled=true".format(usb_uuid)
  call_cmd(param_set_cmd)

  usb_groups_cmd = "sudo xe usb-group-list PUSB-uuids={0}".format(usb_uuid)
  group_regex = r"uuid.*:\s([0-9a-z-]+)\n.*name-label.*:\sGroup\sof\s[a-z0-9\s]+USBs"
  usb_group = exec_and_read(usb_groups_cmd, group_regex, "USB Group")

  vm_list_cmd = "sudo xe vm-list"
  vm_regex = r"uuid.*:\s([a-z0-9\-]+)$\s*name-label.*:\s{0}".format(vm_name)
  vm_uuid = exec_and_read(vm_list_cmd, vm_regex, "VM UUID")

  vm_shutdown_cmd = "sudo xe vm-shutdown uuid={0}".format(vm_uuid)
  call_cmd(vm_shutdown_cmd)

  vusb_create_cmd = "sudo xe vusb-create usb-group-uuid={0} vm-uuid={1}".format(usb_group, vm_uuid)
  call_cmd(vusb_create_cmd)

  vm_start_cmd = "sudo xe vm-start uuid={0}".format(vm_uuid)
  call_cmd(vm_start_cmd)

def main():

  if len(sys.argv) < 3:
    print("Please specify target VM the using -vm <VM Name> parameter")
    print("Example:")
    print("  > ./coral.py -vm MyVirtualMachineName")
    sys.exit("Required parameter missing")

  # Run `lsusb` command and store the output in the lsusb variable
  lsusb = exec_and_read("lsusb")

  vm_name = sys.argv[2]
  device_name = "Google Inc."

  if test_lsusb(lsusb, device_name):
    print("Coral found. Attaching to VM {0}".format(vm_name))
    pass_usb_device_to_vm(device_name, vm_name)
    print("Done.")
    sys.exit()

  device_name = "Global Unichip Corp."
  if not test_lsusb(lsusb, device_name):
    sys.exit("Coral device not detected!")

  print("Coral device detected as {0} but it needs to be initialized.".format(device_name))
  print("Target VM ({1}) will reboot!".format(vm_name))

  pass_usb_device_to_vm(device_name, vm_name)

  print("Uninitialized Coral passed to VM ({0}).".format(vm_name))
  print("Please wait for the VM to finish rebooting and rerun this script!")
  print("Exiting.")

if __name__ == '__main__':
  main()
