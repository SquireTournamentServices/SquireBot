#! /usr/bin/bash
# Check syntax
cd ../
find . | grep .py$ | xargs --verbose -n 1 python3 -m py_compile
echo $?
code=$?
if [ $code -ge 1 ]
then
    echo "Invalid Syntax (see output above)"
    exit 1
fi

cd tests

# Run tests
python3 testRunner.py
echo $?
code=$?
if [ $code -ge 1 ]
then
    echo "Some tests failed (see output above)"
    exit 2
fi
