#!/bin/bash
pip install pyinstaller
pip install lxml

args="-n Pyscripts -y"
while [[ "$#" -gt 0 ]]; do
	case $1 in
		-w|--windowed) 
			args="--windowed ${args}" 
			shift 
			;;
	esac
done
pyinstaller __main__.py $args
