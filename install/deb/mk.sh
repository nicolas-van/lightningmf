#! /bin/bash

author="Nicolas Vanhoren <nicolas.vanhoren@fakemail.com>"
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

py2dsc -m "$author" $package-*.tar.gz
cp copyright deb_dist/$package-*/debian/
pushd .
cd deb_dist/$package-*/
debuild
popd
cp deb_dist/*.deb .
