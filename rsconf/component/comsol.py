40  groupadd -g 524 lmcomsol
41  useradd -g lmcomsol -u 524 lmcomsol
42  groupadd -g 525 comsol-admin
43  useradd -g 525 -u 525 comsol-admin
44  yum install -y webkitgtk
45  df
46  df -h
47  ls /tmp
48  file /tmp/comsol3556433851984569318install
49  ls -al /tmp/comsol3556433851984569318install
50  less /tmp/comsol3556433851984569318install
51  yum install xorg-x11-xauth
yum install -y libXtst

License file does not support this version.
Feature:       SERIAL
Application version > License version: 5.3 > 5.21
License path:  /tmp/cscomsol037168/comsol364349862096318446.dat:
FlexNet Licensing error:-21,126
For further information, refer to the FlexNet Licensing documentation,
available at "www.flexerasoftware.com".
yum install -y redhat-lsb-core
yum install -y mesa-dri-drivers

glxinfo
name of display: localhost:10.0
libGL error: No matching fbConfigs or visuals found
libGL error: failed to load driver: swrast
X Error of failed request:  GLXBadContext
Major opcode of failed request:  150 (GLX)
Minor opcode of failed request:  6 (X_GLXIsDirect)
Serial number of failed request:  23
Current serial number in output stream:  22


https://github.com/ControlSystemStudio/cs-studio/issues/1828
defaults write org.macosforge.xquartz.X11 enable_iglx -bool true

+iglx

canberra-gtk-module

  243  yum install tigervnc-server -y
    244  yum install gnome-classic-session gnome-terminal

    didn't need
      226  yum install -y mesa-dri-drivers
      235  yum install -y glx-utils

    yum install gnome-classic-session gnome-terminal

    disable systemd lisetn on sunrpc all sockets
    comsol listens on *:tcp


    screen sharing


    echo passwd | vncpasswd −f  > ~/.vnc/passwd
    cat ~/.vnc/config
    localhost
    geometry=1600x900
    # alwaysshared
    nolisten=tcp
