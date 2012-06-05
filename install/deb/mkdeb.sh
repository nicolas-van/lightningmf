#! /bin/sh


rm -rf lightningmf/usr

mkdir -p lightningmf/usr/bin
ln -s /usr/lib/lightningmf/main.py lightningmf/usr/bin/lightningmf

dir=lightningmf/usr/lib/lightningmf

mkdir -p $dir
cp ../../main.py $dir/
cp ../../view.ui $dir/
cp ../../config.ui $dir/

dpkg-deb --build lightningmf
