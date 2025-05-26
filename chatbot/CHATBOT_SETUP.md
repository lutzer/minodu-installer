# Chatbot Setup

* install raspberry pi os

  ```
  sudo apt update
  sudo apt upgrade
  ```

* Install olama `curl -fsSL https://ollama.com/install.sh | sh`

## Install Gemma2 Model

* install with `ollama run gemma2:2b` and test if it works



## Setup Chatbot Python Script

* go into *chatbot* folder and run `python -m venv .venv`
* then `source .venv/bin/activate`to activate it
* `pip install -r requirements.txt`  to install dependencies