# Getting Started

[Radio Caca]

[Radio Caca]: https://www.radiocaca.com

## Important disclaimer
This software is intended for use by individuals 
familiar with Python programming language. It uses
sensitive signature code from MetaMask wallet which 
needs to be safe and secure at all times. Make sure 
to inspect the code for any attempts to send your 
information anywhere except https://metamon-api.radiocaca.com/usm-api 
(official metamon game api). We are not responsible 
for any loss incurred if you used modified version 
of this code from other sources!

## Prerequisites

To start using this program Python needs to be 
installed and some packages. The easiest way to 
obtain Python is to install [miniconda], use 
latest release for your platform Linux/Mac/Windows

[miniconda]: https://docs.conda.io/en/latest/miniconda.html

After installation open command line with 
virtual environment activated and run following
command

    pip install tqdm requests pandas argparse

to install all necessary packages

## Prepare wallet(s) information

First open [game] with your browser and make sure 
your wallet is active in MetaMask plugin. Enter
dev mode in browser (Chrome press Ctrl + Shift + I,
or go to menu -> More Tools -> Developer Tools)
<img src="screenshots/enter_game_dev.png" />
select "Network" and "Fetc/XHR" in developer tools menu.

[game]: https://metamon.radiocaca.com

! <b>Imoprtant: make sure to do it before signing 
in with MetaMask</b> !

<img src="screenshots/enter_game_sign.png" />

After login entry with "login" name should appear 
in the list of requests of developers tools.
<img src="screenshots/enter_game_login.png" />
There
after clicking on it and selecting "payload" in new 
menu all 3 essential values wil appear (address, sign, 
msg) copy those values and save in file (for example
default is "wallets.tsv" in same dir where you run it).

<img src="screenshots/enter_game_credentials.png" />

File should have 4 columns tab separated (tsv):

    name    address sign    msg
    Wallet1 0x123.. 0x23... LogIn-...

Name is custom, choose what you want. If you save 
stats to file it will be used for name of that file.
If you have multiple wallets you can add several rows
to this tsv file.

### Alternatively can generate TSV with JS code

After login success, in Chrome open Developer Tools, switch to tab Console, paste the bellow script => Enter

    (()=>{var e=[["name","address","sign","msg"],["Wallet1",sessionStorage.getItem("account-address"),sessionStorage.getItem("connect-sign"),sessionStorage.getItem("connect-signMsg")]],t="";e.forEach(function(n,a){dataString=n.join("\t"),t+=a<e.length?dataString+"\n":dataString});!function(e,t,n){var a=document.createElement("a");n=n||"application/octet-stream",navigator.msSaveBlob?navigator.msSaveBlob(new Blob([e],{type:n}),t):URL&&"download"in a?(a.href=URL.createObjectURL(new Blob([e],{type:n})),a.setAttribute("download",t),document.body.appendChild(a),a.click(),document.body.removeChild(a)):location.href="data:application/octet-stream,"+encodeURIComponent(e)}(t,"wallets.tsv","text/tsv;encoding:utf-8")})();

Thanks to <a href='https://github.com/thucngv'>thucngv</a>!

# Preparation is complete! 
## Ready to roll?

To get familiar run metamon_player.py to get help
    
    python metamon_play.py --help

Message:
    
    usage: metamon_play.py [-h] [-i INPUT_TSV] [-nl] [-nb] [-e] [-s]

    optional arguments:
    -h, --help            show this help message and exit
    -i INPUT_TSV, --input-tsv INPUT_TSV
    Path to tsv file with wallets' access records (name, address, sign, login message) name is used for filename with table of results.
    Results for each wallet are saved in separate files
    -nl, --no-lvlup       Disable automatic lvl up (if not enough potions/diamonds it will be disabled anyway) by default lvl up will be attempted after each battle
    -nb, --skip-battles   No battles, use when need to only mint eggs from shards
    -e, --mint-eggs       Automatically mint eggs after all battles done for a day
    -s, --save-results    To enable saving results on disk use this option. Two files <name>_summary.tsv and <name>_stats.tsv will be saved in current dir.

for example:

    paython metamon_play.py -e -s

Will try to read file wallets.tsv in current dir,
auto fight, mint eggs, and save stats to corresponding 
files. Now you ready to have fun and explore other options.

<b> Note: </b> Since fee for all leagues is the same bot will 
try to fight in highest league for corresponding metamon and 
it is not configurable at this 
time.

Also if there will be interest we can release version which
uses access token instead of signature (tokens expire and it
is more secure to use, however it will require manual step of
obtaining one every day for battles)

Hope you will have fun playing and this script will make it 
a little bit less tedious. Enjoy!