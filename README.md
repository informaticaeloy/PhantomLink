![Python](https://img.shields.io/badge/python-3.x-blue)
![Flask](https://img.shields.io/badge/flask-framework-black)
![License](https://img.shields.io/badge/license-MIT-green)

# PhantomLink

Flask-based controlled browsing platform with proxying, URL inspection,
request logging and network diagnostics.

PhantomLink provides a **controlled web browsing environment** designed
for **security analysis, controlled navigation and traffic
inspection**.\
It allows users to browse external websites through an internal proxy
while collecting diagnostic information and logs.

------------------------------------------------------------------------

# Browseling

Controlled web browsing environment built with Flask.

Browseling provides a proxy-based browsing platform designed for
security analysis, controlled navigation and traffic inspection. It
allows users to browse external websites through an internal proxy while
collecting diagnostic information and logs.

------------------------------------------------------------------------

# Features

-   Web proxy navigation
-   URL inspection
-   Request logging
-   Network diagnostics (IP, latency)
-   Access control and authentication
-   User session management
-   Activity logging
-   Error monitoring
-   HTML rewriting for iframe compatibility
-   Internal navigation history
-   Embedded browser interface
-   Controlled browsing environment

------------------------------------------------------------------------

# Architecture

PhantomLink acts as an intermediate proxy between the user and external
websites.

    User Browser
          │
          ▼
    PhantomLink (Flask)
          │
          ▼
    External Website

All requests are proxied and optionally logged for analysis.

------------------------------------------------------------------------

# Internal Navigation Flow

    User
     │
     ▼
    Browser Interface
     │
     ▼
    URL Input
     │
     ▼
    /proxy/?url=https://example.com
     │
     ▼
    Flask Backend
     │
     ▼
    requests.get()
     │
     ▼
    HTML Processing (BeautifulSoup)
     │
     ▼
    Resource rewriting
     │
     ▼
    Rendered inside iframe

------------------------------------------------------------------------

# Technologies

-   Python
-   Flask
-   Requests
-   BeautifulSoup
-   lxml
-   HTML
-   CSS
-   JavaScript

------------------------------------------------------------------------

# Installation

Clone the repository:

    git clone https://github.com/YOUR_USERNAME/phantomlink.git
    cd phantomlink

Create a virtual environment:

Linux / macOS

    python3 -m venv venv
    source venv/bin/activate

Windows

    python -m venv venv
    venv\Scripts\activate

Install dependencies:

    pip install -r requirements.txt

Example `requirements.txt`:

    Flask
    requests
    beautifulsoup4
    lxml

Run the application:

    python main.py

The server will start on:

    http://127.0.0.1:5000

------------------------------------------------------------------------

# Usage

Open your browser and access:

    http://localhost:5000

Enter a target URL in the navigation bar:

    https://example.com

The request will be processed through the internal proxy:

    /proxy/?url=https://example.com

The page will be retrieved by the backend and rendered inside the
embedded browser iframe.

------------------------------------------------------------------------

# Proxy Mechanism

The proxy endpoint performs the following operations:

1.  Receives the requested URL
2.  Sends an HTTP request using the `requests` library
3.  Retrieves the remote HTML
4.  Parses it with `BeautifulSoup`
5.  Rewrites resource URLs (images, scripts, CSS)
6.  Returns the modified HTML to the browser

This allows bypassing some restrictions such as:

-   `X-Frame-Options`
-   `frame-ancestors`
-   embedding restrictions

Note that some websites may still block proxy access.

------------------------------------------------------------------------

# Network Diagnostics

PhantomLink includes basic network diagnostics for inspected URLs.

Features include:

-   Domain resolution
-   IP address identification
-   Latency measurement
-   Connectivity testing

Example diagnostic flow:

    URL
     │
     ▼
    DNS resolution
     │
     ▼
    IP detection
     │
     ▼
    Latency measurement

------------------------------------------------------------------------

# Logging

The platform can log browsing activity for analysis purposes.

Possible logged data:

-   requested URLs
-   timestamps
-   response codes
-   connection errors
-   network diagnostics

Logs can be used for:

-   traffic inspection
-   debugging
-   research
-   controlled environment monitoring

------------------------------------------------------------------------

# Connectivity Testing

To verify if the hosting environment can reach a specific website you
can run:

    curl -I https://example.com

or

    wget --spider https://example.com

Python test example:

    import requests

    try:
        r = requests.get("https://example.com", timeout=10)
        print("Status:", r.status_code)
    except Exception as e:
        print("Connection error:", e)

------------------------------------------------------------------------

# Known Limitations

Some websites may not load correctly due to:

-   strict CSP policies
-   proxy blocking
-   hosting provider network restrictions
-   WebSocket usage
-   complex JavaScript frameworks

Additionally some hosting providers may force outbound traffic through
internal proxies.

------------------------------------------------------------------------

# Deployment

PhantomLink can run on multiple environments:

-   local development machine
-   VPS servers
-   container environments
-   cloud platforms
-   Replit

For production environments it is recommended to use a WSGI server.

Example using **Waitress**:

    pip install waitress

Run:

    waitress-serve --port=8000 main:app

------------------------------------------------------------------------

# Project Structure

    phantomlink/
    │
    ├── main.py
    ├── proxy.py
    ├── requirements.txt
    │
    ├── templates/
    │   └── index.html
    │
    ├── static/
    │   ├── css
    │   ├── js
    │   └── images
    │
    └── README.md

------------------------------------------------------------------------

# Roadmap

Future improvements may include:

-   advanced traffic inspection
-   response header analysis
-   technology fingerprinting
-   request replay
-   security analysis modules
-   proxy performance optimization

------------------------------------------------------------------------

# Disclaimer

This project is intended for:

-   educational purposes
-   security research
-   controlled environments
-   testing and experimentation

Do not use this tool to violate the policies or security of third-party
systems.

------------------------------------------------------------------------

# License

MIT License
