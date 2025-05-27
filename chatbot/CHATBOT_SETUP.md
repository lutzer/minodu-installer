# Chatbot Setup

* install raspberry pi os

  ```
  sudo apt update
  sudo apt upgrade
  ```

* Install olama `curl -fsSL https://ollama.com/install.sh | sh`

## Install Gemma2 Model

* install with `ollama run gemma2:2b` and test if it works
* install llama with `ollama run llama3.2:1b` for a much faster model

### TODO

* try out 
  * Llama 3.2 3B: Often faster inference than Gemma2:2b despite being larger
  * Qwen2.5 1.5B: Excellent context handling, very efficient


## Setup Chatbot Python Script

* go into *chatbot* folder and run `python -m venv .venv`
* then `source .venv/bin/activate`to activate it
* `pip install -r requirements.txt`  to install dependencies