#! /bin/sh

rm -rf lightningmf/usr

mkdir -p lightningmf/usr/bin
ln -s /usr/lib/lightningmf/main.py lightningmf/usr/bin/lightningmf

dir=lightningmf/usr/lib/lightningmf
mkdir -p $dir
cp ../../main.py $dir/
cp ../../view.ui $dir/
cp ../../config.ui $dir/

chown root:root lightningmf
find lightningmf -executable | while read el; do chmod 0755 $el; done
find lightningmf -not -executable | while read el; do chmod 0644 $el; done

dpkg-deb --build lightningmf
