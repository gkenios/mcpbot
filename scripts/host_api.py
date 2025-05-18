if __name__ == "__main__":
    import uvicorn
    from mcpbot.shared.config import PORT

    uvicorn.run("mcpbot.main:app", port=int(PORT))
