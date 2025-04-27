# MCPBot
---

**Documentation**: <a href="https://gkenios.github.io/mcpbot" target="_blank">https://gkenios.github.io/mcpbot</a>

---

An implementation of an MCP client and server, using FastAPI.

## To Do
- [ ] Add metadata to the streaming answer.
- [ ] Develop a client-side GUI for the MCP client with ReactJS.

## Local
To run locally
- Run `uv sync --group local`
- In the .env file, set the secrets defined in the `mcpbot/config-local.py` file
- If you have access download the whole `.chromadb` folder [this link](https://drive.google.com/drive/folders/1DaUQ6ZmFzjPIj9kMZTJSJT_7zPtpJ1-y?usp=drive_link) and place it in the root directory of the project. <br>
  Otherwise, create your own vector database using the `scripts/create_document.py` script. <br>
