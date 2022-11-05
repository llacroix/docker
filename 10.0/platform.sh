PLATFORM=`uname -m`

if [ $PLATFORM = "aarch64" ]
then
    echo -n "arm64"
else
if [ $PLATFORM = "x86_64" ]
then
    echo -n "amd64"
else
    echo -n $PLATFORM
fi
fi
