# Fata

Fata is an open source ad blocker that relies on DNS adblocking, 
pattern matching and DPI to identify and block ads.

This project's objective is to provide a simple yet powerfull setup
for a local proxy, managable from a clean web interface
(inspired by Pi-Hole and Brave Shields)

### Tech Stack

**Shields Engine**
- base engine based on Brave's Adblock library, written in Rust (with python bindings)
- Fata engine written in python
- mitmproxy to intercept HTTP and HTTPS trafic 

**Web interface**
- **Backend**
    - Flask
- **Frontend**
    - React
    - Vite.js
    - Typescript

# How it works
The whole process is quite simple

1. the request gets intercepted from Fata
2. the Shield engine first performs a series of inpections on the request
    - the request gets passed throug a series of scanners for Deep Packet Inspection
    - if nothing is found, the request is confronted against a list of known signatures
3. if the request passes all checks, it gets forwarded and you can see the response


# How to run


> [!NOTE]
> This is still in development mode; therefore there is still is quite some
> setup to do in order to run Fata*

1. **Create a virtual environment**  
    - `python -m venv .venv`
    - `source .venv/bin/activate` on Linux and `./.venv/Scripts/activate` on Windows (Powershell)

2. **Install dependencies**
    - `pip install -r requirements.txt` in the project's root 
    - `npm i` inside `fata/web/frontend`
    
3. **Activate engine** (this will also start the web backend)  
    - run `make` in the root of the project

4. **Start the web interface**
    - run `npm run dev` inside `fata/web/frontend`
    - this will automatically open the web interface in the browser
> [!NOTE]
> You will need to install mitmproxy's certificate to intercept HTTPS traffic.  
> To do so, after you run make, visit `mitm.it` and install the certificate for your device.  
> We also provide certificates available in the `certs/` folder  
> (but still, informations on how to install them can be found on `mitm.it`).
