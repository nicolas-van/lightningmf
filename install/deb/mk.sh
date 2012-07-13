#! /bin/bash

package="lightningmf"

rm $package-*.tar.gz
rm *.deb
rm -r deb_dist
pushd .
cd ../../
rm -r dist
./setup.py sdist
popd
mv ../../dist/$package-*.tar.gz .

py2dsc $package-*.tar.gz
cp control deb_dist/$package-*/debian/ || exit -1
cp copyright deb_dist/$package-*/debian/

pushd .
cd deb_dist/$package-*/
debuild
popd

pushd .
cd deb_dist/$package-*/debian/$package/usr/share/
mkdir applications
popd
cp *.desktop deb_dist/$package-*/debian/$package/usr/share/applications/

pushd .
cd deb_dist/$package-*/
debuild
popd
cp deb_dist/*.deb .
