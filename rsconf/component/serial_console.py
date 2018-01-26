"""
$ ra 1 get BIOS.SerialCommSettings
[Key=BIOS.Setup.1-1#SerialCommSettings]
ConTermType=Vt100Vt220
FailSafeBaud=115200
RedirAfterBoot=Enabled
SerialComm=Off
SerialPortAddress=Com1

ssh root@<idrac-ip>
racadm
set IOS.SerialCommSettings.RedirAfterBoot Enabled
set BIOS.SerialCommSettings.SerialPortAddress Serial1Com2Serial2Com1
job create BIOS.Setup.1-1
serveraction powercycle
```


https://kernelmanic.com/2015/10/14/enable-serial-console-on-centosrhel-7/

https://help.ubuntu.com/community/SerialConsoleHowto


```text
$ diff /etc/default/grub-dist /etc/default/grub
5,6c5,7
< GRUB_TERMINAL_OUTPUT="console"
< GRUB_CMDLINE_LINUX="crashkernel=auto rd.md.uuid=2f8476d6:c69ef43a:634bb920:01b6e507 rd.lvm.lv=centos/root rd.md.uuid=591be47b:fb3549c1:28d3b4b0:57583bf5 rhgb quiet"
---
> GRUB_TERMINAL="console serial"
> GRUB_SERIAL_COMMAND="serial --speed=115200 --unit=0 --word=8 --parity=no --stop=1"
> GRUB_CMDLINE_LINUX="crashkernel=auto rd.md.uuid=2f8476d6:c69ef43a:634bb920:01b6e507 rd.lvm.lv=centos/root rd.md.uuid=591be47b:fb3549c1:28d3b4b0:57583bf5 console=tty1 console=ttyS0,115200n8"
```

```sh
grub2-mkconfig -o /boot/grub2/grub.cfg
```

To test:

```sh
systemctl start serial-getty@ttyS0.service
```

To enable:

```sh
systemctl enable serial-getty@ttyS0.service
"""
