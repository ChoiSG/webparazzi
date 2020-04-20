# webparazzi
Simple script to take screenshot from a list of subdomains or ip addresses 

## Under Construction - PoC 
Even though webparazzi is a simple script, I only had 3 hours to build it. So the script is barely in PoC state, barely working at the moment. 

## Installation 
```
git clone https://github.com/ChoiSG/webparazzi.git
cd ./webparazzi
pip3 install -r requirements.txt

python3 webparazzi.py -h 
```

## Usage 

1. Have a text file with list of subdomains.

sample.txt
```
example.com
google.com
wow.this.does.not.exist.example.com
vpn.example.com
```

2. Execute the script 
```
python3 webparazzi.py -f sample.txt
```

3. Check the images folder! 

## Created for & Special Thanks to 
Boan Project 