#!/bin/bash
pip install -r requirements.txt

args="-y --clean"
while [[ "$#" -gt 0 ]]; do
	case $1 in
		-w|--windowed) 
			args="--windowed ${args}" 
			shift 
			;;
	esac
done
pyinstaller $args -n Rimtrans_py --path=src/Rimtrans_py src/Rimtrans_py/__main__.py 
