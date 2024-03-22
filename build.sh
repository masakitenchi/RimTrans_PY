#!/bin/bash
pip install -r requirements.txt

args="-n Pyscripts -y"
while [[ "$#" -gt 0 ]]; do
	case $1 in
		-w|--windowed) 
			args="--windowed ${args}" 
			shift 
			;;
	esac
done
pyinstaller src/Rimtrans_py/__main__.py $args
